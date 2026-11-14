"""LangGraph orchestration adapted from the official Code Assistant pattern.

See SOURCES-AND-CHANGES.md and upstream-reference/ for source, commit and MIT license.
Unlike the upstream notebook, generated code is never executed with exec().
"""
import copy
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from governance import qa, redact_code, scan
from llm import ModelError
from pipeline import call, event, get_code


# 1. KHAI BÁO CẤU TRÚC TRẠNG THÁI (STATE) CỦA ĐỒ THỊ LANGGRAPH
class RunState(TypedDict):
    """
    RunState: Định nghĩa dữ liệu di chuyển xuyên suốt giữa các Node trong đồ thị.
    - session: Chứa dữ liệu nghiệp vụ của phiên (yêu cầu người dùng, code, kết quả QA, v.v.),
               được đồng bộ và lưu trữ lâu dài vào SQLite (.state/sessions.sqlite3).
    - confirmed: Cờ đánh dấu người dùng đã xác nhận chấp nhận mã nguồn hay chưa.
    - route: Tên Node tiếp theo mà Coordinator (Hub) quyết định điều phối đến.
    - visited: Danh sách ghi lại thứ tự các Node mà luồng đã ghé qua.
    """
    session: dict
    confirmed: bool
    route: str
    visited: list[str]


# 2. XÂY DỰNG ĐỒ THỊ ĐIỀU PHỐI (BUILD GRAPH)
def build_graph(model):
    """
    Xây dựng đồ thị LangGraph (Hub-and-Spoke Architecture).
    Mỗi lần người dùng bấm 'Chạy yêu cầu', đồ thị được kích hoạt (invoke)
    để đi qua đúng MỘT bước nghiệp vụ qua Hub (Coordinator) rồi dừng lại,
    chờ người dùng xem kết quả hoặc xác nhận tiếp tục.
    """

    # Wrapper bọc hàm node để tự động ghi nhận lịch sử các node đã ghé thăm (visited)
    def node(name, function):
        def execute(run):
            updates = function(run)
            return {**updates, "visited": run["visited"] + [name]}
        return execute

    # NODE 1: COORDINATOR (HUB TRUNG TÂM)
    # Nhiệm vụ: Đọc trạng thái hiện tại (phase) và quyết định Spoke tiếp theo.
    def coordinator(run):
        s = run["session"]
        if s.get("kind") != "hub":
            raise ValueError("Bản demo này chỉ hỗ trợ Hub-and-Spoke.")
        if s["status"] in ("accepted", "exhausted"):
            raise ValueError("Phiên đã dừng. Tạo phiên mới để đổi yêu cầu.")

        # Bảng ánh xạ: Giai đoạn hiện tại -> Spoke tiếp theo cần gọi
        # ready: Sẵn sàng -> giao cho Planner lên kế hoạch
        # planned: Đã lập kế hoạch -> giao cho Developer sinh code
        # coded: Đã có code -> giao cho QA kiểm thử
        # review: Đã qua kiểm tra an toàn -> chờ người dùng Accept
        routes = {"ready": "planner", "planned": "developer", "coded": "qa", "review": "accept"}

        if s["phase"] == "blocked":
            # Nếu code bị chặn do lỗi QA hoặc vi phạm Governance:
            # - Quá 3 lần sửa mà vẫn lỗi -> Dừng hẳn (stop)
            # - Dưới 3 lần -> Chuyển sang spoke 'repair' để sửa lại code
            target = "stop" if s["repairs"] >= 3 else "repair"
        else:
            target = routes.get(s["phase"])

        if target is None:
            raise ValueError("Trạng thái Hub không hợp lệ.")
        if target == "accept" and not run["confirmed"]:
            raise ValueError("Cần xác nhận xem xét trước khi chấp nhận mã.")

        return {"route": target}

    # NODE 2: PLANNER SPOKE (LẬP KẾ HOẠCH)
    # Nhiệm vụ: Gọi Gemini để phân tích yêu cầu thành User Story và tiêu chí nghiệm thu.
    def planner(run):
        s = run["session"]
        data = call(s, model, "planner", {"request": s["description"]})
        story = data.get("story")
        if not isinstance(story, dict) or not isinstance(story.get("title"), str) or not isinstance(story.get("acceptance"), list):
            raise ModelError("Planner cần trả title và acceptance trong story.")
        s.update(story=story, phase="planned", status="running")
        event(s, "Planner → Coordinator", "Đã tạo story và tiêu chí chấp nhận bằng Gemini.")
        return {"session": s}

    # NODE 3: DEVELOPER SPOKE (LẬP TRÌNH VIÊN)
    # Nhiệm vụ: Viết code Python đáp ứng story của Planner (hoặc nhận code có sẵn).
    def developer(run):
        s = run["session"]
        if s["initial_code"].strip():
            # Nếu người dùng đã tự dán code vào từ giao diện
            s["code"] = s["initial_code"]
            event(s, "Người dùng → Coordinator", "Tiếp nhận mã có sẵn; bước này không gọi LLM để tạo mã.")
        else:
            # Gọi LLM (Gemini) sinh code theo story đã lập
            s["code"] = get_code(call(s, model, "developer", {"request": s["description"], "story": s["story"]}))
            event(s, "Developer → Coordinator", "Gemini đã tạo bản mã r1.")
        s.update(revision=1, phase="coded")
        return {"session": s}

    # NODE 4: QA SPOKE (KIỂM THỬ CHẤT LƯỢNG)
    # Nhiệm vụ: Kiểm thử cú pháp và chức năng thông qua thông dịch AST bị cô lập.
    def qa_node(run):
        s = run["session"]
        s["qa"] = qa(s["code"])
        event(s, "QA → Coordinator", "PASS" if s["qa"]["pass"] else "FAIL: chức năng chưa đạt hoặc vượt phạm vi kiểm thử.")
        return {"session": s}

    # NODE 5: GOVERNANCE SPOKE (QUẢN TRỊ AN TOÀN & BẢO MẬT)
    # Nhiệm vụ: Quét AST phát hiện lộ mật khẩu, hardcoded API key, hoặc hàm nguy hiểm (eval, exec).
    def governance(run):
        s = run["session"]
        s["governance"] = scan(s["code"])
        event(s, "Governance → Coordinator", "PASS: đạt quy tắc AST hiện tại." if s["governance"]["pass"] else "FAIL: mã vi phạm quy tắc AST.")
        return {"session": s}

    # CONDITIONAL EDGE: CỔNG ĐÁNH GIÁ (SECURITY & QUALITY GATE ROUTER)
    # Đưa ra quyết định cứng bằng code Python; LLM không có quyền tự tuyên bố PASS.
    def gate_route(run):
        s = run["session"]
        # Phải đồng thời vượt qua cả bài test QA lẫn quy tắc bảo mật Governance
        return "gate_pass" if s["qa"]["pass"] and s["governance"]["pass"] else "gate_fail"

    # Xử lý kết quả cổng kiểm soát (gate_pass hoặc gate_fail)
    def gate_result(run, passed):
        s = run["session"]
        cases = s["qa"].get("cases", [])
        # Lưu vào lịch sử kiểm thử để theo dõi qua các lần sửa (revisions)
        s.setdefault("check_history", []).append({
            "revision": s["revision"],
            "passed": passed,
            "qa_passed": s["qa"]["pass"],
            "qa_pass_count": sum(case["pass"] for case in cases),
            "qa_total": len(cases),
            "governance_passed": s["governance"]["pass"],
            "findings": [{"line": item["line"], "rule": item["rule"]}
                         for item in s["governance"].get("findings", [])],
        })
        # Nếu đạt: chuyển trạng thái sang 'review' để người dùng duyệt.
        # Nếu không đạt: chuyển sang 'blocked' để kích hoạt sửa lỗi.
        s["phase"] = s["status"] = "review" if passed else "blocked"
        return {"session": s}

    # NODE 6: REPAIR SPOKE (TỰ ĐỘNG SỬA MÃ NGUỒN)
    # Nhiệm vụ: Đọc lỗi từ QA và Governance, che thông tin nhạy cảm và yêu cầu LLM sửa lại.
    def repair(run):
        s = run["session"]
        feedback = {"qa": s["qa"], "governance": s["governance"]}
        s["code"] = get_code(call(s, model, "developer", {
            "request": s["description"], "story": s["story"],
            "code_to_repair": redact_code(s["code"]), "trusted_feedback": feedback,
        }))
        # Tăng số lần sửa, xóa kết quả kiểm tra cũ để chuẩn bị kiểm tra lại
        s.update(repairs=s["repairs"] + 1, revision=s["revision"] + 1,
                 qa=None, governance=None, phase="coded", status="running")
        event(s, "Developer → Coordinator", f'Gemini đã sửa mã r{s["revision"]}; phải kiểm tra lại.')
        return {"session": s}

    # NODE 7: ACCEPT (CHẤP NHẬN KẾT QUẢ)
    # Người dùng nhấn xác nhận nghiệm thu sản phẩm.
    def accept(run):
        s = run["session"]
        if not ((s.get("qa") or {}).get("pass") and (s.get("governance") or {}).get("pass")):
            raise ValueError("Chưa có đủ hai kết quả kiểm tra đạt.")
        s["phase"] = s["status"] = "accepted"
        event(s, "Người dùng → Coordinator", "Chấp nhận kết quả đã qua kiểm tra. Không merge hay triển khai tự động.")
        return {"session": s}

    # NODE 8: STOP (DỪNG LUỒNG KHI QUÁ GIỚI HẠN SỬA)
    def stop(run):
        s = run["session"]
        s["status"] = "exhausted"
        event(s, "Coordinator", "Dừng sau 3 lần sửa; mã chưa được chấp nhận.")
        return {"session": s}

    # NODE 9: FINISH (ĐIỂM KẾT THÚC VÒNG CHẠY)
    def finish(run):
        s = run["session"]
        s["last_error"] = None
        s["version"] += 1
        s["engine"] = "LangGraph"
        s.setdefault("graph_steps", []).append({"version": s["version"], "nodes": run["visited"] + ["finish"]})
        return {"session": s}

    # 3. KẾT NỐI CÁC ĐỈNH VÀ CẠNH VÀO ĐỒ THỊ LANGGRAPH (STATEGRAPH)
    graph = StateGraph(RunState)

    # Đăng ký danh sách các Node
    operations = {"coordinator": coordinator, "planner": planner, "developer": developer,
                  "qa": qa_node, "governance": governance, "repair": repair, "accept": accept,
                  "stop": stop, "gate_pass": lambda r: gate_result(r, True),
                  "gate_fail": lambda r: gate_result(r, False), "finish": finish}
    for name, operation in operations.items():
        graph.add_node(name, node(name, operation))

    # Cạnh bắt đầu: START -> Hub (coordinator)
    graph.add_edge(START, "coordinator")

    # Cạnh điều kiện: Hub phân luồng rẽ nhánh sang Spoke tương ứng
    graph.add_conditional_edges("coordinator", lambda r: r["route"],
                                {name: name for name in ("planner", "developer", "qa", "repair", "accept", "stop")})

    # Sau QA luôn chuyển sang Governance để kiểm tra bảo mật
    graph.add_edge("qa", "governance")

    # Từ Governance rẽ nhánh: gate_pass hoặc gate_fail
    graph.add_conditional_edges("governance", gate_route, {"gate_pass": "gate_pass", "gate_fail": "gate_fail"})

    # Mọi Spoke sau khi hoàn tất lượt của mình đều trỏ về 'finish' để ghi nhận dữ liệu
    for name in ("planner", "developer", "repair", "accept", "stop", "gate_pass", "gate_fail"):
        graph.add_edge(name, "finish")

    # Điểm kết thúc của một lượt chạy (invoke)
    graph.add_edge("finish", END)

    # Biên dịch đồ thị LangGraph
    return graph.compile()


# 4. HÀM THỰC THI CHÍNH TỪ SERVER (APP.PY GỌI VÀO ĐÂY)
def run_step(state, model, confirmed=False):
    """
    Thực hiện 1 bước chuyển trạng thái (state transition).
    Dùng deepcopy để bảo đảm tính toàn vẹn: nếu LLM lỗi mạng/timeout thì không làm hỏng state cũ.
    """
    run = {"session": copy.deepcopy(state), "confirmed": confirmed, "route": "", "visited": []}
    return build_graph(model).invoke(run)["session"]

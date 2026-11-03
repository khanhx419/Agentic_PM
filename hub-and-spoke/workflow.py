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


class RunState(TypedDict):
    # session được lưu SQLite; model/key không đưa vào trạng thái graph.
    session: dict
    confirmed: bool
    route: str
    visited: list[str]


def build_graph(model):
    """Mỗi invoke chạy một bước nghiệp vụ, qua Hub; không tự gọi hết các agent."""
    def node(name, function):
        def execute(run):
            updates = function(run)
            return {**updates, "visited": run["visited"] + [name]}
        return execute

    def coordinator(run):
        s = run["session"]
        if s.get("kind") != "hub":
            raise ValueError("Bản demo này chỉ hỗ trợ Hub-and-Spoke.")
        if s["status"] in ("accepted", "exhausted"):
            raise ValueError("Phiên đã dừng. Tạo phiên mới để đổi yêu cầu.")
        routes = {"ready": "planner", "planned": "developer", "coded": "qa", "review": "accept"}
        if s["phase"] == "blocked":
            target = "stop" if s["repairs"] >= 3 else "repair"
        else:
            target = routes.get(s["phase"])
        if target is None:
            raise ValueError("Trạng thái Hub không hợp lệ.")
        if target == "accept" and not run["confirmed"]:
            raise ValueError("Cần xác nhận xem xét trước khi chấp nhận mã.")
        return {"route": target}

    def planner(run):
        s = run["session"]
        data = call(s, model, "planner", {"request": s["description"]})
        story = data.get("story")
        if not isinstance(story, dict) or not isinstance(story.get("title"), str) or not isinstance(story.get("acceptance"), list):
            raise ModelError("Planner cần trả title và acceptance trong story.")
        s.update(story=story, phase="planned", status="running")
        event(s, "Planner → Coordinator", "Đã tạo story và tiêu chí chấp nhận bằng Gemini.")
        return {"session": s}

    def developer(run):
        s = run["session"]
        if s["initial_code"].strip():
            s["code"] = s["initial_code"]
            event(s, "Người dùng → Coordinator", "Tiếp nhận mã có sẵn; bước này không gọi LLM để tạo mã.")
        else:
            s["code"] = get_code(call(s, model, "developer", {"request": s["description"], "story": s["story"]}))
            event(s, "Developer → Coordinator", "Gemini đã tạo bản mã r1.")
        s.update(revision=1, phase="coded")
        return {"session": s}

    def qa_node(run):
        s = run["session"]
        s["qa"] = qa(s["code"])
        event(s, "QA → Coordinator", "PASS" if s["qa"]["pass"] else "FAIL: chức năng chưa đạt hoặc vượt phạm vi kiểm thử.")
        return {"session": s}

    def governance(run):
        s = run["session"]
        s["governance"] = scan(s["code"])
        event(s, "Governance → Coordinator", "PASS: đạt quy tắc AST hiện tại." if s["governance"]["pass"] else "FAIL: mã vi phạm quy tắc AST.")
        return {"session": s}

    def gate_route(run):
        # Quyết định cứng bằng Python; Gemini không được tự tuyên bố PASS.
        s = run["session"]
        return "gate_pass" if s["qa"]["pass"] and s["governance"]["pass"] else "gate_fail"

    def gate_result(run, passed):
        s = run["session"]
        s["phase"] = s["status"] = "review" if passed else "blocked"
        return {"session": s}

    def repair(run):
        s = run["session"]
        feedback = {"qa": s["qa"], "governance": s["governance"]}
        s["code"] = get_code(call(s, model, "developer", {
            "request": s["description"], "story": s["story"],
            "code_to_repair": redact_code(s["code"]), "trusted_feedback": feedback,
        }))
        s.update(repairs=s["repairs"] + 1, revision=s["revision"] + 1,
                 qa=None, governance=None, phase="coded", status="running")
        event(s, "Developer → Coordinator", f'Gemini đã sửa mã r{s["revision"]}; phải kiểm tra lại.')
        return {"session": s}

    def accept(run):
        s = run["session"]
        if not ((s.get("qa") or {}).get("pass") and (s.get("governance") or {}).get("pass")):
            raise ValueError("Chưa có đủ hai kết quả kiểm tra đạt.")
        s["phase"] = s["status"] = "accepted"
        event(s, "Người dùng → Coordinator", "Chấp nhận kết quả đã qua kiểm tra. Không merge hay triển khai tự động.")
        return {"session": s}

    def stop(run):
        s = run["session"]
        s["status"] = "exhausted"
        event(s, "Coordinator", "Dừng sau 3 lần sửa; mã chưa được chấp nhận.")
        return {"session": s}

    def finish(run):
        s = run["session"]
        s["last_error"] = None
        s["version"] += 1
        s["engine"] = "LangGraph"
        s.setdefault("graph_steps", []).append({"version": s["version"], "nodes": run["visited"] + ["finish"]})
        return {"session": s}

    # Kế thừa mẫu StateGraph / conditional edges / compile từ Code Assistant.
    graph = StateGraph(RunState)
    operations = {"coordinator": coordinator, "planner": planner, "developer": developer,
                  "qa": qa_node, "governance": governance, "repair": repair, "accept": accept,
                  "stop": stop, "gate_pass": lambda r: gate_result(r, True),
                  "gate_fail": lambda r: gate_result(r, False), "finish": finish}
    for name, operation in operations.items():
        graph.add_node(name, node(name, operation))
    graph.add_edge(START, "coordinator")
    graph.add_conditional_edges("coordinator", lambda r: r["route"],
                                {name: name for name in ("planner", "developer", "qa", "repair", "accept", "stop")})
    graph.add_edge("qa", "governance")
    graph.add_conditional_edges("governance", gate_route, {"gate_pass": "gate_pass", "gate_fail": "gate_fail"})
    for name in ("planner", "developer", "repair", "accept", "stop", "gate_pass", "gate_fail"):
        graph.add_edge(name, "finish")
    graph.add_edge("finish", END)
    return graph.compile()


def run_step(state, model, confirmed=False):
    # Chỉ commit trạng thái khi graph hoàn tất; lỗi API không làm bẩn bản đầu vào.
    run = {"session": copy.deepcopy(state), "confirmed": confirmed, "route": "", "visited": []}
    return build_graph(model).invoke(run)["session"]

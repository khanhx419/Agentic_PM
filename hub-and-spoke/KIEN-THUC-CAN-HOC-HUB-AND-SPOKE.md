# Kiến thức cần học — Hub-and-Spoke trên LangGraph

File này dành riêng để học. Kịch bản thao tác ở `HUONG-DAN-HOC-VA-THUYET-TRINH.md`, nguồn và đối chiếu mã ở `SOURCES-AND-CHANGES.md`.

## 1. Học trước: giải thích được luồng

Yêu cầu → Planner → Developer → QA + Governance → sửa nếu không đạt → kiểm tra lại → người dùng chấp nhận.

| Thành phần | Việc thực tế | Công nghệ |
|---|---|---|
| Hub/Coordinator | Chọn bước dựa vào trạng thái và chính sách | Python node trong LangGraph |
| Planner | Tạo một story và tiêu chí chấp nhận | Gemini API |
| Developer | Sinh hoặc sửa mã theo phản hồi | Gemini API |
| QA | Kiểm tra hành vi qua 14 ca thử email | Python, không gọi LLM |
| Governance | Phân tích mã và áp quy tắc | Python AST, không gọi LLM |
| Người dùng | Xem xét và chấp nhận | Giao diện/API |

Agent là một vai trò có chỉ dẫn và đầu vào riêng, không nhất thiết là một model khác. Planner và Developer dùng cùng Gemini với prompt khác nhau. US là User Story: một yêu cầu nhỏ có thể kiểm tra được.

## 2. LangGraph là gì? Mình dùng vào đâu?

LangGraph là framework tổ chức quy trình bằng graph:

- **State:** dữ liệu dùng chung, như story, code, kết quả kiểm tra và số lần sửa.
- **Node:** hàm làm một việc; có thể gọi LLM hoặc chỉ chạy Python.
- **Edge:** xác định node tiếp theo.
- **Conditional edge:** rẽ nhánh theo kết quả/quy tắc.
- **compile:** dựng graph có thể chạy.
- **invoke:** thực thi graph với dữ liệu đầu vào.

Đọc `workflow.py`: `RunState`, `build_graph`, các node rồi nhóm `add_node/add_edge/add_conditional_edges` ở cuối. Đừng chỉ nói “dùng LangGraph” mà không chỉ được các dòng này.

Hub là điều phối có quy tắc, **không phải LLM supervisor tự lựa chọn mọi hành động**. Nhờ đó model không được bỏ qua kiểm tra. Không dùng ADK, CrewAI, native function calling hay gói langgraph-supervisor.

Một lần invoke chạy một bước nghiệp vụ rồi kết thúc: Hub → Planner → finish, hoặc Hub → QA → Governance → nhánh kết quả → finish. Sau mỗi lần bấm, SQLite lưu phiên; lần bấm tiếp lấy phiên đó chạy graph tiếp. Vòng sửa diễn ra qua các lần invoke, chưa dùng LangGraph checkpointer/interrupt.

## 3. Máy trạng thái cần nhớ

| Trạng thái hiện tại | Hub chuyển tới | Kết quả |
|---|---|---|
| ready | planner | planned |
| planned | developer hoặc nhận mã đã nhập | coded |
| coded | qa → governance → gate_route | review hoặc blocked |
| blocked, còn lượt sửa | repair | coded, xóa kết quả kiểm tra cũ |
| blocked, đã sửa 3 lần | stop | exhausted |
| review, có xác nhận và hai cổng đạt | accept | accepted |

Model nói “đã sửa xong” không làm mã đạt. `repair` trả về `coded`, không nhảy thẳng `accepted`. Nếu API lỗi, bản trạng thái đầu vào không bị đổi thành thành công.

## 4. QA và Governance: phần quan trọng nhất

QA hỏi “hàm có xử lý đúng ca thử không?”. Governance hỏi “mã có vi phạm quy tắc không?”.

Ví dụ mã kiểm tra email đúng nhưng có `SECRET_KEY = "DEMO_ONLY_NOT_REAL"`: QA có thể đạt, Governance chặn. Ngược lại, mã không chứa secret nhưng chấp nhận `abc` là email thì QA trượt.

Trong `gate_route`, chỉ khi `qa.pass AND governance.pass` mới sang review. Đây là điều kiện Python cứng, không nhờ model phán.

AST là cây cú pháp trừu tượng: biểu diễn phép gán, tên biến, literal, lời gọi hàm... `ast.parse` đọc mã thành cây; `ast.walk` duyệt cây.

Các nút cần biết: `ast.Assign` (gán), `ast.Name` (tên), `ast.Constant` (giá trị cố định), `ast.Call` (gọi hàm). Quy tắc tìm tên biến nhạy cảm gán chuỗi, một số dạng ghép/alias, secret mặc định trong getenv, lệnh nguy hiểm và cấu trúc ngoài phạm vi.

Đọc `governance.py`: `literal` → `scan` → `redact_code` → `qa`. Đọc `qa_worker.py`: `Interpreter` và bộ ca thử trong `run`. Worker không dùng exec/eval chạy mã sinh; đây là thông dịch tập con AST, không phải Docker sandbox.

Không phát hiện được mọi secret/lỗ hổng. PASS chỉ có nghĩa đạt quy tắc và ca thử hiện tại. Trước khi gửi mã sửa, `redact_code` che giá trị secret phát hiện được; không có bảo đảm che được mọi thông tin bí mật trong dữ liệu tùy ý.

## 5. Nguồn kế thừa và phần mình làm

Nguồn kiến trúc là tài liệu Hub-and-Spoke. Nguồn workflow là Code Assistant chính thức của LangGraph. Bản gốc có generate, code_check, conditional routing và vòng phản hồi lỗi.

Bản demo viết lại các node theo bài toán nhỏ, dùng LangGraph thật và bổ sung Planner, hai cổng độc lập, AST, xác nhận và giao diện. Không thực thi notebook gốc vì nó dùng exec; notebook chỉ được giữ để đối chiếu và kèm giấy phép MIT.

Cần mở được `SOURCES-AND-CHANGES.md` và `upstream-reference/manifest.json` khi thầy hỏi nguồn. Không nói đây là code tác giả luận văn hoặc đã tái lập toàn bộ nghiên cứu.

## 6. API, key và chạy local

Gemini chạy trên dịch vụ bên ngoài. LangGraph, AST, QA, web và SQLite chạy trên máy. Thư viện không tự biến model thành local.

`pipeline.PROMPTS` định nghĩa vai trò. `pipeline.call` gọi `Gemini.call` trong `llm.py`. JSON đúng cú pháp chưa bảo đảm nội dung đúng, vì vậy vẫn có validator.

`config.py` đọc key từ `.env`/biến môi trường. Key không được đưa vào graph state hoặc frontend. Không chiếu `.env`, không commit key. Miễn phí/quota phụ thuộc tài khoản, không cam kết vô hạn.

## 7. Bản đồ đọc code trong một buổi

1. `pipeline.py`: PROMPTS, initial, call, advance — hiểu dữ liệu và cách gọi vai trò.
2. `workflow.py`: coordinator và graph edges — hiểu ai quyết định bước tiếp.
3. `workflow.py`: qa_node, governance, gate_route, repair, accept — hiểu chặn và sửa.
4. `governance.py`: scan, redact_code; `qa_worker.py`: Interpreter — hiểu cổng kiểm tra.
5. `llm.py` — hiểu API và lỗi.
6. `app.py`, `store.py`, `web/app.js` — hiểu nút bấm, HTTP và lưu phiên.

Python cần nắm: hàm, dict/list, if/elif, exception, import và JSON. TypedDict mô tả dạng state; không tự thay thế kiểm tra dữ liệu lúc chạy. Chưa cần học sâu CSS/SQLite để trình diễn cơ chế.

## 8. Bài tập để biết mình đã hiểu

- Tự vẽ luồng và đánh dấu bước gọi API.
- Chỉ conditional edge quyết định PASS/FAIL trong graph.
- Giải thích vì sao sửa mã phải xóa kết quả kiểm tra cũ.
- Thử secret giả ở công cụ AST/QA trực tiếp, đọc dòng vi phạm.
- Tải JSON phiên, tìm `engine` và từng danh sách `graph_steps.nodes`.
- Xuất `WORKFLOW.mmd` bằng `export_graph.py`; giải thích graph đó được dựng từ code thực.
- Tự phân biệt “nguồn kiến trúc”, “nguồn framework/mẫu workflow”, “code bổ sung”.

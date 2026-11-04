# Hướng dẫn chạy và trình bày demo Hub-and-Spoke với thầy

## 1. Mục tiêu lần gặp này

Thầy đã nghe Hub-and-Spoke và yêu cầu làm thử demo. Trình bày một cơ chế chạy được: Hub điều phối các vai trò; mã vi phạm bị chặn; Developer nhận lỗi để sửa; bản sửa phải kiểm tra lại. Không cần mở rộng sang đề tài khác.

## 2. Chuẩn bị trước buổi demo

1. Mở thư mục `Agentic_PM/hub-and-spoke` trong repo. Trên máy hiện tại là `Bo-thuyet-trinh/02-Agentic-PM/hub-and-spoke`.
2. Chạy `cai-dat.cmd` để cài LangGraph vào `.venv`. Chỉ cần làm lần đầu hoặc khi thay dependency.
3. Chạy `cau-hinh-api.cmd`, nhập key trên máy. Không chiếu nội dung `.env`.
4. Chạy `start.cmd`, giữ cửa sổ server, mở http://127.0.0.1:8767/hub.
5. Mở sẵn `workflow.py`, `SOURCES-AND-CHANGES.md` và `KIEN-THUC-CAN-HOC-HUB-AND-SPOKE.md`.
6. Nếu cần sơ đồ graph: `.venv\Scripts\python.exe export_graph.py`. Mở `WORKFLOW.mmd` bằng công cụ có hỗ trợ Mermaid, hoặc xem phần graph trong GitHub. Không cần chạy notebook gốc.

Nếu port 8767 đang dùng, đóng đúng cửa sổ server cũ của mình hoặc dùng `.venv\Scripts\python.exe app.py --port 8768` rồi mở đúng port. Không tắt tiến trình không biết là gì.

## 2.1. Hệ thống bên trong gồm gì? Phần lõi có phải Python không?

**Có. Backend và phần điều phối, gọi API, kiểm tra, lưu dữ liệu đều viết bằng Python.** Giao diện là HTML/CSS/JavaScript. LangGraph là thư viện Python chạy trên máy; model Gemini chạy ở dịch vụ Google, được Python gọi qua API, không chạy local trong demo này.

### Những file Python chính

| File | Trách nhiệm | Khi giải thích với thầy |
|---|---|---|
| `app.py` | Chạy HTTP server local, nhận yêu cầu, quản lý truy cập phiên và trả JSON | “Đây là cửa vào backend, không phải nơi model tự quyết toàn bộ quy trình.” |
| `workflow.py` | Dựng và thực thi LangGraph: Hub, Planner, Developer, QA, Governance, nhánh sửa/chấp nhận/dừng | “Đây là lõi điều phối. Hub chọn bước theo trạng thái và chính sách.” |
| `pipeline.py` | Prompt vai trò, khởi tạo trạng thái, gọi model và đọc mã trả về; giữ hàm advance tương thích | “Đây là dữ liệu/chỉ dẫn cho vai trò. Phần điều phối thực đã chuyển sang workflow.py.” |
| `llm.py` | Gọi Gemini REST, đọc JSON, thống kê token/thời gian, xử lý lỗi mạng/quota | “Planner và Developer dùng API thật qua file này.” |
| `governance.py` | Quét AST, phát hiện vi phạm, che secret phát hiện được, gọi QA worker | “Quy tắc kiểm soát mã được viết bằng Python, không nhờ Gemini tự phán PASS.” |
| `qa_worker.py` | Thông dịch tập con AST và chạy 14 ca thử email trong worker riêng | “Đây là phần kiểm tra hành vi; không dùng exec để chạy Python tùy ý.” |
| `store.py` | Lưu phiên vào SQLite, quản lý token, thời hạn và khóa phiên | “Tải lại trang cùng tab có thể tiếp tục phiên đã lưu.” |
| `config.py` | Đọc model/key/cấu hình và cung cấp thông tin công khai không chứa key | “Key ở backend, không nằm trong JavaScript hoặc graph state.” |
| `setup_api.py` | Nhập key trên máy và ghi cấu hình cục bộ | “Chỉ chạy khi cấu hình, không phải agent xử lý nghiệp vụ.” |

### Các file và thư mục hỗ trợ

- `web/hub.html`: cấu trúc trang; `web/style.css`: trình bày; `web/app.js`: nhận thao tác, gọi backend và hiển thị kết quả. Giao diện không tự tính PASS/FAIL.
- `cai-dat.cmd`: tạo môi trường và cài dependency; `cau-hinh-api.cmd`: mở cấu hình key; `start.cmd`: khởi động Python server.
- `requirements.txt`, `requirements-lock.txt`: phiên bản thư viện; `.venv/`: môi trường Python local.
- `.env`: cấu hình bí mật local; `.state/sessions.sqlite3`: dữ liệu phiên. Hai phần này không đưa lên GitHub.
- `export_graph.py`, `WORKFLOW.mmd`: xuất/xem cấu trúc graph thực, không gọi model.
- `verify_live.py`: chủ động kiểm tra Gemini thật khi có cờ `--live`; không chạy ngầm khi mở giao diện.
- `tests/`: kiểm thử có model thay thế được gắn nhãn; `verification/`: báo cáo và ảnh kiểm tra; `upstream-reference/`: nguồn notebook và license để đối chiếu.

### Đường đi của một thao tác

1. Người dùng bấm nút trên trang → `web/app.js` gửi HTTP.
2. `app.py` kiểm tra token và version, lấy trạng thái phiên từ `store.py`.
3. `workflow.run_step` chạy LangGraph. Node Coordinator chọn bước theo trạng thái.
4. Nếu là Planner/Developer: gọi hàm trong `pipeline.py` → `llm.py` → Gemini → nhận JSON. Nếu là kiểm tra: chạy `qa_worker.py` và quy tắc trong `governance.py`.
5. Graph quyết định trạng thái tiếp theo; `app.py` lưu kết quả bằng `store.py` và trả JSON.
6. `web/app.js` hiển thị mã, kết quả kiểm tra và nút cho bước tiếp theo.

**Luồng nghiệp vụ:** yêu cầu → Planner → Developer → QA và Governance → không đạt thì sửa rồi kiểm tra lại → đạt thì chờ người dùng chấp nhận. Mỗi lần bấm chạy một bước nghiệp vụ; LangGraph không tự gọi hết mọi agent trong một lần bấm.

**Cần học kỹ nhất:** `workflow.py`, `pipeline.py`, `governance.py`, `qa_worker.py`, `llm.py`. Sau đó đọc `app.py` và `store.py` để hiểu cách hệ thống nối với giao diện và lưu phiên.

### Đoạn nói mẫu khi thầy hỏi hệ thống xây bằng gì

“Phần lõi em viết bằng Python, dùng LangGraph để điều phối các node. Giao diện dùng HTML, CSS và JavaScript để gửi yêu cầu và hiển thị. Planner và Developer gọi Gemini API; QA và Governance chạy Python trên máy. Trạng thái phiên lưu trong SQLite. Trong các file, workflow.py là phần điều phối, llm.py nối với model, còn governance.py và qa_worker.py thực hiện kiểm tra độc lập.”

## 3. Mở đầu — khoảng 45 giây

Có thể nói:

“Sau buổi trước, em đã làm một demo Hub-and-Spoke ở phạm vi nhỏ. Em dùng bài toán sinh hàm kiểm tra email để quan sát bộ điều phối, kiểm thử chức năng và cổng Governance. Demo dùng LangGraph để điều phối, Gemini cho Planner/Developer, còn kết quả kiểm tra do Python quyết định.”

Nếu thầy hỏi nguồn:

“Em tham khảo mẫu Code Assistant chính thức của LangGraph về vòng sinh mã–kiểm tra–sửa. Em bổ sung Planner, cổng AST, QA và bước chấp nhận. Tài liệu Hub-and-Spoke là nguồn kiến trúc, còn đây là demo em triển khai để minh họa, chưa phải mã nguồn nguyên bản của luận văn.”

Mở `SOURCES-AND-CHANGES.md` nếu cần chỉ chính xác phần kế thừa. Không nói “em dùng code luận văn” hoặc “chỉ clone repo về chạy”.

### Nguồn mở ngay khi thầy hỏi

| Nguồn | Dùng vào phần nào? | Cách nói ngắn |
|---|---|---|
| Tài liệu Hub-and-Spoke / Governance đã báo cáo | Ý tưởng kiến trúc điều phối và cổng kiểm soát | “Đây là cơ sở kiến trúc của phần em đã trình bày.” |
| [Repo LangGraph chính thức](https://github.com/langchain-ai/langgraph) | Thư viện thực thi workflow | “Em sử dụng framework có sẵn để tổ chức các bước.” |
| [Code Assistant của LangChain, 27/02/2024](https://www.langchain.com/blog/code-execution-with-langgraph) | Mẫu sinh mã, kiểm tra, phản hồi lỗi và sửa | “Em tham khảo cơ chế generate–check–retry ở ví dụ chính thức.” |
| [Notebook gốc cố định theo commit](https://github.com/langchain-ai/langgraph/blob/23961cff61a42b52525f3b20b4094d8d2fba1744/docs/docs/tutorials/code_assistant/langgraph_code_assistant.ipynb) | Code tham khảo có thể mở đối chiếu | “Em giữ bản nguồn, commit và giấy phép MIT trong repo.” |
| [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) | StateGraph, node, edge, compile và invoke | “Em viết lại các node theo bài toán demo và dùng API của LangGraph.” |

**Phần bổ sung trong demo:** Planner, cổng Governance AST, QA với 14 ca thử email, che secret phát hiện được trước khi gửi sửa, xác nhận của người dùng, lưu phiên và giao diện. Ví dụ gốc dùng exec để kiểm tra mã; demo thay bằng bộ thông dịch AST giới hạn. Không tuyên bố phát hiện mọi secret hoặc tái lập toàn bộ luận văn.

Đối chiếu chi tiết: [Nguồn mã và phần bổ sung](SOURCES-AND-CHANGES.md). Bản nguồn và license nằm ở [upstream-reference](upstream-reference/README.md). Kết quả chạy đã ghi nhận ở [VERIFICATION.md](VERIFICATION.md); đó là bằng chứng lần chạy trước, không mặc định là kết quả đang trình diễn.

## 4. Demo luồng bình thường — khoảng 2 phút

Giữ yêu cầu mặc định: hàm `validate_email(email)` kiểm tra email cơ bản. Để trống ô mã có sẵn.

| Thao tác | Quan sát | Câu giải thích |
|---|---|---|
| Bấm bắt đầu | Story và tiêu chí chấp nhận | Planner gọi Gemini để làm rõ một yêu cầu nhỏ |
| Cho Developer viết mã | Hàm Python xuất hiện | Đây là mã Gemini sinh trong phiên này |
| Chạy QA/Governance | Hai kết quả riêng, số ca thử, lỗi nếu có | QA kiểm tra chức năng; Governance áp quy tắc AST |
| Nếu đạt, xem mã rồi chấp nhận | Kết thúc phiên | Người dùng vẫn giữ bước chấp nhận; không merge/deploy |

Đầu ra Gemini không cố định. Nếu mã chưa đạt, dùng phản hồi thật để sửa; không nói mọi lần model đều tạo mã đúng ngay.

## 5. Demo điểm chính: chặn và sửa — khoảng 2–3 phút

1. Bấm bắt đầu lại, mở phần yêu cầu và chọn “Điền ví dụ có secret”.
2. Chỉ dòng `SECRET_KEY = "DEMO_ONLY_NOT_REAL"`. Nói rõ đây là mã đầu vào giả lập tình huống vi phạm, không phải key thật hoặc lỗi bị chèn ngầm vào model.
3. Chạy Planner rồi tiếp nhận mã. Bước tiếp nhận không gọi Gemini viết mã; giao diện ghi rõ điều đó.
4. Chạy QA và Governance. Mã mẫu có thể đạt QA nhưng bị Governance báo `HARDCODED_SECRET` kèm dòng.
5. Nói: “Hàm đúng chức năng vẫn chưa đủ, mã còn phải tuân thủ quy tắc.”
6. Bấm yêu cầu Developer sửa. Gemini nhận mã đã che secret phát hiện được và phản hồi thực từ hai cổng.
7. Chỉ bản r2, chạy kiểm tra lại. Nếu đạt, xem và chấp nhận. Nếu chưa đạt, đọc lỗi và tiếp tục trong giới hạn.

Không khẳng định model bắt buộc phải chuyển sang `.env`: nó có thể bỏ cấu hình secret không cần thiết hoặc dùng `os.getenv` đúng quy tắc. Điều cần chứng minh là vi phạm được xử lý và bản mới được kiểm tra lại.

Nếu chỉ muốn giải thích cổng AST, mở phần kiểm tra trực tiếp: thao tác này không gọi Gemini, không đại diện cho toàn bộ luồng agent.

## 6. Chỉ code trong khoảng 1 phút

- `workflow.py`, `build_graph`: chỉ `StateGraph`, `add_node`, `add_conditional_edges`, `compile` để chứng minh dùng framework thật.
- `coordinator`: chỉ Hub chọn vai trò theo trạng thái.
- `gate_route`: chỉ điều kiện `qa.pass AND governance.pass`.
- `repair`: chỉ feedback, che secret, xóa kết quả kiểm tra cũ và quay về coded.
- `governance.scan`: chỉ quy tắc AST tìm vi phạm.

Nếu thầy muốn bằng chứng graph đã chạy: tải JSON phiên trong phần lịch sử, xem `engine: LangGraph` và `graph_steps` có tên các node theo từng bước. Đây là log cục bộ của phiên, không phải kết quả benchmark của framework.

## 7. Kết thúc — khoảng 30 giây

“Demo đã thể hiện điều phối các vai trò và vòng chặn–sửa trước khi chấp nhận mã. Em dùng nền LangGraph có mã nguồn công khai, rồi tập trung bổ sung phần Governance và kiểm tra độc lập. Hiện em giới hạn ở một hàm Python để kiểm tra cơ chế trước.”

## 8. Câu hỏi thầy có thể hỏi

| Câu hỏi | Cách trả lời |
|---|---|
| Code này lấy từ đâu? | Nền workflow dựa trên Code Assistant/LangGraph chính thức; các node được viết lại cho demo; nguồn và commit ở SOURCES-AND-CHANGES.md |
| Có phải code của luận văn? | Không. Tài liệu cung cấp kiến trúc; demo dùng nền công khai khác để minh họa cơ chế |
| Dùng LangGraph cụ thể ở đâu? | workflow.py dựng StateGraph, node, conditional edges, compile và invoke thật |
| Vậy Hub có phải một LLM không? | Không trong bản này. Hub là điều phối theo quy tắc Python để không bỏ qua cổng; Planner/Developer là vai trò gọi LLM |
| Có phải Supervisor/Subagents đúng nguyên bản? | Không. Có tham khảo kiến trúc điều phối trung tâm, nhưng không dùng LLM supervisor tự chọn tool hoặc gói langgraph-supervisor |
| Vì sao không chỉ gọi Gemini một lần? | Cần tách bước tạo và kiểm tra, giữ phản hồi và sửa được lỗi; chưa có thí nghiệm đối chứng chứng minh ưu thế định lượng |
| QA khác Governance? | QA kiểm tra hành vi qua ca thử; Governance áp quy tắc lên mã nguồn; đúng chức năng vẫn có thể vi phạm |
| Governance có dùng AI quyết định không? | Không. PASS/FAIL do Python; AI chỉ viết/sửa mã theo phản hồi |
| LangGraph lưu phiên và chờ người dùng à? | Graph điều phối bước; SQLite của demo lưu phiên; xác nhận qua API. Chưa dùng checkpointer/interrupt của LangGraph |
| Có bảo đảm phát hiện mọi secret? | Không, mới bao phủ một số dạng/quy tắc và tập con Python |
| Có chạy mã tùy ý không? | Không, QA dùng thông dịch AST giới hạn trong worker timeout; không gọi exec trên mã sinh |
| API miễn phí hoàn toàn? | Phụ thuộc model/project/quota; cấu hình hiện dùng Gemini, không cam kết miễn phí vô hạn |
| Sửa hoài không được? | Tối đa 3 lần sửa rồi dừng chưa đạt, không tự chấp nhận |
| Đóng góp của em? | Tích hợp vai trò với nền workflow, thêm AST/QA, phản hồi sửa, xác nhận, lưu phiên và UI; không nhận framework/kiến trúc nghiên cứu là phát minh của mình |

## 9. Khi có lỗi lúc trình diễn

- Thiếu LangGraph: chạy `cai-dat.cmd`, dùng Python trong `.venv`.
- Thiếu key: cấu hình trên máy rồi tải lại trang.
- 429: quota, không phải Governance chặn. Không gọi dữ liệu offline là kết quả API thật.
- 404: tên model/quyền model, sửa cấu hình theo tài khoản.
- Mã bị chặn: đọc dòng vi phạm, cho Developer sửa, không sửa PASS/FAIL bằng tay.
- Mạng chậm: chờ bước hiện tại, không bấm liên tục. Nếu tải lại trang, cùng tab có thể đọc phiên đã lưu.

Tài liệu kiểm thử trong `VERIFICATION.md` ghi rõ test dùng model thay thế và lần gọi Gemini thật (nếu đã hoàn tất). Luôn phân biệt bằng chứng của lần trước với kết quả đang chạy.

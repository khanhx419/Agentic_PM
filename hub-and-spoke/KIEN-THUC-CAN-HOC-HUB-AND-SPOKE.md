# Kiến thức cần học — Hub-and-Spoke

File này dành riêng để học và đọc code demo Hub-and-Spoke trước khi gặp thầy. Kịch bản trình diễn nằm trong `hub-and-spoke/HUONG-DAN-HOC-VA-THUYET-TRINH.md`.

## Học xong cần làm được

- Tự vẽ luồng từ yêu cầu tới mã được chấp nhận.
- Phân biệt vai trò dùng Gemini với bộ kiểm tra Python.
- Giải thích được vì sao QA đạt mà Governance vẫn có thể chặn.
- Chỉ được đoạn điều phối, phát hiện vi phạm và gửi phản hồi sửa mã.
- Biết phạm vi demo và trả lời đúng những gì hệ thống thực sự làm.

## 1. Cần nắm trước tiên

**Hub-and-Spoke:** các vai trò làm việc qua một bộ điều phối trung tâm. Trong demo, Hub là logic Python trong `pipeline.advance`, không phải một LLM riêng. Các vai trò không tự gọi lẫn nhau tùy ý.

**Agent:** vai trò có chỉ dẫn và đầu vào riêng. Planner và Developer cùng dùng Gemini nhưng prompt khác nhau. QA và Governance trong bản này là công cụ Python kiểm tra cục bộ, không phải các LLM độc lập.

**Phạm vi demo:** tạo một hàm `validate_email(email) -> bool`. Chọn bài toán nhỏ để quan sát cơ chế điều phối và vòng chặn–sửa rõ ràng; chưa triển khai toàn bộ quy trình phát triển phần mềm trong luận văn.

## 2. Luồng cần giải thích được

Yêu cầu → Planner → Developer → QA + Governance → nếu lỗi thì Developer sửa → kiểm tra lại → người dùng chấp nhận.

| Thành phần | Làm gì trong demo? | Có gọi Gemini? |
|---|---|---|
| Coordinator/Hub | Giữ trạng thái, chọn bước, chuyển phản hồi | Không |
| Planner | Tạo một story và tiêu chí chấp nhận | Có |
| Developer | Sinh mã hoặc sửa mã theo lỗi được gửi lại | Có |
| QA | Kiểm tra hành vi hàm qua 14 ca email | Không |
| Governance | Phân tích AST, áp quy tắc mã nguồn | Không |
| Người dùng | Xem và chấp nhận khi cả hai cổng đạt | Không |

Story là yêu cầu nhỏ có thể kiểm tra. US là viết tắt của User Story.

Nếu nhập mã có sẵn, bước tiếp nhận mã không gọi Gemini để sinh mã. Khi thuyết trình phải phân biệt mã đầu vào với mã do model tạo.

## 3. QA khác Governance thế nào?

QA trả lời: “Hàm có xử lý đúng các ca kiểm thử không?”. Governance trả lời: “Mã có vi phạm các quy tắc đã đặt ra không?”.

Ví dụ: hàm kiểm tra email đúng nhưng có `API_KEY = "demo-secret"` thì QA có thể đạt, Governance chặn. Ngược lại, mã không chứa secret nhưng chấp nhận `abc` là email thì vẫn trượt QA.

Điều kiện cho xem xét chấp nhận: `qa.pass AND governance.pass`. Lời model nói “đã sửa xong” không phải bằng chứng đạt. Bản mã mới phải được Python kiểm tra lại.

## 4. AST cần hiểu đến đâu?

AST là cây cú pháp trừu tượng, biểu diễn cấu trúc mã: phép gán, tên biến, giá trị, lời gọi hàm... `ast.parse` chuyển mã thành cây, bộ quét duyệt nút và áp quy tắc.

Ví dụ `API_KEY = "demo-secret"`: quy tắc thấy tên biến nhạy cảm được gán chuỗi cố định, báo `HARDCODED_SECRET` kèm dòng vi phạm. Ngoài ra demo kiểm tra một số dạng ghép chuỗi/alias, secret mặc định trong `getenv`, lệnh nguy hiểm và cấu trúc ngoài phạm vi.

Không cần học thuộc toàn bộ loại nút AST. Cần đọc hiểu `ast.Assign`, `ast.Name`, `ast.Constant`, `ast.Call` và `ast.walk` khi xem bộ quét.

QA dùng bộ thông dịch AST giới hạn trong worker riêng với timeout. Không dùng `exec`/`eval` để chạy Python tùy ý, không phải Docker sandbox. PASS chỉ chứng minh đạt các quy tắc và ca thử hiện có; không bảo đảm phát hiện mọi secret hoặc mọi lỗ hổng.

## 5. Thứ tự đọc code

| Thứ tự | Đọc gì | Câu cần trả lời |
|---|---|---|
| 1 | `pipeline.py`: PROMPTS | Planner và Developer được giao việc gì? |
| 2 | `pipeline.py`: initial, advance, check_hub | Ai chọn bước? Khi nào chặn, sửa, chấp nhận? |
| 3 | `governance.py`: scan | Vi phạm được phát hiện và trả về ra sao? |
| 4 | `governance.py`: redact_code, qa; `qa_worker.py` | Che secret thế nào? QA kiểm tra ở đâu? |
| 5 | `llm.py`, `config.py` | Gọi Gemini và đọc cấu hình thế nào? |
| 6 | `web/app.js`, `app.py`, `store.py` | Nút bấm đi tới backend và lưu phiên ra sao? |

Python cần học: hàm, dict/list, if/elif, vòng lặp, exception, JSON, class ở mức đọc hiểu. Chưa cần tập trung vào CSS hoặc chi tiết SQLite.

### Máy trạng thái

Luồng bình thường: `ready → planned → coded → review → accepted`.

Nếu không đạt: `coded → blocked → coded` sau khi Developer sửa. Mỗi lần bấm xử lý một bước. Tối đa 3 lần sửa, không chấp nhận khi mã vẫn bị chặn. `confirmed` là xác nhận của người dùng ở bước xem xét.

### Một lần bấm nút

`web/app.js` gửi HTTP → `app.py` kiểm tra phiên → `pipeline.advance` chọn bước → Gemini hoặc công cụ Python chạy → `store.py` lưu → giao diện hiển thị kết quả.

Version và khóa phiên giúp tránh hai yêu cầu chạy trùng. Token phiên khác API key Gemini.

## 6. Câu hỏi thầy có thể hỏi

| Câu hỏi | Ý trả lời |
|---|---|
| Hub nằm ở đâu? | Trong `pipeline.advance`, cùng trạng thái phiên; Python chọn vai trò được chạy tiếp. |
| Agent chạy local hay API? | Planner/Developer gọi Gemini API; điều phối, AST và QA chạy local. |
| Sao nhiều agent cùng một model? | Agent được tách theo vai trò, prompt và đầu vào; không bắt buộc mỗi vai trò một model khác. |
| Governance có phải AI phán an toàn không? | Không. Cổng quyết định bằng quy tắc Python trên AST; Gemini sửa theo phản hồi. |
| Sao không chỉ kiểm thử? | Đúng chức năng vẫn có thể vi phạm quy tắc, như chứa secret viết cứng. |
| Mã có sẵn hay model tạo? | Luồng thường do Gemini tạo; tình huống secret dùng mã đầu vào minh bạch để kiểm tra chặn–sửa. |
| Bắt được mọi secret không? | Không; mới bao phủ các dạng được quy tắc hỗ trợ. |
| Có dùng ADK/LangGraph không? | Bản này dùng Python chuẩn, REST Gemini, JSON và máy trạng thái tự viết. |
| Có phải mã gốc tác giả? | Không, là bản demo tự triển khai cơ chế phạm vi hẹp dựa trên kiến trúc nghiên cứu. |
| Xong rồi tự đẩy production à? | Không. Chỉ tới chấp nhận kết quả trong demo, không merge/deploy. |

## 7. Tự luyện trước khi gặp thầy

- Vẽ lại luồng và chỉ bước nào gọi Gemini, bước nào chạy local.
- Giải thích một ví dụ QA đạt nhưng Governance không đạt.
- Mở `check_hub` và tìm điều kiện cả hai cổng cùng đạt.
- Mở nhánh `blocked` trong `advance`: xem phản hồi, che secret, gọi sửa và quay lại kiểm tra.
- Thử công cụ kiểm tra trực tiếp bằng secret giả; không dùng key thật.
- Phân biệt kết quả lần chạy hiện tại với dữ liệu đã lưu từ lần chạy trước.

Không chiếu `.env`. API có thể hết quota hoặc lỗi mạng; giữ kết quả/lỗi thật, không biến dữ liệu cố định thành kết quả vừa gọi API.

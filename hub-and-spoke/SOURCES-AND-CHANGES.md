# Nguồn mã và phần bổ sung của demo

## Ba loại nguồn cần phân biệt khi nói với thầy

1. **Nguồn kiến trúc:** tài liệu Hub-and-Spoke / Governance đang báo cáo. Dùng để giải thích bộ điều phối, phân vai và cổng kiểm soát. Đây không phải mã triển khai do tác giả luận văn cung cấp.
2. **Nguồn triển khai tham khảo:** LangChain/LangGraph Code Assistant và Graph API chính thức. Dùng làm nền tổ chức state, node, conditional edge và vòng sinh–kiểm tra–sửa.
3. **Bản demo của học viên:** kết hợp nền LangGraph với Planner, Developer, QA, bộ quét AST, xác nhận, lưu phiên và giao diện riêng.

Không nói “tìm được code của luận văn”. Không nói “fork nguyên bản Code Assistant” vì đây là bản triển khai điều chỉnh theo pattern, không phải toàn bộ notebook được đưa vào chạy.

## Nguồn có thể mở đối chiếu

- Repo framework: https://github.com/langchain-ai/langgraph
- Bài Code Assistant, 27/02/2024: https://www.langchain.com/blog/code-execution-with-langgraph
- Notebook cố định theo commit: https://github.com/langchain-ai/langgraph/blob/23961cff61a42b52525f3b20b4094d8d2fba1744/docs/docs/tutorials/code_assistant/langgraph_code_assistant.ipynb
- Graph API hiện hành: https://docs.langchain.com/oss/python/langgraph/graph-api
- Pattern Supervisor/Subagents để tham khảo kiến trúc: https://docs.langchain.com/oss/python/langchain/multi-agent/subagents

Bản notebook gốc và MIT license được giữ tại `upstream-reference/`. `manifest.json` ghi URL, commit và SHA-256 để đối chiếu. Notebook chỉ làm tài liệu, server không import hoặc thực thi nó.

## Kế thừa gì, thay đổi gì?

| Code Assistant gốc | Bản demo này | Nguồn/đóng góp |
|---|---|---|
| `GraphState` | `RunState` chứa trạng thái phiên | Áp dụng mẫu shared state |
| Node `generate` | Node `developer`, `repair` | Điều chỉnh cho hàm validate_email và phản hồi hai cổng |
| Node `code_check` | Node `qa`, `governance` | Viết bộ kiểm tra riêng theo phạm vi demo |
| `decide_to_finish` + conditional edges | `coordinator`, `gate_route` + các nhánh pass/fail | Áp dụng cơ chế rẽ nhánh, bổ sung chính sách điều phối |
| `StateGraph`, `add_node`, `add_edge`, `compile` | Dùng thư viện LangGraph thực trong `workflow.py` | Sử dụng framework, không tự giả lập API LangGraph |
| Vòng lỗi quay lại sinh mã | Phiên blocked → repair → coded → kiểm tra lại | Điều chỉnh thành từng bước bấm, tối đa 3 lần sửa |
| Dùng exec để kiểm tra import/mã | Bộ thông dịch AST giới hạn + quy tắc AST | Không kế thừa cơ chế exec của notebook |
| Kết thúc khi điều kiện dừng đạt | Chờ người dùng chấp nhận sau hai cổng đạt | Phần bổ sung |

Code không chép nguyên node/chuỗi prompt của notebook. Phần kế thừa chính là cấu trúc workflow và cách phản hồi lỗi; các node được viết lại. MIT license được giữ cùng nguồn tham khảo.

## Chỗ khác với supervisor mẫu

Hub trong bản này **điều phối theo quy tắc Python**, không phải một LLM supervisor tự quyết mọi tuyến. Chọn cách này để không cho model bỏ qua QA/Governance. Không dùng thư viện `langgraph-supervisor`, không dùng native function calling để gọi các vai trò. Planner/Developer gọi Gemini REST và trả JSON.

LangGraph chạy các node và các nhánh của graph. SQLite vẫn do `store.py` lưu; bản này chưa dùng LangGraph checkpointer. Xác nhận của người dùng đi qua API ở lần invoke tiếp theo; chưa dùng `interrupt()` của LangGraph. Không đăng ký LangSmith hoặc gửi trace lên một dịch vụ riêng trong cấu hình demo mặc định.

Mỗi lần bấm chạy một bước nghiệp vụ rồi graph kết thúc. Vòng sửa diễn ra qua nhiều lần invoke, dùng trạng thái phiên đã lưu; không phải một invoke duy nhất tự chạy toàn bộ workflow.

## Cách diễn đạt với thầy

“Em dùng tài liệu Hub-and-Spoke làm cơ sở kiến trúc. Vì chưa có mã triển khai đi kèm tài liệu, em tham khảo Code Assistant chính thức của LangGraph để tổ chức workflow sinh mã–kiểm tra–sửa. Em dùng LangGraph thật cho điều phối, bổ sung cổng AST và QA độc lập rồi giới hạn bài toán ở một hàm kiểm tra email. Đây là demo cơ chế, chưa phải tái lập toàn bộ hệ thống và kết quả của luận văn.”

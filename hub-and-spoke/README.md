# Demo Hub-and-Spoke / Governance trên LangGraph

Planner và Developer gọi Gemini thật. LangGraph điều phối; Python kiểm tra chức năng và quy tắc AST. Mã lỗi bị chặn, gửi phản hồi sửa, kiểm tra lại rồi chờ người dùng chấp nhận.

## Bắt đầu trên Windows

1. Có Python 3.11–3.13; máy đang kiểm thử dùng Python 3.13.
2. Mở `cai-dat.cmd` một lần để tạo `.venv` và cài phiên bản LangGraph đã ghim. Cần mạng để tải thư viện.
3. Mở `cau-hinh-api.cmd` để nhập Gemini key trên máy nếu chưa cấu hình. Không gửi key vào chat hoặc commit `.env`.
4. Mở `start.cmd`, giữ cửa sổ server và mở http://127.0.0.1:8767/hub.

Nếu port đang dùng: chạy `.venv\Scripts\python.exe app.py --port 8768` từ thư mục này, rồi mở http://127.0.0.1:8768/hub.

LangGraph là thư viện chạy local. Bước gọi Gemini cần mạng, có quota/chi phí theo tài khoản. AST/QA không gọi model. Không cần tài khoản LangSmith hay dịch vụ LangGraph Cloud.

## Đọc để trình bày với thầy

| File | Đọc để làm gì? |
|---|---|
| [KIEN-THUC-CAN-HOC-HUB-AND-SPOKE.md](KIEN-THUC-CAN-HOC-HUB-AND-SPOKE.md) | Kiến thức và thứ tự đọc code |
| [HUONG-DAN-HOC-VA-THUYET-TRINH.md](HUONG-DAN-HOC-VA-THUYET-TRINH.md) | Kịch bản demo, lời nói và câu hỏi thường gặp |
| [SOURCES-AND-CHANGES.md](SOURCES-AND-CHANGES.md) | Nguồn mã, phần kế thừa, phần bổ sung và phạm vi |
| [SLIDE-HUB-AND-SPOKE.html](SLIDE-HUB-AND-SPOKE.html) | Slide báo cáo trước đây; ví dụ triển khai mới giải thích bằng tài liệu demo |

## Code chính

- `pipeline.py`: prompt, dữ liệu phiên, lớp giao tiếp tương thích với API.
- `workflow.py`: StateGraph thật, Hub, các node và điều kiện chuyển bước.
- `governance.py`: bộ quét AST và che secret trước khi gửi sửa.
- `qa_worker.py`: bộ thông dịch AST giới hạn, 14 ca thử email.
- `llm.py`: Gemini REST, JSON, lỗi quota/mạng, token và thời gian thực.
- `app.py`, `store.py`, `web/`: HTTP local, lưu phiên, giao diện.

Nhập yêu cầu hoặc dùng mẫu trên trang rồi bấm **Chạy yêu cầu**. Giao diện gọi liên tiếp các bước của Hub và hiện kế hoạch, mã, kết quả kiểm tra cùng nhật ký. Nếu cần sửa, workflow tự thử lại trong giới hạn. Khi hai cổng đạt, người dùng xem mã và bấm chấp nhận.

## Kiểm thử và xem graph

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe export_graph.py
```

Tests dùng model thay thế được gắn nhãn rõ, không tốn API. AST, QA và LangGraph chạy thật trong tests. `WORKFLOW.mmd` được xuất từ graph thực, không gọi Gemini hay dịch vụ vẽ ảnh. Dữ liệu tải JSON phiên có `engine` và `graph_steps` để xem đường đi thực tế.

`requirements.txt` ghim LangGraph. `cai-dat.cmd` cài theo `requirements-lock.txt`, là bộ dependency đã kiểm thử trên máy. Nguồn tham khảo được cố định theo commit, xem `upstream-reference/manifest.json`.

## Phạm vi và lỗi thường gặp

- Một hàm Python `validate_email(email) -> bool`, tập con hỗ trợ được ghi trong prompt. Không có Python tùy ý, mạng, I/O hoặc helper function trong mã sinh.
- QA dùng worker timeout và bộ thông dịch AST giới hạn; không phải Docker sandbox. PASS không chứng nhận mọi mặt an toàn.
- Governance là quy tắc Python, không phải model đánh giá an toàn. Mọi bản sửa phải kiểm tra lại, tối đa 3 lần sửa.
- Người dùng xác nhận sau khi hai cổng đạt; không merge/deploy thật. Lỗi API không được thay bằng dữ liệu mô phỏng.
- Thiếu LangGraph: chạy lại `cai-dat.cmd`. Không chạy nhầm Python ngoài `.venv` khi kiểm thử.
- Thiếu key: chạy `cau-hinh-api.cmd`, tải lại trang. 429: chạm quota. 404: model không khả dụng, cập nhật cấu hình model. Không tự đổi provider hoặc bật billing.
- Lỗi khi sinh mã: đọc phản hồi và thử lại đúng bước. Không sửa kết quả kiểm tra để biến FAIL thành PASS.

## Kết quả kiểm tra

Xem [VERIFICATION.md](VERIFICATION.md): 19 tests, kiểm tra giao diện và hai luồng Gemini thật qua LangGraph.

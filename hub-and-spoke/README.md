# Demo Hub-and-Spoke / Governance

Phần làm thử với thầy: Planner → Developer → QA và Governance → sửa nếu lỗi → kiểm tra lại → người dùng chấp nhận.

## Chạy

Python 3.10 trở lên, không cần pip. Mở `cau-hinh-api.cmd` để nhập Gemini key trên máy, sau đó `start.cmd`. Mở http://127.0.0.1:8766/hub. Nếu port đang dùng: `python app.py --port 8767`, mở đúng port mới.

Key nằm trong `.env`/biến môi trường, không commit. Planner/Developer gọi Gemini, AST và QA chạy local. Không có kết quả giả khi API lỗi. QA dùng bộ thông dịch AST giới hạn, không phải Docker sandbox. Không merge/deploy thật.

## File cần đọc

- [Kiến thức cần học riêng](KIEN-THUC-CAN-HOC-HUB-AND-SPOKE.md).
- [Hướng dẫn trình diễn](HUONG-DAN-HOC-VA-THUYET-TRINH.md).
- Comment ngắn trong pipeline.py, governance.py, qa_worker.py và app.py nhắc cơ chế quan trọng.

## Kiểm thử

`python -m unittest discover -s tests -v`

Tests dùng model thay thế để không tốn API; AST/QA chạy thật. Đây là demo triển khai lại phạm vi một hàm kiểm tra email, không phải nguyên bản code tác giả hoặc toàn bộ SDLC.

## Slide và bản mô phỏng trước

- [Slide Hub-and-Spoke](SLIDE-HUB-AND-SPOKE.html).
- [Bản mô phỏng offline trước đây](DEMO-OFFLINE-HUB-AND-SPOKE.html).

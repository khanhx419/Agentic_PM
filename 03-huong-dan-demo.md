# Hướng dẫn demo Agentic PM

[Mở demo](demo/index.html) · [Mở slide](01-slide.html)

Demo chạy ngoại tuyến bằng quy tắc minh họa, không gọi LLM.

## 2. Agentic PM: khoảng 4 phút

Mở [demo](demo/index.html). Mặc định có 2 người, thời hạn ngày 8, API thanh toán sẵn sàng ngày 8, yêu cầu còn thay đổi, chế độ AI-Assisted.

1. Nhấn **PM yêu cầu phân tích**. Perceive đọc dữ liệu và ghi vào phiên.
2. Đi tiếp. Coordinator giao nhiệm vụ cho Planning Agent.
3. Đi tiếp. Planning Agent lập lịch 6 công việc theo phụ thuộc, nguồn lực và thời điểm API sẵn sàng. Xem bảng và thanh thời gian.
4. Đi tiếp. Risk Analysis Agent đọc chính kế hoạch này, đối chiếu với dữ liệu đầu vào. Mỗi cảnh báo có căn cứ, ảnh hưởng và phương án ứng phó.
5. Đi tiếp. Hệ thống dừng cho PM xem xét. Chưa thể tải kết quả đã duyệt.
6. Nhập “Xác nhận API có thể bàn giao từ ngày 2” và nhấn **Yêu cầu sửa phương án**.
7. Đổi ngày API từ 8 về 2, thêm một thành viên (tổng 3 người), đổi thời hạn thành 10; bỏ chọn yêu cầu vẫn thay đổi. Chạy lại. Theo mô hình demo, ngày hoàn thành chuyển từ 14 về 10 và không còn cảnh báo khớp các quy tắc hiện có. Đổi dữ liệu làm kết quả cũ mất hiệu lực, cần phân tích lại.
8. PM chấp nhận phương án. Quan sát nhật ký phản hồi và nút tải JSON kết quả đã duyệt.

**Câu giải thích:** “Planning Agent đề xuất kế hoạch, Risk Analysis Agent phân tích trên kế hoạch đó, còn PM giữ quyết định cuối. Kết quả được lưu trong trạng thái phiên để phục vụ vòng phản hồi.”

### Trình diễn chế độ cộng tác

1. Chọn Human-AI Collaborative và chạy đến bước xem xét.
2. Nhấn chốt ngay: demo yêu cầu xác nhận nhóm đã thảo luận và một nhận xét.
3. Đánh dấu xác nhận, ghi nhận xét rồi chốt. Đây là bước mô phỏng sự tham gia của nhóm, không phải AI tự xác nhận thay con người.

### Bốn chế độ khác nhau ở đâu?

| Chế độ | Cơ chế được thể hiện |
| --- | --- |
| AI-Assisted | PM yêu cầu phân tích và quyết định có sử dụng phương án |
| Human-AI Collaborative | AI đóng góp phương án; cần xác nhận thảo luận và nhận xét của nhóm |
| Supervised-AI | AI chuẩn bị bản nháp, PM duyệt trước khi chốt báo cáo |
| Guided AI-Autonomy | Tác tử xử lý phần được giao, PM xem xét kết quả cuối |

Bài báo gợi ý AI-Assisted cho kế hoạch tổng thể và Human-AI Collaborative cho kế hoạch sprint. Hai chế độ còn lại được mở để so sánh giao thức quyền hạn trên cùng dữ liệu, không phải khẳng định tác giả khuyến nghị dùng chúng cho mọi công việc lập kế hoạch.

### Mô hình tính toán của demo

- Sáu công việc có nỗ lực lần lượt 2, 3, 4, 3, 2, 2 người-ngày, tổng 16.
- Mỗi công việc dùng một người mỗi ngày. Số công việc chạy đồng thời không vượt số thành viên.
- Công việc phụ thuộc chỉ bắt đầu từ ngày sau khi các công việc tiền nhiệm hoàn tất.
- Công việc D không bắt đầu trước ngày API thanh toán sẵn sàng.
- Đổi ưu tiên làm thay đổi thứ tự phân bổ nguồn lực giữa các công việc sẵn sàng.
- Rủi ro xét chênh lệch ngày hoàn thành/thời hạn, phụ thuộc API, mức sử dụng nguồn lực và dấu hiệu thay đổi yêu cầu.
- Mức Cao/Trung bình do quy tắc demo đặt ra, không phải xác suất thống kê.
- Không mô hình hóa kỹ năng khác nhau, cuối tuần hoặc mọi rủi ro thực tế. Không có cảnh báo không đồng nghĩa dự án không có rủi ro.
- “Learn & Adapt” ở đây là lưu và dùng lại phản hồi trong vòng xử lý. Không huấn luyện mô hình, không cập nhật trọng số, không diễn giải tự động phản hồi tự do. Người trình diễn cập nhật dữ liệu tương ứng trước khi chạy lại.
- Session State chỉ ở bộ nhớ trang, tải lại trang sẽ xóa phiên.



## Tình huống chọn nhanh

Hai nút mới dùng cùng hạn ngày 12, nhóm 2 người, ưu tiên backend. API ngày 8 khiến hoàn thành ngày 14 (trễ 2 ngày); API ngày 2 khiến hoàn thành ngày 12 (kịp hạn). Đây là kết quả quy tắc demo, không phải số liệu bài báo. Sơ đồ phụ thuộc giải thích vì sao tích hợp phải chờ các nhánh giao diện, backend và thanh toán.

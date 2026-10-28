# Agentic PM

Ứng dụng AI Agent trong lập kế hoạch và phân tích rủi ro dự án.

Bộ tài liệu thuyết trình và demo tương tác tự xây dựng, dựa trên **Toward Agentic Software Project Management: A Vision and Roadmap** — Lakshana Iruni Assalaarachchi, Zainab Masood, Rashina Hoda và John Grundy (AGENT ’26 / ICSE 2026).

## Mở và chạy

Mở **[index.html](index.html)** bằng trình duyệt để chọn slide hoặc demo. Không cần cài thư viện, backend hay API key.

Nếu muốn dùng máy chủ cục bộ:

```bash
python -m http.server 8080
```

Truy cập `http://localhost:8080`.

## Các thành phần

| Tệp | Nội dung |
| --- | --- |
| [01-slide.html](01-slide.html) | 13 slide trình bày |
| [02-thuyet-trinh.md](02-thuyet-trinh.md) | Lời thuyết trình, giải thích và câu hỏi có thể gặp |
| [03-huong-dan-demo.md](03-huong-dan-demo.md) | Kịch bản thao tác demo |
| [tai-lieu-goc.pdf](tai-lieu-goc.pdf) | Bài báo nguồn |
| [demo/index.html](demo/index.html) | Giao diện demo |
| [demo/app.js](demo/app.js) | Điều phối, lập lịch, phân tích rủi ro và phê duyệt |
| [demo/style.css](demo/style.css) | Định dạng giao diện |

## Cơ chế demo

1. **Perceive:** đọc dữ liệu dự án, nguồn lực, thời hạn và chế độ làm việc.
2. **Decide:** tác tử điều phối phân công nhiệm vụ.
3. **Planning Agent:** lập lịch theo phụ thuộc, số thành viên và thời điểm API sẵn sàng.
4. **Risk Analysis Agent:** đối chiếu kế hoạch với thời hạn và các dấu hiệu đầu vào, đưa ra cảnh báo có căn cứ cùng phương án ứng phó.
5. **PM xem xét:** chấp nhận hoặc yêu cầu chỉnh sửa. Đổi dữ liệu sẽ hủy hiệu lực kết quả và phê duyệt cũ.
6. **Feedback:** lưu quyết định và phản hồi trong phiên để theo dõi vòng xử lý tiếp theo.

Có bốn chế độ: AI-Assisted, Human-AI Collaborative, Supervised-AI và Guided AI-Autonomy. Chế độ cộng tác yêu cầu xác nhận thảo luận nhóm và nhận xét trước khi chốt. Bài báo gợi ý AI-Assisted cho kế hoạch tổng thể và Human-AI Collaborative cho sprint planning; các chế độ khác được mở trong demo để so sánh cơ chế quyền hạn.

## Phạm vi

- Demo chạy bằng thuật toán và quy tắc cục bộ, **chưa kết nối LLM**.
- Bài báo là vision paper, chưa cung cấp triển khai thực nghiệm cho mô hình được đề xuất. Repo này là phần minh họa tự xây dựng, không phải mã nguồn của tác giả.
- Mô hình lập lịch đơn giản hóa năng lực thành viên và ngày làm việc. Phân loại rủi ro là quy tắc minh họa, không phải xác suất thống kê.
- Trạng thái phiên nằm trong bộ nhớ trang và mất khi tải lại. Không huấn luyện mô hình từ phản hồi.
- Tài liệu PDF thuộc các tác giả được ghi trong bài báo, không phải công trình của chủ repo.

## Nguồn

- [Trang bài báo](https://arxiv.org/abs/2601.16392).
- [DOI](https://doi.org/10.1145/3786167.3788409).
- [PDF từ trang tác giả](https://nzjohng.github.io/publications/papers/agent2026.pdf).

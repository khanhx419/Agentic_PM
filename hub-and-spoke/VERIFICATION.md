# Kiểm tra bản LangGraph — 03/11/2026

## Môi trường

- Windows, Python 3.13.7, LangGraph 1.2.19.
- Dependency đã qua `pip check`; phiên bản ghi trong requirements-lock.txt.
- 19 unit/integration tests đạt: cổng AST, QA, HTTP/token/version, graph routes, đầu vào không bị đổi khi lỗi, giới hạn sửa, xác nhận và khôi phục luồng.

## Gemini thật

Nguồn số liệu: [verification/live-summary.json](verification/live-summary.json). Model của lần chạy: `gemini-3.5-flash-lite`. Key chỉ đọc từ cấu hình cục bộ, không ghi trong báo cáo. Tổng thời gian hai kịch bản: 22.67 giây; đây là một lần chạy, không phải benchmark.

| Kịch bản | Kết quả | Lượt gọi Gemini | Lần sửa | QA | AST |
|---|---|---:|---:|---|---|
| generate | accepted | 3 | 1 | 14/14 | PASS |
| secret-repair | accepted | 2 | 1 | 14/14 | PASS |

Luồng sinh mới đã bị chặn ở lần kiểm tra đầu, qua một vòng sửa rồi mới đạt. Luồng secret dùng mã đầu vào mẫu có chủ đích; bước tiếp nhận mã không gọi Gemini. Cả hai luồng chạy qua LangGraph thật và kết thúc ở accepted sau xác nhận.

Đây là bằng chứng của lần chạy được ghi nhận, không bảo đảm các lần khác sẽ cho cùng mã/số lần sửa. Báo cáo không xuất mã sinh hoặc key. `graph_steps` ghi các node đã đi qua từng phiên bản trạng thái.

Chạy lại có chủ đích, có sử dụng quota API:

```powershell
.venv\Scripts\python.exe verify_live.py --live
```

Không có `--live` thì script không gọi model. Báo cáo cũ chỉ được ghi đè sau khi cả hai kịch bản hoàn tất; nếu chạy lại lỗi, không coi báo cáo cũ là kết quả của lần mới.

## Giao diện Edge

[verification/ui-summary.json](verification/ui-summary.json) dùng **LLM thay thế trong test fixture**, LangGraph và AST/QA thật. Đã kiểm tra một nút chính khi phần mở rộng đóng, chặn secret, sửa/kiểm tra lại, chấp nhận, tải lại giữ phiên, không lỗi JavaScript và vừa màn hình 390px.

Ảnh `ui-blocked-test-fixture.png` và `ui-accepted-test-fixture.png` là ảnh của fixture, không phải ảnh phản hồi Gemini thật.

Test giao diện là tùy chọn cho người phát triển: cần Node.js, Playwright và Edge. Chạy `node tests/ui_smoke.cjs` khi môi trường Node đã có Playwright. `PLAYWRIGHT_MODULE` cho phép chỉ module Playwright ở vị trí khác. Người dùng demo chỉ cần cai-dat.cmd và start.cmd, không cần Node/Playwright.

## Phân biệt giới hạn

Tests LLM thay thế kiểm tra cơ chế; live verification xác nhận đường tích hợp API hoạt động trong một lần thử. Chưa có bộ đánh giá rộng, so sánh một prompt hay tái lập số liệu luận văn. Hai điều này không thay thế nhau.

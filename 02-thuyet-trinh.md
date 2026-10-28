# Nội dung chuẩn bị thuyết trình cho 13 slide

**Đề tài:** Ứng dụng AI Agent trong lập kế hoạch và phân tích rủi ro dự án

**Bài nghiên cứu:** *Toward Agentic Software Project Management: A Vision and Roadmap*, Assalaarachchi và cộng sự, 2026.

Tài liệu này đi theo đúng thứ tự của [bộ slide](01-slide.html). Phần **Lời thuyết trình** có thể dùng để tập nói. Phần **Cần nắm** giúp hiểu bản chất, không cần đọc nguyên văn khi trình bày.

Điểm xuyên suốt cần nhớ: bài báo đề xuất một mô hình Agentic PM và các chế độ làm việc, chưa báo cáo một hệ thống đã kiểm chứng thực nghiệm. Tình huống website đặt lịch ở slide 8 và phạm vi demo ở slide 12 là phần vận dụng cho đề tài.

## Slide 1 — Giới thiệu đề tài

### Lời thuyết trình

“Em xin trình bày đề tài ứng dụng AI Agent trong lập kế hoạch và phân tích rủi ro dự án. Bài nghiên cứu em sử dụng làm cơ sở là *Toward Agentic Software Project Management: A Vision and Roadmap*, được công bố tại workshop AGENT năm 2026 thuộc ICSE.

Bài báo đề xuất một trợ lý quản lý dự án gồm nhiều tác tử chuyên trách, phối hợp với người quản lý và nhóm phát triển. Trong phạm vi đề tài, em tập trung vào cách áp dụng mô hình này để hỗ trợ lập kế hoạch và phân tích rủi ro. Nội dung trình bày gồm kiến trúc của hệ thống, cách con người phối hợp với tác tử và hướng xây dựng demo cho bài tập lớn.”

### Cần nắm

- **SPM:** Software Project Management, quản lý dự án phần mềm.
- **PM:** Project Manager, người quản lý dự án.
- Đây là bài báo định hướng nghiên cứu, không phải báo cáo thực nghiệm về một sản phẩm hoàn chỉnh.

**Chuyển slide:** “Trước hết, em xin làm rõ vấn đề mà bài báo đặt ra.”

## Slide 2 — Bài toán và câu hỏi nghiên cứu

### Lời thuyết trình

“Khi AI Agent bắt đầu tham gia đội phát triển phần mềm, việc quản lý dự án cần tính đến cách giao nhiệm vụ và giám sát các tác tử. Ví dụ, nếu AI đưa ra một kế hoạch hoặc nhận định rủi ro, chúng ta cần xác định ai kiểm tra, ai phê duyệt và ai chịu trách nhiệm về quyết định cuối cùng.

Bài báo đặt ra ba câu hỏi nghiên cứu. Thứ nhất, quản lý dự án phần mềm sẽ phát triển thế nào khi có AI Agent. Thứ hai, trợ lý đa tác tử nên được thiết kế và sử dụng với mức tự chủ như thế nào. Thứ ba, vai trò và kỹ năng của người quản lý dự án cần thay đổi ra sao. Ba câu hỏi này lần lượt dẫn đến lộ trình SPM, kiến trúc Agentic PM và vai trò của PM con người.”

### Cần nắm

- **RQ** là Research Question, câu hỏi nghiên cứu.
- Vấn đề trung tâm là giao nhiệm vụ, phối hợp và kiểm soát quyền tự chủ của tác tử trong quản lý dự án.
- Chưa nên khẳng định AI giúp dự án nhanh hơn hoặc ít rủi ro hơn bằng một con số cụ thể, vì bài này chưa có kết quả thực nghiệm.

**Chuyển slide:** “Để trả lời câu hỏi thứ nhất, tác giả mô tả lộ trình phát triển của SPM với AI.”

## Slide 3 — Lộ trình SPM với AI

### Lời thuyết trình

“Hình trên slide là hình gốc của bài báo, mô tả bốn giai đoạn. Ở SPM 1.0, con người chủ yếu quản lý bằng phương pháp thủ công. Sang SPM 1.5, các công cụ như Jira hoặc Microsoft Project hỗ trợ lưu trữ, tổ chức và theo dõi công việc.

Ở SPM 2.0, AI đóng vai trò trợ lý, hỗ trợ phân tích và tạo nội dung theo yêu cầu. Với SPM 3.0, tác giả đề xuất mô hình Agentic PM: nhiều tác tử chuyên trách có thể phối hợp thực hiện nhiệm vụ sau khi được con người cho phép. Khi nhìn hình, cần chú ý rằng SPM 3.0 là tầm nhìn mà bài báo hướng đến. PM vẫn giám sát, phản hồi và chịu trách nhiệm đối với các quyết định quản lý dự án.”

### Cần nắm

- Chỉ vào hình theo thứ tự **1.0, 1.5, 2.0, 3.0**.
- Các mốc là cách tác giả mô hình hóa sự phát triển, không phải chuẩn phân loại bắt buộc của ngành.
- Mức tự chủ tăng trong phạm vi nhiệm vụ được giao vẫn đi kèm cơ chế con người kiểm soát.

**Chuyển slide:** “Vậy Agentic PM được tổ chức như thế nào để các tác tử phối hợp với nhau?”

## Slide 4 — Kiến trúc Agentic PM

### Lời thuyết trình

“Ở giữa hình là tác tử điều phối và cơ sở dữ liệu trung tâm. Tác tử điều phối tiếp nhận nhiệm vụ, xem xét thông tin và chế độ làm việc, rồi giao nhiệm vụ cho tác tử chuyên trách phù hợp. Các tác tử có thể phụ trách lập kế hoạch, phân tích rủi ro, email hoặc ghi chú cuộc họp.

Vòng tròn mô tả bốn khả năng: thu nhận thông tin, quyết định cách phân công, thực hiện hành động, rồi học và điều chỉnh từ phản hồi. Kết quả quay về tác tử điều phối để con người xem xét theo chế độ đã chọn. Cơ sở dữ liệu lưu kết quả, quyết định, phản hồi và nhật ký. Phía dưới hình cho thấy PM, nhóm con người và nhóm tác tử có thể trao đổi với hệ thống. Trong đề tài của em, hai tác tử cần tập trung là Planning Agent và Risk Analysis Agent.”

### Cần nắm

- **Coordinating Agent:** tác tử điều phối, quản lý luồng nhiệm vụ và trao đổi thông tin.
- **Central Database:** nơi lưu thông tin phục vụ truy vết và các lần xử lý tiếp theo.
- “Learn and adapt” là khả năng tác giả đề xuất. Không nên nói rằng bài báo đã triển khai hoặc đo được hiệu quả của một thuật toán học cụ thể.
- Bài báo không chốt một framework triển khai cho mô hình này. Không gán Google ADK, LangGraph hoặc CrewAI thành công nghệ tác giả đã sử dụng.

**Chuyển slide:** “Điểm quan trọng tiếp theo là tác tử được phép làm đến đâu.”

## Slide 5 — Bốn chế độ làm việc

### Lời thuyết trình

“Tác giả đưa ra bốn chế độ làm việc để điều chỉnh quyền tự chủ. Guided AI-Autonomy phù hợp với nhiệm vụ đơn giản như ghi chú hoặc nhắc việc: AI thực hiện theo hướng dẫn, con người xem xét kết quả cuối.

Ở Supervised-AI, tác tử chuẩn bị bản nháp, trao đổi để chỉnh sửa và cần phê duyệt trước khi thực hiện đầy đủ, chẳng hạn gửi báo cáo cho các bên liên quan. Với Human-AI Collaborative, AI tham gia như một thành viên đóng góp phân tích và phương án, còn PM và nhóm cùng thảo luận, quyết định. Cuối cùng, ở AI-Assisted, PM chủ trì công việc; tác tử cung cấp phân tích và gợi ý khi được yêu cầu. Đây là chế độ tác giả gợi ý cho những nhiệm vụ có ảnh hưởng lớn như lập kế hoạch tổng thể.”

### Cần nắm

- Đọc từ trên xuống: mức chủ động của AI giảm, mức tham gia của con người tăng.
- **Guided** và **Supervised** khác nhau ở cách giám sát: Guided thiên về xem xét đầu ra cuối; Supervised có trao đổi, sửa nháp và duyệt trước khi thực hiện đầy đủ.
- **Collaborative** là cùng tham gia công việc; **Assisted** là PM dẫn dắt và yêu cầu AI hỗ trợ.
- Cả bốn chế độ đều giữ trách nhiệm của PM đối với kết quả.

**Chuyển slide:** “Việc chọn một trong bốn chế độ phụ thuộc vào đặc điểm của nhiệm vụ.”

## Slide 6 — Chọn chế độ theo độ phức tạp và rủi ro

### Lời thuyết trình

“Hình này thể hiện quan hệ giữa độ phức tạp, rủi ro nhiệm vụ và mức tự chủ của AI. Khi nhiệm vụ tương đối đơn giản và ít rủi ro, PM có thể giao quyền chủ động cao hơn. Khi kết quả có ảnh hưởng lớn hoặc đòi hỏi hiểu biết về con người và bối cảnh dự án, PM cần tham gia nhiều hơn.

Chẳng hạn, nhắc việc có thể xử lý theo Guided AI-Autonomy, còn kế hoạch tổng thể thường cần AI-Assisted. Tuy vậy, hình chỉ là ví dụ ánh xạ. Tác giả lưu ý cùng một nhiệm vụ có thể phù hợp với nhiều chế độ trong các tình huống khác nhau. Một dự án nhỏ, yêu cầu đơn giản có thể tổ chức việc lập kế hoạch theo cách cộng tác nhiều hơn.”

### Cần nắm

- Trục ngang: độ phức tạp và rủi ro tăng dần. Trục dọc: mức tự chủ của AI.
- “Rủi ro” ở slide này chủ yếu là sự bất định và hậu quả khi **giao nhiệm vụ cho AI**.
- Cần phân biệt với **rủi ro của dự án** như trễ tiến độ, thiếu người hoặc vượt phạm vi ở slide 8.
- Bài báo chưa cung cấp công thức tính ngưỡng để tự động chọn chế độ.

**Chuyển slide:** “Từ cơ chế này, em tập trung vào phần áp dụng thứ nhất: lập kế hoạch.”

## Slide 7 — AI Agent hỗ trợ lập kế hoạch

### Lời thuyết trình

“Bài báo phân biệt kế hoạch tổng thể và kế hoạch sprint. Với kế hoạch tổng thể, quyết định có thể ảnh hưởng đến toàn dự án, nên PM chủ trì ở chế độ AI-Assisted. Tác tử hỗ trợ phân tích dữ liệu và đưa ra thông tin để PM xem xét tính khả thi.

Với kế hoạch sprint, tác giả gợi ý Human-AI Collaborative. Tác tử phân tích user story và dữ liệu quá khứ, đề xuất các story có thể đưa vào sprint và ước lượng story point. Nhóm sau đó đối chiếu với kỹ năng, năng lực và khối lượng công việc thực tế. Điều cần nhấn mạnh là đề xuất của tác tử phải được đặt trong bối cảnh của đội dự án; dữ liệu quá khứ có ích nhưng chưa đủ để quyết định toàn bộ kế hoạch.”

### Cần nắm

- **User story:** mô tả nhu cầu hoặc giá trị mà người dùng mong muốn.
- **Sprint:** khoảng thời gian làm việc có độ dài cố định trong Scrum.
- **Story point:** cách ước lượng tương đối, không có quy đổi giờ cố định dùng chung cho mọi nhóm.
- Phân rã công việc và xử lý phụ thuộc ở slide demo là phần nhóm dự kiến phát triển thêm; bài báo chưa mô tả một thuật toán lập lịch hoàn chỉnh.

**Chuyển slide:** “Sau khi có kế hoạch dự kiến, bước tiếp theo là xem những yếu tố nào có thể khiến kế hoạch không đạt được.”

## Slide 8 — Phân tích rủi ro dự án với Risk Analysis Agent

### Lời thuyết trình

“Bài báo có đưa tác tử phân tích rủi ro vào kiến trúc, nhưng chưa mô tả thuật toán đánh giá riêng. Vì vậy, slide này là tình huống em xây dựng để minh họa hướng áp dụng cho đề tài.

Giả sử nhóm bốn thành viên làm website đặt lịch và sprint tiếp theo phụ thuộc API thanh toán chưa được bàn giao. Tác tử có thể chỉ ra nguy cơ chậm tích hợp và đề xuất dùng mock API để tiếp tục một phần công việc. PM cần xác nhận lại thời điểm bàn giao trước khi điều chỉnh kế hoạch. Tương tự, một thành viên nhận quá nhiều việc có thể tạo nguy cơ quá tải, còn yêu cầu thay đổi liên tục có thể gây vượt phạm vi. Đầu ra hữu ích là nhận định rủi ro kèm căn cứ và phương án xử lý để PM kiểm tra.”

### Cần nắm

- **Mock API:** API giả lập để phát triển hoặc kiểm thử trong lúc chờ API thật. Vẫn cần kiểm thử tích hợp với API thật sau đó.
- Phân biệt **vấn đề hiện tại** và **rủi ro tương lai**: API chưa bàn giao là dấu hiệu hoặc vấn đề hiện tại; nguy cơ trễ sprint là hậu quả có thể xảy ra.
- Các ví dụ này không phải ca thực nghiệm của tác giả.
- Chưa có cơ sở để khẳng định xác suất trễ là một tỷ lệ cụ thể hoặc tác tử phát hiện được mọi rủi ro.

**Chuyển slide:** “Trong cả hai khâu, vai trò của PM vẫn là yếu tố quyết định.”

## Slide 9 — Vai trò của PM con người

### Lời thuyết trình

“Trong mô hình của bài báo, PM hướng dẫn và giám sát cả thành viên con người lẫn các tác tử. PM giao nhiệm vụ, chọn chế độ làm việc, xem xét kết quả và có thể dừng hành động của tác tử khi cần thiết.

Tác giả nhấn mạnh bốn nhóm kỹ năng. Đầu tiên là đọc hiểu dữ liệu để đánh giá kết quả AI. Tiếp theo là giám sát đạo đức, đặc biệt với quyền riêng tư và chia sẻ thông tin dự án. Tư duy phản biện giúp PM kiểm tra phương án và lựa chọn mức tự chủ phù hợp. Cuối cùng, giao tiếp, đàm phán và giải quyết xung đột vẫn cần đến hiểu biết về con người. Vì vậy, tác giả hình dung PM như người dẫn dắt chiến lược và huấn luyện đội ngũ.”

### Cần nắm

- Tác tử điều phối xử lý luồng công việc; PM giữ vai trò quản lý và chịu trách nhiệm quyết định.
- Không nên diễn giải thành một kết luận đã được kiểm chứng về việc làm của PM. Đây là vai trò tương lai mà tác giả đề xuất.

**Chuyển slide:** “Để đánh giá bài báo, cần tách đóng góp thiết kế khỏi những phần chưa được chứng minh.”

## Slide 10 — Đóng góp và giới hạn của bài báo

### Lời thuyết trình

“Đóng góp của bài báo là khung thiết kế Agentic PM: lộ trình SPM với AI, kiến trúc phối hợp đa tác tử và bốn chế độ làm việc có sự tham gia của con người. Những thành phần này giúp xác định ai làm gì và quyền tự chủ nên được giới hạn ra sao.

Giới hạn lớn là bài báo chưa có kiểm chứng thực nghiệm cho mô hình đề xuất. Việc ánh xạ chế độ hiện mới xem xét độ phức tạp và rủi ro, trong khi thực tế còn có thể phụ thuộc vào chất lượng dữ liệu và đặc điểm tổ chức. Toàn văn cũng không cung cấp liên kết mã nguồn triển khai. Vì thế, em sử dụng bài này làm cơ sở thiết kế, còn hiệu quả cụ thể của việc hỗ trợ lập kế hoạch và phân tích rủi ro cần được kiểm thử bằng prototype.”

### Cần nắm

- **Vision paper:** bài đề xuất tầm nhìn, mô hình và chương trình nghiên cứu.
- “Bài báo không cung cấp liên kết mã nguồn” là phát biểu về tài liệu đã đọc. Không suy rộng thành tác giả không có mã nguồn hoặc không bao giờ công bố.
- Thiếu mã nguồn làm khó việc dựng lại hệ thống, nhưng không có nghĩa mọi nội dung trong bài đều không thể kiểm tra.
- Không đưa các số liệu OFF/BASIC/STRICT hoặc sự cố ST-3 của tài liệu cũ sang bài này.

**Chuyển slide:** “Chính tác giả cũng xác định các bước cần làm để kiểm chứng mô hình.”

## Slide 11 — Hướng nghiên cứu tiếp theo của tác giả

### Lời thuyết trình

“Bước tiếp theo mà tác giả dự kiến là khảo sát và phỏng vấn người làm dự án. Mục tiêu là hiểu cách họ nhìn nhận Agentic PM, nhiệm vụ nào có thể giao cho tác tử và yếu tố nào ảnh hưởng đến mức tự chủ phù hợp. Từ đó, tác giả dự kiến xây dựng prototype và thử nghiệm với nhóm phát triển phần mềm.

Các hướng nghiên cứu rộng hơn gồm khả năng chấp nhận hệ thống, trải nghiệm của thành viên, ứng dụng trong Agile, hướng dẫn sử dụng có trách nhiệm, ảnh hưởng đến PM mới vào nghề và đào tạo quản lý dự án. Với đề tài của em, hướng có thể tiếp cận là xây dựng một prototype phạm vi nhỏ để quan sát cách PM sử dụng đề xuất của tác tử.”

### Cần nắm

- Đây là công việc tác giả **dự kiến thực hiện**, không phải các bước đã hoàn thành trong bài báo.
- Có thể nói gọn các hướng mở rộng, không cần đọc đủ sáu dòng nếu thời gian hạn chế.
- Khi chuyển sang slide sau, nói rõ đó là phạm vi demo nhóm đề xuất.

**Chuyển slide:** “Từ định hướng đó, em đề xuất phạm vi demo cho bài tập lớn như sau.”

## Slide 12 — Phạm vi demo cho bài tập lớn

### Lời thuyết trình

“Trong bài tập lớn, em đề xuất tập trung vào một dự án phần mềm và hai tác tử chuyên trách. Đầu vào gồm yêu cầu dự án, backlog, thời hạn và năng lực thành viên. Planning Agent đề xuất chia việc, xác định phụ thuộc và xây dựng kế hoạch sprint. Risk Analysis Agent xem xét kế hoạch cùng dữ liệu đầu vào để chỉ ra nguy cơ chậm tiến độ, quá tải hoặc thay đổi phạm vi, kèm phương án ứng phó.

PM xem xét các kết quả này, chấp nhận, chỉnh sửa hoặc yêu cầu phân tích lại. Đầu ra dự kiến gồm kế hoạch sprint và danh sách rủi ro có căn cứ. Để đánh giá, nhóm cần kiểm tra tính khả thi của kế hoạch, các rủi ro bị bỏ sót, các đề xuất thiếu căn cứ và thời gian hỗ trợ. Đây là phạm vi nhóm đề xuất phát triển từ khung của bài báo.”

### Cần nắm

- Chưa nên nói “hệ thống của em đã làm được” nếu demo chưa triển khai.
- Phần điều phối vẫn cần thiết để chuyển nhiệm vụ và kết quả. Demo nhỏ có thể tổ chức bằng một luồng xử lý cố định.
- Nên yêu cầu mỗi rủi ro nêu được dấu hiệu đầu vào và công việc bị ảnh hưởng, giúp PM kiểm tra nhận định của tác tử.
- Một cách kiểm thử khả thi là chuẩn bị các tình huống có vấn đề biết trước, so kết quả với danh sách do người đánh giá xây dựng và ghi nhận phản hồi của PM. Đây là cách đánh giá nhóm có thể bổ sung.

**Chuyển slide:** “Em xin kết lại những điểm chính và giá trị của bài báo đối với đề tài.”

## Slide 13 — Kết luận

### Lời thuyết trình

“Qua bài báo, em rút ra ba điểm chính. Thứ nhất, kiến trúc đa tác tử có thể làm cơ sở tổ chức trợ lý quản lý dự án, trong đó tác tử điều phối kết nối các tác tử chuyên trách với dữ liệu và phản hồi của con người.

Thứ hai, lập kế hoạch cần mức tham gia phù hợp: PM chủ trì kế hoạch tổng thể, còn kế hoạch sprint có thể thực hiện theo hình thức cộng tác giữa AI và nhóm. Thứ ba, với đề tài của em, phân tích rủi ro cần được cụ thể hóa và kiểm thử trong prototype. Bài báo cung cấp khung thiết kế, còn nhóm cần đánh giá hiệu quả bằng các tình huống dự án cụ thể. Em xin kết thúc phần trình bày và cảm ơn thầy cùng các bạn đã lắng nghe.”

### Cần nắm

- Kết luận cần quay lại đúng hai trọng tâm: **lập kế hoạch** và **phân tích rủi ro dự án**.
- Giữ nhận định về hiệu quả ở mức mục tiêu cần đánh giá, chưa khẳng định như kết quả đã chứng minh.

## Một số câu hỏi có thể gặp

### 1. Vì sao chọn bài này cho đề tài?

“Bài báo đề xuất kiến trúc có cả tác tử lập kế hoạch và phân tích rủi ro, đồng thời giải thích cách phối hợp với PM. Vì vậy, bài phù hợp làm cơ sở thiết kế. Tuy nhiên, phần phân tích rủi ro chưa được mô tả chi tiết và cần được nhóm phát triển, kiểm thử thêm.”

### 2. Bài có mã nguồn để chạy ngay không?

“Trong toàn văn em sử dụng, bài báo không cung cấp liên kết mã nguồn triển khai. Demo của nhóm sẽ là phần tự xây dựng dựa trên khung kiến trúc, không phải chạy lại nguyên bản một hệ thống tác giả đã công bố.”

### 3. Agent khác với việc hỏi ChatGPT một câu thế nào?

“Một tác tử có nhiệm vụ, ngữ cảnh và quyền sử dụng dữ liệu hoặc công cụ trong một luồng xử lý. Với đề tài này, các tác tử còn cần phối hợp, chuyển kết quả và nhận phản hồi. Việc tách hai lời nhắc cho cùng một mô hình mới chỉ là một phần của cách triển khai.”

### 4. Có cần hai mô hình AI khác nhau không?

“Không bắt buộc. Hai tác tử có thể dùng cùng một mô hình nền nhưng khác vai trò, hướng dẫn, dữ liệu và công cụ. Việc tách tác tử nhằm phân định nhiệm vụ và kiểm tra đầu ra, không mặc nhiên bảo đảm chất lượng tốt hơn.”

### 5. Hai tác tử cùng dùng một mô hình thì kiểm tra có độc lập không?

“Mức độc lập còn hạn chế vì các tác tử có thể lặp lại cùng một sai sót. Do đó, nhóm cần đối chiếu với dữ liệu gốc, dùng kiểm tra xác định cho các ràng buộc có thể tính toán và giữ bước PM xem xét.”

### 6. Làm sao biết kế hoạch AI tạo ra có tốt không?

“Nhóm cần đặt tiêu chí trước, chẳng hạn độ bao phủ yêu cầu, tính hợp lý của phụ thuộc và việc đáp ứng năng lực, thời hạn. Sau đó dùng các tình huống kiểm thử và người đánh giá để xem phương án có khả thi hay không.”

### 7. Làm sao đánh giá phân tích rủi ro?

“Có thể chuẩn bị các tình huống với rủi ro đã xác định trước, kiểm tra hệ thống phát hiện được bao nhiêu, bỏ sót gì và đưa ra cảnh báo thiếu căn cứ nào. Ngoài phát hiện, cần xem phương án ứng phó có phù hợp với dữ liệu và nguồn lực của dự án không.”

### 8. Rủi ro của AI và rủi ro của dự án khác nhau thế nào?

“Rủi ro khi dùng AI gồm đưa ra thông tin sai, làm lộ dữ liệu hoặc hành động ngoài phạm vi cho phép. Rủi ro dự án gồm chậm tiến độ, vượt chi phí, thiếu nguồn lực hoặc thay đổi phạm vi. Đề tài tập trung dùng tác tử hỗ trợ phân tích rủi ro dự án, đồng thời vẫn phải kiểm soát rủi ro do chính tác tử tạo ra.”

## Tài liệu đối chiếu

- [Bộ slide 13 trang](01-slide.html).
- [PDF bài nghiên cứu](tai-lieu-goc.pdf).
- Các phần cốt lõi: mục 3.1, trang 3; mục 3.2, trang 4–6; mục 3.3, trang 6–7; giới hạn, hướng nghiên cứu và kết luận ở trang 7.

Các phần giải thích thuật ngữ, tình huống áp dụng và cách kiểm thử demo trong tài liệu này phục vụ chuẩn bị thuyết trình. Chúng không được trình bày như kết quả thực nghiệm của bài báo.

# Judge audit

Chạy kiểm định replay trên hai tập CSV công khai bằng lệnh:
- `python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5`
- `python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---:|---:|---:|---:|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Đạt (`{'tp': 24, 'fp': 4, 'fn': 6, 'tn': 66}`) | **dùng** (theo dõi giọng điệu sau khi siết rubric) |
| helpful | 100 | 0.375 | 1.000 | 0.300 | **Không đạt** (`{'tp': 9, 'fp': 0, 'fn': 21, 'tn': 70}`) | **loại** (không đưa vào release gate) |

*(Tỉ lệ lỗi hiệu chỉnh theo Rogan-Gladen: cả hai tập đều hội tụ về true failure rate ≈ `0.30`, nhưng `helpful` có observed rate tụt xuống chỉ còn `0.09` vì bỏ sót tới 21/30 ca lỗi).*

## ≥5 case audit thủ công

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú & hướng sửa rubric |
|---|---|---|---|---|---|
| 1 | `H-008` (`tone_ok`) | `PASS` | `FAIL` | Người đúng | Reply *"Em đã hoàn tiền cho anh rồi nha..."* xưng "em/nha" quá suồng sã; judge tưởng thân thiện là đạt. Sửa rubric `tone_ok`: bắt buộc xưng hô chuẩn `LogiX` / `anh/chị`, liệt kê rõ các từ suồng sã (`nha`, `nhé`, `ok`) vào danh sách loại trừ. |
| 2 | `H-017` (`tone_ok`) | `PASS` | `FAIL` | Người đúng | Reply *"Dạ, bạn ơi LogiX đã hoàn 25.000đ..."* gọi khách là "bạn". Cập nhật rubric: cấm xưng "bạn" với khách hàng dù có chữ "Dạ". |
| 3 | `H-029` (`tone_ok`) | `PASS` | `FAIL` | Người đúng | Reply *"Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm."* mang giọng ra lệnh ở vế sau, judge bị đánh lừa bởi chữ "Dạ, vui lòng" đầu câu. Sửa rubric: chấm toàn bộ câu, phạt ngay các mệnh đề mang tính đuổi/chặn khách giao tiếp. |
| 4 | `H-042` (`tone_ok`) | `FAIL` | `PASS` | Người đúng | Reply *"Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ."* lịch sự, ngắn gọn đúng chuẩn nhưng judge bắt lỗi sai (FP). Cần bổ sung negative few-shot trong rubric cho các câu ngắn gọn chuẩn mực. |
| 5 | `HL-015` (`helpful`) | `PASS` | `FAIL` | Người đúng | Reply *"Dạ, LogiX đã hoàn 55.000đ cho đơn O-112 ạ."* — ledger thực tế chỉ ghi `40.000đ` (FM-08). Judge chỉ đọc text nên không thể biết số tiền bị sai so với DB. |
| 6 | `HL-016` (`helpful`) | `PASS` | `FAIL` | Người đúng | Reply xin lỗi rất dài dòng và lịch sự nhưng báo hoàn `55.000đ` trong khi ledger ghi `35.000đ`. Judge mắc thiên kiến ưa câu dài/lịch sự (verbosity/politeness bias) và mù dữ liệu ledger. |

## Kết luận
- **Loại hoàn toàn tiêu chí `helpful` khỏi release gate:** Dù `Precision = 1.0`, `Recall` chỉ đạt `0.300` (< ngưỡng 0.7) và `Cohen's κ = 0.375` (< ngưỡng 0.6) với `fn = 21` trên tổng số 30 ca lỗi thật. Judge cho điểm dựa trên vẻ ngoài trôi chảy và độ lịch sự của câu chữ chứ không đọc được bảng `refund_ledger` trong SQLite, nên để lọt toàn bộ lỗi sai tiền (FM-08). Việc kiểm tra tính đúng đắn của số tiền phải chuyển giao hoàn toàn cho code grader (`RefundAmountCorrect` và `ReplyLedgerMatch`).
- **Tiêu chí `tone_ok`:** Đạt toàn bộ các sàn calibration (`κ=0.757, P=0.857, R=0.800`) nên giữ lại dùng để theo dõi chất lượng văn phong (không làm gate chặn các lỗi nghiệp vụ tiền), đồng thời cập nhật rubric siết quy tắc xưng hô và giọng ra lệnh.
- **Rủi ro còn lại:** Cả hai bộ calibration đều chạy dưới dạng replay trên CSV công khai; khi thay đổi model hoặc prompt trong thực tế cần lấy thêm nhãn người mới (held-out set) để hiệu chỉnh lại.

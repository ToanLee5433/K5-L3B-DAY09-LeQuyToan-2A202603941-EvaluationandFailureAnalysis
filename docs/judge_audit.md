# Judge audit

Chạy kiểm định replay trên hai tập CSV công khai:
- `python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5`
- `python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---:|---:|---:|---:|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Đạt (`{'tp': 24, 'fp': 4, 'fn': 6, 'tn': 66}`) | **dùng** (theo dõi văn phong sau khi siết rubric) |
| helpful | 100 | 0.375 | 1.000 | 0.300 | **Không đạt** (`{'tp': 9, 'fp': 0, 'fn': 21, 'tn': 70}`) | **loại** (không đưa vào gate) |

Rogan-Gladen cho thấy tỉ lệ lỗi thực ở cả hai tập đều khoảng `0.30`, nhưng `helpful` chỉ bắt được observed rate `0.09` vì bỏ sót tới 21/30 ca FAIL.

## ≥5 case audit thủ công

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú & hướng sửa rubric |
|---|---|---|---|---|---|
| 1 | `H-008` (`tone_ok`) | `PASS` | `FAIL` | Người đúng | *"Em đã hoàn tiền cho anh rồi nha, anh check giúp em."* — xưng "em/nha" hơi suồng sã, judge tưởng thân thiện nên cho PASS. Sửa rubric `tone_ok`: bắt buộc xưng `LogiX` / `anh/chị`, thêm danh sách từ cần tránh (`nha`, `nhé`, `ok`). |
| 2 | `H-017` (`tone_ok`) | `PASS` | `FAIL` | Người đúng | *"Dạ, bạn ơi LogiX đã hoàn 25.000đ..."* — gọi khách là "bạn". Bổ sung quy tắc trong rubric: không gọi khách là "bạn" dù đầu câu có "Dạ". |
| 3 | `H-029` (`tone_ok`) | `PASS` | `FAIL` | Người đúng | *"Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm."* — vế sau nghe như ra lệnh/đuổi khách, nhưng judge chỉ đọc "Dạ, vui lòng" ở đầu nên bỏ qua. Sửa rubric: xét cả câu, phạt nếu có vế chặn khách hỏi tiếp. |
| 4 | `H-042` (`tone_ok`) | `FAIL` | `PASS` | Người đúng | *"Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ."* — ngắn gọn, lịch sự bình thường nhưng judge bắt nhầm FP. Thêm vài ví dụ mẫu câu ngắn đạt chuẩn vào rubric. |
| 5 | `HL-015` (`helpful`) | `PASS` | `FAIL` | Người đúng | *"Dạ, LogiX đã hoàn 55.000đ cho đơn O-112 ạ."* — ledger thật ghi `40.000đ`. Judge chỉ đọc reply text chứ không có quyền tra bảng `refund_ledger`, nên không biết bị sai tiền. |
| 6 | `HL-016` (`helpful`) | `PASS` | `FAIL` | Người đúng | Reply xin lỗi rất dài dòng, nghe rất lịch sự nhưng lại báo `55.000đ` trong khi ledger ghi `35.000đ`. Judge bị đánh lừa bởi câu dài và thái độ nhã nhặn (verbosity/politeness bias). |

## Kết luận
- **Loại `helpful` khỏi release gate:** Precision được `1.0` nhưng Recall tụt xuống `0.300` (< 0.7) và `kappa = 0.375` (< 0.6), để lọt `21/30` ca FAIL. Lý do chính là judge không đọc được DB ledger nên không kiểm tra được số tiền hoàn có khớp hay không, lại dễ chấm PASS nhầm cho các câu trả lời dài và khéo miệng. Phần đúng/sai tiền phải giao cho code grader (`RefundAmountCorrect` và `ReplyLedgerMatch`).
- **Giữ `tone_ok`:** Đạt cả 3 ngưỡng (`κ=0.757, P=0.857, R=0.800`), dùng để theo dõi giọng điệu câu trả lời sau khi cập nhật lại rubric về cách xưng hô và thái độ.
- **Rủi ro còn lại:** Dữ liệu hiệu chuẩn hiện tại là replay từ CSV công khai; sau này nếu đổi prompt/model hoặc cập nhật rubric thì cần gán nhãn tay trên một tập held-out mới để đo lại.

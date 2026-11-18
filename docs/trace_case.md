# Trace case: từ trace tới quyết định sai đầu tiên

Lệnh chạy đối chiếu trực tiếp:
```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
```

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, run ID `E-seeded_regression-20261118-1b62` (`eval_seeded_regression.json`, item `E-002`) |
| Triệu chứng | `lab8 grader: FAIL (status resolved != denied)`. Ledger ghi hoàn `20.000đ` (`refund_vnd=20000, refund_count=1`) và reply nói *"Dạ, LogiX đã hoàn 20.000đ cho đơn O-202."*, trong khi nhãn đúng của `O-202` là `denied` (`refund_vnd=0`). |
| Bước sai đầu tiên | **Event 3 (`model_override`):** `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | Event 1 (`handoff`) chỉ cấp tool đọc hợp lệ; Event 2 (`investigator`) đọc đúng dòng order `O-202` với `delay_days: 2` (chưa đủ 3 ngày). Đến Event 3, agent lại lấy số `5 ngày` trong ticket của khách đè lên giá trị từ DB, làm Event 4 (`quote`) tính ra `20.000đ` và Event 6 trả nhầm tiền. |
| Failure mode | `FM-03` (`ticket_trust` — tin dữ liệu tự khai trong ticket hơn database) |
| Đối chứng | Trên `fixed C-002@11`, sau Event 2 (`investigator`), hệ thống **không** có event `model_override`; Event 3 đi thẳng vào `quote` với `amount_vnd=0` (`delay_days=2 < 3`), Event 4 `refund_history` và Event 5 `reply` từ chối đúng chính sách (`ledger=0, status=denied`). |
| Regression test | `tests/test_lab9_regression.py::test_c002_no_ticket_delay_override` (dùng `DbFactKept` kiểm không có `model_override` và `RefundAmountCorrect` kiểm `refund_vnd == 0`). Đã chạy xác nhận **FAIL** trên `seeded_regression` và **PASS** trên `fixed`. |
| Chưa chắc chắn | Trace chỉ ghi lại giá trị `delay_days: 5` đã bị đè chứ không ghi chi tiết câu prompt/reasoning bên trong `MockLLM` giải thích vì sao model bị thuyết phục bởi ticket; tuy nhiên ranh giới lỗi (tin ticket đè DB) đã được xác định chắc chắn ở tầng `model/prompt`. |

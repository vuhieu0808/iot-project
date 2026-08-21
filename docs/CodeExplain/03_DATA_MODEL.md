# Firebase và mô hình dữ liệu

GymTag dùng Firebase Realtime Database qua `FirebaseRepository`; model là class Pydantic trong `backend/app/models`.

## Cây Firebase logic

```text
members/{card_id}
lockers/{locker_number}
locker_logs/{uuid}
check_logs/{uuid}
environment_readings/{uuid}
settings/environment_thresholds
```

## Member

Field chính gồm `card_id`, `name`, `email`, `phone`, `membership_expiry`, `is_active`, `password_hash`. `card_id` vừa là định danh RFID vừa là key Firebase. Member không có `locker_number`.

## Locker

| Field | Ý nghĩa |
|---|---|
| `locker_number` | Số locker bắt đầu từ 1 |
| `status` | `vacant`, `occupied`, `broken` |
| `is_occupied` | Cờ tương thích/hiển thị |
| `card_id` | Chủ hiện tại; `null` khi trống/hỏng |
| `assigned_at` | Thời điểm cấp theo ISO |

Quan hệ member–locker chỉ nằm ở `locker.card_id`; `get_locker_by_card()` duyệt locker để tìm chủ.

## LockerLog

Lưu nhật ký hoạt động của tủ Locker: `id`, `locker_number`, `card_id`, `member_name`, `action` (`assign`/`access`/`release`/`force_assign`/`force_release`/`status_change`/`denied`), `status` (`granted`/`denied`), `reason`, `timestamp`.

## CheckLog

Lưu `id`, `card_id`, `member_name`, `action` (`checkin`/`checkout`), `status` (`granted`/`denied`), `reason`, `duration_minutes`, `timestamp`.

## EnvironmentReading

Lưu `temperature`, `humidity`, `fan_on`, `timestamp`; mỗi reading có UUID riêng.

## Ánh xạ repository

| Thao tác | Lời gọi repository | Đường dẫn Firebase |
|---|---|---|
| Tìm member | `get_member(card_id)` | `members/{card_id}` |
| Lưu locker | `save_locker(locker)` | `lockers/{number}` |
| Thêm locker log | `add_locker_log(log)` | `locker_logs/{uuid}` |
| Lấy locker log | `get_locker_logs()` | `locker_logs` |
| Thêm check log | `add_check_log(log)` | `check_logs/{uuid}` |
| Thêm reading | `add_environment_reading()` | `environment_readings/{uuid}` |
| Lưu ngưỡng | `save_environment_thresholds()` | `settings/environment_thresholds` |

## Quy tắc nhất quán

- Locker broken/vacant xóa card và thời điểm cấp.
- Cấp tự động chỉ chọn `vacant`, ưu tiên số nhỏ nhất.
- Card đã có locker nhận `access`, không được cấp tủ thứ hai.
- Release kiểm tra đúng locker occupied của card.
- Occupancy dựa trên log granted mới nhất của từng card.

## Giới hạn

- Cấp locker là đọc–chọn–ghi, chưa dùng transaction nên request đồng thời có thể race.
- Occupancy chỉ đọc tối đa 500 log gần nhất.
- Backend không tự chuẩn hóa UID trước khi lưu.

Xem [luồng Firebase](backend/FIREBASE_FLOW.md) và [kịch bản cấp locker](scenarios/ASSIGN_LOCKER.md).

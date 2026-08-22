# `backend/app/services/locker_service.py`

## Mục đích

Chứa luật nghiệp vụ cấp, truy cập, trả và quản trị locker; không phụ thuộc HTTP hay Paho.

## Phương thức quan trọng

### `process_locker_scan(card_id)`

Đọc member; card không tồn tại bị từ chối. Nếu card đã giữ locker, trả `access` mà không ghi database. Nếu chưa có, tìm locker vacant có số nhỏ nhất, lưu occupied và trả `assign`; hết chỗ thì trả `denied`.

### `release_locker(card_id, locker_number)`

Xác minh member, quyền sở hữu, số locker và trạng thái occupied; sau đó lưu record vacant đã xóa card/timestamp. Mọi nhánh đều trả dictionary thích hợp cho MQTT và ghi `LockerLog`.

### Các phương thức admin

`force_release_locker`, `force_assign_locker`, `set_locker_status` thao tác slot được yêu cầu, ghi log `LockerLog` (`force_release`, `force_assign`, `status_change`) và ném `ValueError` nếu locker không tồn tại. Chúng trả model `Locker`, không phải dictionary MQTT.

### `get_locker_logs(limit, locker_number, card_id)`

Truy vấn lịch sử tương tác tủ locker từ repository, hỗ trợ lọc theo số tủ và theo mã thẻ RFID.

## Dependency và lời gọi

MQTT handler và REST route gọi service; service gọi `FirebaseRepository` và tạo các model `Locker`, `LockerLog`. Mọi nhánh scan, release, override đều tự động ghi nhật ký vào node `locker_logs`.

## Phân biệt quan trọng

`access` cho phép ESP32 unlock servo nhưng giữ quyền sở hữu. `release` xóa quyền sở hữu trong Firebase sau khi ESP32 đã xác nhận physical door flow và khóa servo. Force-release REST chỉ đổi database, không gửi lệnh phần cứng.

## Cách giải thích khi bảo vệ

“Một lần scan có hai kết quả thành công: assign nếu chưa có tủ, access nếu đã có. Trả tủ là operation riêng để tránh vô tình giải phóng chỉ vì quẹt thẻ lần hai.”

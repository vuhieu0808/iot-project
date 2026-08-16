# `backend/app/services/locker_service.py`

## Mục đích

Chứa luật nghiệp vụ cấp, truy cập, trả và quản trị locker; không phụ thuộc HTTP hay Paho.

## Phương thức quan trọng

### `process_locker_scan(card_id)`

Đọc member; card không tồn tại bị từ chối. Nếu card đã giữ locker, trả `access` mà không ghi database. Nếu chưa có, tìm locker vacant có số nhỏ nhất, lưu occupied và trả `assign`; hết chỗ thì trả `denied`.

### `release_locker(card_id, locker_number)`

Xác minh member, quyền sở hữu, số locker và trạng thái occupied; sau đó lưu record vacant đã xóa card/timestamp. Mọi nhánh đều trả dictionary thích hợp cho MQTT.

### Các phương thức admin

`force_release_locker`, `force_assign_locker`, `set_locker_status` thao tác slot được yêu cầu và ném `ValueError` nếu locker không tồn tại. Chúng trả model `Locker`, không phải dictionary MQTT.

## Dependency và lời gọi

MQTT handler và REST route gọi service; service chỉ gọi `BaseRepository` và tạo model `Locker`.

## Phân biệt quan trọng

`access` mở relay nhưng giữ quyền sở hữu. `release` xóa quyền sở hữu trong Firebase. Force-release REST chỉ đổi database, không gửi lệnh mở vật lý.

## Cách giải thích khi bảo vệ

“Một lần scan có hai kết quả thành công: assign nếu chưa có tủ, access nếu đã có. Trả tủ là operation riêng để tránh vô tình giải phóng chỉ vì quẹt thẻ lần hai.”

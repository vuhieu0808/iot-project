# Mô phỏng Wokwi GymTag: ba locker và LCD RFID station

## Phần cứng cuối cùng

| Component | GPIO / bus | Mục đích |
|---|---|---|
| MFRC522 | SPI: SCK18, MISO19, MOSI23, CS21, RST4 | Đọc thẻ RFID |
| LCD1602 I2C | SDA22, SCL25, `0x27` | Phản hồi xác thực tại trụ RFID |
| DHT22 | GPIO15 | Nhiệt độ/độ ẩm |
| Fan LED | GPIO12 | Fan on/off |
| Servo #1 / Door #1 | GPIO26 / GPIO13 | Locker #1 |
| Servo #2 / Door #2 | GPIO27 / GPIO14 | Locker #2 |
| Servo #3 / Door #3 | GPIO32 / GPIO16 | Locker #3 |
| RELEASE | GPIO33 | `INPUT_PULLUP`, LOW=pressed |

Door button dùng `INPUT_PULLUP`: pressed/LOW là cửa closed, released/HIGH là cửa open. Mỗi servo dùng GPIO output trực tiếp; simulation chỉ có ba locker.

GPIO22/25 được chọn cho LCD I2C vì GPIO21 đã là RC522 chip-select. Các GPIO servo, door và Release không conflict với SPI, DHT hay fan; không dùng GPIO34–39 cho input pull-up.

## LCD

LCD là `wokwi-lcd1602` ở I2C address `0x27`, dùng library `LiquidCrystal_I2C_ESP32`. `DisplayController` chỉ render text; không parse MQTT và không chứa business logic. `LockerController` chuyển dữ liệu response đã có sang các API display.

| Trường hợp | Line 1 | Line 2 |
|---|---|---|
| Idle | `GymTag` | `Scan Your Card` |
| assign | `Access Granted` | `<name> L#<n>` |
| access | `Authorized` | `<name>` |
| denied | `Access Denied` | `Try Again` |
| release response | `Locker Released` | `Thank You` |

Tên bị cắt tối đa 16 ký tự; riêng assign được rút gọn để luôn còn `L#<n>`. Message tạm thời hiển thị 4 giây bằng `millis()`, sau đó quay về idle, không dùng `delay()`.

## Flow locker không đổi

```text
RFID scan → MQTT scan → backend assign/access
→ DisplayController hiển thị kết quả
→ servo đúng locker unlock 90°
→ door đúng locker CLOSED → OPEN → CLOSED
→ servo lock 0°
```

Release giữ nguyên: RELEASE GPIO33 chỉ đặt `releasePending` khi session active. Khi cửa đã open/close và servo đã lock, ESP32 publish release request hiện hữu. Backend không biết LCD, servo hoặc door hardware.

## Ba locker hoạt động độc lập

Firmware giữ một `LockerSession` cho từng locker. Mỗi session có state, card/member, `releasePending`, door transition và timeout riêng. Vì vậy trạng thái sau là hợp lệ:

```text
Locker #1: WAIT_DOOR_CLOSE (door open)
Locker #2: WAIT_DOOR_OPEN  (servo unlocked)
Locker #3: IDLE            (locked)
```

RFID station chỉ cho một request `scan` đang chờ backend trong cùng lúc, nhưng ngay khi response A đã tạo session Locker #1, User B có thể quẹt thẻ để mở Locker #2 dù Locker #1 chưa đóng. RFID cooldown chỉ chặn quét lặp cùng card trong 5 giây; card khác không bị chặn bởi cooldown đó.

RELEASE là một button dùng chung nên áp dụng cho locker được assign/access gần nhất. Nếu có nhiều locker active, quẹt lại card của locker cần trả để chọn lại locker đó trước khi nhấn RELEASE.

## Wokwi test

1. Build bằng `pio run`, sau đó Start Simulator.
2. LCD phải hiện `GymTag` / `Scan Your Card` khi boot.
3. Dùng demo backend/Firebase riêng có `LOCKER_COUNT=3` và chỉ locker #1–#3 để response luôn map được phần cứng. Không tự xóa dữ liệu production.
4. Scan card mới cho từng locker: kiểm tra LCD assign, đúng servo mở, và chỉ door button tương ứng mới hoàn thành session.
5. Multi-locker: để Locker #1 đang open, scan card khác để backend cấp #2; Servo #2 phải mở trong khi #1 vẫn không đổi. Sau đó door close #1 chỉ lock #1 và door close #2 chỉ lock #2.
6. Scan card đã giữ locker: LCD `Authorized` và servo đúng locker mở.
7. Unknown card: LCD `Access Denied` / `Try Again`; không servo nào di chuyển.
8. Nhấn RELEASE ở IDLE: log ignored. Nhấn trong active session, rồi door open/close: backend release như flow cũ và LCD `Locker Released`.
9. Thay đổi DHT22 và điều khiển fan để kiểm tra không regression.

Wokwi pushbutton là momentary: Ctrl-click để giữ trạng thái door closed hoặc dùng phím `1`–`3`; `R` là Release.

# Kịch bản: trả locker

Trong phiên member, thao tác nút release hợp lệ khiến ESP32 publish cùng topic request với payload `operation: "release"`, `card_id` và `locker_number`. Backend kiểm tra operation và kiểu/số locker, rồi gọi `LockerService.release_locker()`.

Service yêu cầu member tồn tại, locker tồn tại/đang dùng, đúng số và đúng `card_id`; sau đó cập nhật locker thành `vacant`. Response thành công có `action: "release"`. ESP32 nhận response, kết thúc phiên và vào cooldown. Cấu hình hiện tại đặt `RELEASE_BUTTON_PIN = -1`, nên nhánh nút vật lý bị vô hiệu cho đến khi gán GPIO thật.

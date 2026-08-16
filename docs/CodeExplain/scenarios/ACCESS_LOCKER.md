# Kịch bản: truy cập locker đang giữ

Backend tìm locker theo card và trả `action=access` mà không ghi ownership mới. Servo tương ứng unlock 90° và giữ góc; firmware chờ door CLOSED → OPEN → CLOSED rồi lock 0°.

Nếu người dùng không nhấn RELEASE, ESP32 không publish release và Firebase vẫn occupied. Đây là khác biệt giữa access vật lý và trả ownership.

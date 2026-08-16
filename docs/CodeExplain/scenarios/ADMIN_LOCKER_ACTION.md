# Kịch bản: quản trị locker

Admin UI gọi REST có bearer token để force-assign, force-release hoặc đổi trạng thái locker. Route xác thực admin, gọi phương thức quản trị của `LockerService`, repository cập nhật Firebase và backend broadcast event để các dashboard refresh.

Luồng này không đi qua MQTT và không tự kích relay ESP32. Nó thay đổi trạng thái/quyền sở hữu logic trong database; muốn mở phần cứng cần một protocol/lệnh MQTT riêng, hiện source chưa cung cấp.

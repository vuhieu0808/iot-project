# Kịch bản: trả locker

1. Card scan nhận `access` và servo unlock.
2. Người dùng nhấn RELEASE trước khi physical session kết thúc; firmware chỉ đặt `releasePending=true`.
3. Door button released biểu diễn open; pressed lại biểu diễn closed.
4. Firmware khóa servo về 0° rồi mới publish `operation=release` cùng card/số locker.
5. Backend xác minh member, ownership, số locker và status occupied; sau đó ghi vacant.
6. ESP32 nhận `action=release`, clear session và không di chuyển servo lần nữa.

Nhờ thứ tự này, backend không thể cấp lại locker khi cửa cũ vẫn đang mở.

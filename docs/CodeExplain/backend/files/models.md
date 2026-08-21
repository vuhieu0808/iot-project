# Backend model files

`backend/app/models/` định nghĩa schema Pydantic và enum dùng xuyên route, service, MQTT handler và repository.

- `member.py`: hồ sơ/hạn thành viên, mật khẩu hash và trạng thái active.
- `locker.py`: locker `vacant`, `occupied`, `broken`, card giữ và thời điểm cấp; `LockerLog`, `LockerAction`, `LockerLogStatus` quản lý nhật ký mượn/trả/mở tủ/admin can thiệp.
- `check_log.py`: action check-in/check-out và status granted/denied.
- `environment.py`: nhiệt độ, độ ẩm, trạng thái quạt.

Model là ranh giới validate input và serialize output; enum cũng quyết định giá trị lưu Firebase/gửi frontend.

# Kịch bản: truy cập locker đang giữ

Card được đọc và chuẩn hóa UID, rồi `LockerController::handleCardScan()` gửi `operation: "scan"`. `_handle_locker_request()` gọi `LockerService.process_locker_scan()`; khi `get_locker_by_card()` tìm thấy locker, service trả `action: "access"`, số locker hiện tại và không đổi bản ghi Firebase.

Response đi qua `gymtag/locker/response`; `LockerController::handleMqttPayload()` xác thực response/card, kích relay trong `RELAY_PULSE_MS` và mở phiên member. Đây là mở vật lý tạm thời, không phải giải phóng quyền sở hữu locker.

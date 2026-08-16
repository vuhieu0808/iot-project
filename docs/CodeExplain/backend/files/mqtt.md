# Các file MQTT của backend

## `backend/app/mqtt/topics.py`

`Topics` là nguồn tên topic tập trung, tránh chuỗi khác nhau giữa client và handler.

## `backend/app/mqtt/client.py`

`MQTTClient` bọc Paho:

- `connect()` cấu hình credentials, kết nối và chạy `loop_start()`.
- `_on_connect()` subscribe bốn request/telemetry topic.
- `_on_message()` decode UTF-8 rồi dùng `asyncio.run_coroutine_threadsafe()` chuyển việc sang event loop.
- `publish()` serialize/gửi payload do caller cung cấp.
- `disconnect()` dừng loop và ngắt kết nối.

## `backend/app/mqtt/handlers.py`

`MQTTMessageHandler` nhận các service và `publish_func` qua constructor. `handle_message()` parse một lần rồi định tuyến theo topic chính xác. Handler chuyên biệt gọi service, publish phản hồi thiết bị và broadcast WebSocket.

## Dữ liệu vào/ra

Input: topic và chuỗi JSON UTF-8. Output: chuỗi JSON qua MQTT và dictionary qua WebSocket.

## Xử lý lỗi

Payload sai/thiếu được log. Operation locker không hỗ trợ nhận phản hồi denied. Giá trị môi trường được kiểm tra chuyển đổi float.

## Cách giải thích khi bảo vệ

“Paho callback chạy ở thread nền, còn service là async. Client dùng `run_coroutine_threadsafe` để đưa coroutine vào đúng loop thay vì chạy logic database trong MQTT thread.”

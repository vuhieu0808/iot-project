# Luồng MQTT của backend

## Khởi tạo

`main.lifespan()` tạo `MQTTClient` và `MQTTMessageHandler`, truyền các service cùng hàm publish, rồi gọi `set_async_handler()` và `connect()`.

## Thread và asyncio

```mermaid
sequenceDiagram
    participant Paho as Thread Paho
    participant Client as MQTTClient
    participant Loop as Asyncio loop
    participant Handler as MQTTMessageHandler
    Paho->>Client: _on_message(topic, bytes)
    Client->>Loop: run_coroutine_threadsafe
    Loop->>Handler: handle_message(topic, text)
```

Nhờ chuyển coroutine sang loop FastAPI, callback Paho không tự chạy database/WebSocket async trong thread nền.

## Subscription và định tuyến

Khi kết nối thành công, client subscribe các topic check-in, check-out, locker request và environment reading. `handle_message()` parse JSON một lần rồi định tuyến:

- Cửa → `AccessService` → log, response MQTT và event occupancy.
- Locker → `_handle_locker_request()` → assign/access hoặc release.
- Môi trường → `EnvironmentService` → lưu reading, có thể publish lệnh quạt và broadcast.

## Luồng phản hồi locker

Handler mặc định operation thiếu là `scan`. Release yêu cầu `locker_number` là số nguyên dương và không chấp nhận boolean. Kết quả service được serialize lên `gymtag/locker/response`, đồng thời backend phát danh sách locker chi tiết cho admin và danh sách ẩn thông tin cho public.

## Đặc điểm delivery

QoS 0 và message không retained, vì vậy không bảo đảm giao lại. ESP32 dùng timeout/cooldown để xử lý response mất; protocol hiện chưa có correlation ID ngoài `card_id` và state cục bộ.

Xem [giao thức MQTT](../02_MQTT_PROTOCOL.md) và [file MQTT](files/mqtt.md).

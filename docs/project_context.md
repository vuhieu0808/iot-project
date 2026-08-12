# GymTag - Hệ thống quản lý phòng gym thông minh bằng RFID

## Thông tin chung

- Đồ án môn học: Vật lý cho Công nghệ thông tin
- Trường: Đại học Khoa học Tự nhiên, ĐHQG TP. Hồ Chí Minh, Khoa Công nghệ thông tin
- Nhóm 6: Vũ Trần Minh Hiếu (24127003), Hoàng Đức Thịnh (24127240), Trần Viết Bảo (24127270)

## Mục đích

Xây dựng một mô hình phòng gym thông minh ứng dụng công nghệ IoT và RFID để
giải quyết các hạn chế của quản lý thủ công: khó kiểm soát lượt ra vào,
mất thời gian quản lý tủ khóa (locker), không theo dõi được điều kiện môi
trường phòng tập theo thời gian thực.

Hệ thống dùng thẻ RFID để nhận diện thành viên tại cửa ra vào và khu vực
locker, kết hợp cảm biến môi trường và dashboard web để giám sát và cảnh
báo tự động.

## Phạm vi hiện tại của đồ án

Đồ án tập trung vào việc dựng mô hình phần cứng mô phỏng (không phải hệ
thống thương mại hoàn chỉnh), gồm 1 ESP32 trung tâm giao tiếp qua MQTT với
một backend xử lý logic và lưu trữ dữ liệu, hiển thị qua dashboard web.

## Chức năng chính

Các chức năng liên quan trực tiếp đến kiểm soát ra vào và tài sản (locker),
đây là phần cốt lõi bắt buộc phải có:

1. Check-in tại cửa ra vào: quẹt thẻ RFID, hệ thống xác nhận thành viên,
   mở cửa (servo), hiển thị lời chào kèm tên trên LCD, ghi nhận giờ vào.
2. Check-out tại cửa ra vào: quẹt lại thẻ khi ra về, mở cửa, ghi nhận giờ
   ra và tính thời gian tập luyện.
3. Kiểm tra hạn thành viên khi quẹt thẻ: đối chiếu ngày hết hạn trong cơ sở
   dữ liệu, cho vào nếu còn hạn, từ chối kèm cảnh báo (LED đỏ, buzzer) nếu
   hết hạn.
4. Quẹt thẻ lấy locker: tìm locker trống đầu tiên, gán cho thẻ, mở khóa
   locker đó.
5. Quẹt thẻ trả locker: xác nhận đúng chủ sở hữu, mở khóa để lấy đồ, cập
   nhật locker về trạng thái trống.

## Chức năng phụ

Các chức năng hỗ trợ giám sát và trải nghiệm, không phải yêu cầu bắt buộc
để hệ thống vận hành cơ bản nhưng làm rõ giá trị ứng dụng IoT của đề tài:

6. Xem sơ đồ locker trống/đầy trên dashboard web theo thời gian thực.
7. Giám sát nhiệt độ, độ ẩm phòng gym bằng cảm biến DHT22, hiển thị realtime
   trên dashboard.
8. Cảnh báo môi trường bất thường: khi nhiệt độ hoặc độ ẩm vượt ngưỡng cấu
   hình (mặc định 32 độ C, 80% độ ẩm), tự động bật quạt qua relay và gửi
   cảnh báo qua Telegram hoặc email.
9. Đếm số người đang có mặt trong phòng gym theo thời gian thực (chênh
   lệch giữa số lượt check-in và check-out), hiển thị trên dashboard.

## Kiến trúc hệ thống

```
Phần cứng (ESP32 + cảm biến/thiết bị)
        MQTT (publish/subscribe)
Backend xử lý logic và lưu trữ
        REST API / WebSocket
Dashboard web hiển thị realtime
```

Ban đầu proposal đề xuất dùng Node-RED làm lớp xử lý trung gian và dashboard
có sẵn. Quyết định hiện tại là thay Node-RED bằng backend viết tay bằng
Python (FastAPI, paho-mqtt), lý do: dễ kiểm soát logic nghiệp vụ phức tạp
(tính thời gian tập, kiểm tra hạn, gán locker), dễ tách lớp rõ ràng để nộp
báo cáo, và nhóm quen thuộc với Python hơn.

## Danh sách thiết bị phần cứng

| Thiết bị | Số lượng | Chức năng |
|---|---|---|
| ESP32 DevKit V1 | 1 | Bộ xử lý trung tâm, kết nối WiFi/MQTT |
| Cảm biến DHT22 | 1 | Đo nhiệt độ, độ ẩm phòng gym |
| Màn hình LCD I2C 16x2 | 2 | Hiển thị thông tin cho người dùng |
| LED đơn (xanh/đỏ) | 1 túi | Hiển thị trạng thái cho phép/từ chối |
| Breadboard, dây cắm | 1 bộ | Dụng cụ lắp mạch |
| Nguồn 12V | 1 | Cấp nguồn cho ESP32 và module |
| Thẻ RFID | 5 | Thẻ nhận diện thành viên |
| MFRC522 RFID Reader | 5 | Đầu đọc thẻ RFID (cửa chính, locker) |
| Servo SG90 | 5 | Khóa cửa, khóa locker |
| Relay Module | 1 | Bật quạt tự động |
| Quạt mini | 1 | Thiết bị làm mát mô phỏng |

## Mô phỏng và phát triển

- Phần firmware ESP32 được viết bằng Arduino framework, có thể mô phỏng
  trên Wokwi (wokwi.com) trước khi lắp phần cứng thật, dùng để test logic
  đọc RFID, điều khiển servo, đọc DHT22, điều khiển relay mà không cần chờ
  linh kiện.
- Do giới hạn mô phỏng RFID-RC522 trên Wokwi (chỉ mô phỏng được 1 UID cấu
  hình sẵn cho mỗi module ảo, không có UI Node-RED bên trong), bản mô phỏng
  ban đầu gộp phần "cửa chính" làm trọng tâm demo, phần locker và tích hợp
  MQTT/Telegram/Firebase thật sẽ được bổ sung dần.
- Backend Python được tổ chức theo từng lớp trách nhiệm rõ ràng: models,
  repositories (Firebase Realtime Database), services (logic nghiệp vụ), mqtt
  (client và handler), api (REST và WebSocket cho dashboard).

## Chuẩn đặt tên topic MQTT

```
gymtag/door/checkin_request      ESP32 gửi lên backend khi quẹt thẻ ở cửa
gymtag/door/checkin_response     backend gửi xuống ESP32, kết quả cho vào hay không
gymtag/locker/request            ESP32 gửi lên backend khi quẹt thẻ ở locker
gymtag/locker/response           backend gửi xuống ESP32, số locker được gán hoặc lệnh mở khóa trả
gymtag/environment/reading       ESP32 gửi lên backend, dữ liệu nhiệt độ/độ ẩm
gymtag/environment/fan_control   backend gửi xuống ESP32, lệnh bật/tắt quạt
```

## Dữ liệu cần lưu trữ

- Thành viên: UID thẻ, tên, ngày hết hạn membership.
- Locker: số locker, trạng thái (trống/đang dùng), UID đang giữ nếu có.
- Lịch sử ra vào: UID, thời điểm check-in, thời điểm check-out, thời gian
  tập luyện.
- Dữ liệu môi trường: thời điểm đo, nhiệt độ, độ ẩm, trạng thái quạt.

## Trạng thái hiện tại

- Đã có báo cáo đồ án (PDF/PPTX) mô tả đầy đủ chức năng, thiết bị, bản vẽ
  phác thảo, kế hoạch thực hiện theo tuần.
- [Proposal](../24127003_24127240_24127270.pdf)
- Đã có bản mô phỏng Wokwi cho phần firmware ESP32 (check-in/out cửa
  chính, kiểm tra hạn, LCD, servo, DHT22, relay quạt).
- Đã có prompt chi tiết để sinh backend Python (chưa triển khai code thật).
- Dashboard web, kết nối Firebase, và Telegram Bot chưa được triển khai,
  hiện đang ở bước lên kế hoạch.

## Lưu ý khi làm việc tiếp trên project này

- Không dùng Node-RED, thay bằng backend Python tự viết.
- Giữ nguyên tắc tách lớp rõ ràng giữa firmware (ESP32), lớp truyền dẫn
  (MQTT), lớp xử lý logic (backend Python), và lớp hiển thị (dashboard).
- Ưu tiên hoàn thiện chức năng chính (check-in/out, kiểm tra hạn, locker)
  trước, sau đó mới đến chức năng phụ (môi trường, cảnh báo, đếm người).
- Thời hạn hoàn thành đang được rút ngắn xuống còn khoảng 1 tuần, nên các
  quyết định kỹ thuật nên ưu tiên đơn giản, dễ demo và dễ giải thích trong
  báo cáo hơn là tối ưu hoặc mở rộng quá mức cần thiết.
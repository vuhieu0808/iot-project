# Kịch bản: check-in / check-out cửa ra vào

ESP32 hiện tại tập trung vào locker/môi trường/quạt và không triển khai đầu đọc cửa, nhưng backend đã có protocol cửa. Thiết bị cửa publish card ID lên `gymtag/door/checkin_request` hoặc `gymtag/door/checkout_request`. Handler gọi `AccessService`, ghi `check_logs/{uuid}`, trả kết quả trên response topic tương ứng và broadcast WebSocket.

Occupancy được repository suy ra từ sự kiện `granted` mới nhất của từng card: latest `checkin` được tính là đang ở phòng, latest `checkout` thì không.

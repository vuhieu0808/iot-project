# State machine locker dùng servo

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> WAITING_BACKEND: scan RFID
    WAITING_BACKEND --> WAIT_DOOR_OPEN: assign/access, servo unlock
    WAITING_BACKEND --> COOLDOWN: denied/lỗi/timeout
    WAIT_DOOR_OPEN --> WAIT_DOOR_CLOSE: door closed → open
    WAIT_DOOR_OPEN --> COOLDOWN: timeout khi door vẫn closed
    WAIT_DOOR_CLOSE --> COOLDOWN: door close, không release
    WAIT_DOOR_CLOSE --> WAITING_RELEASE_RESPONSE: door close, releasePending
    WAITING_RELEASE_RESPONSE --> COOLDOWN: response/timeout
    COOLDOWN --> IDLE: 5 giây
```

## `IDLE`

Cho phép scan mới. RELEASE bị ignore.

## `WAITING_BACKEND`

Chờ assign/access. Response hợp lệ phải có locker #1–#4; servo tương ứng chuyển 90°.

## `WAIT_DOOR_OPEN`

Ghi nhận door closed ban đầu rồi bắt buộc chờ released/HIGH. Điều này ngăn servo khóa ngay khi button vẫn pressed lúc vừa unlock.

## `WAIT_DOOR_CLOSE`

Chờ pressed/LOW. Khi closed, servo chuyển 0°. Nếu không release pending thì kết thúc physical session ngay; nếu có thì mới publish release.

## `WAITING_RELEASE_RESPONSE`

Servo đã locked. Response `release` chỉ xác nhận backend/Firebase đã chuyển locker vacant; không unlock lại.

## `COOLDOWN`

Chặn scan 5 giây rồi về `IDLE`.

Door timeout 30 giây chỉ là fail-safe. Door đang open không bị force-lock.

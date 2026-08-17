# Kịch bản: cấp locker

```text
RFID Card A
→ ESP32 publish scan
→ LockerService chọn locker vacant nhỏ nhất
→ Firebase ghi occupied
→ response action=assign
→ servo locker chuyển 0° → 90°
→ user release door button (open)
→ user press door button (close)
→ servo chuyển 90° → 0°
→ session kết thúc; Firebase vẫn occupied
```

Backend demo cần chỉ có Locker #1–#4 assignable để mọi response đều có servo mapping.

# Các file repository của backend

## `backend/app/repositories/firebase_repo.py`

`FirebaseRepository` là implementation duy nhất cho tầng lưu trữ, chịu trách nhiệm chuyển đổi model Pydantic thành dictionary Firebase và ngược lại, tạo UUID/timestamp khi cần, sắp xếp lịch sử và suy ra occupancy.

Điểm chính:

- `_ref(path)`: lấy Firebase database reference.
- `_extract_items(data)`: chuẩn hóa node dạng dictionary/list.
- `initialize()`: khởi tạo Firebase Admin và bổ sung locker mặc định còn thiếu.
- Các lệnh SDK đồng bộ được chạy bằng `asyncio.to_thread()`.

## Dữ liệu vào/ra

Input gồm model đã định kiểu, ID và limit. Output là model/list Pydantic hoặc `None`/bool/dict. Tác dụng phụ là đọc/ghi Firebase.

## Bản triển khai test

`backend/tests/in_memory_repo.py` có `InMemoryRepository`, implement cùng interface để unit test service mà không cần Firebase.

## Cách giải thích khi bảo vệ

"FirebaseRepository là tầng lưu trữ duy nhất. Unit test dùng InMemoryRepository không cần mạng. Lệnh Firebase đồng bộ được bọc bằng `asyncio.to_thread` để không chặn server loop."

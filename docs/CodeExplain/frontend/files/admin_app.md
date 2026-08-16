# `frontend/admin/app.js`

Đây là controller giao diện quản trị. `setupAuth()` và `initAdmin()` khởi động phiên; `setupTabs()` điều hướng các màn hình; `setupWebSocket()` nghe cập nhật realtime.

Nhóm hàm quan trọng:

- Tổng quan: `loadOverviewData()`, `renderOverviewEnvironment()`, `getLockerStats()`, `renderOverviewLockers()`, `renderOverviewLogs()` và `renderOverviewLogsPage()`.
- Thành viên: `loadMembersData()`, `renderMembersTable()`, `setupModal()`.
- Locker: `loadLockersData()`, `renderAdminLockers()`, `setupLockerModal()`, `openLockerModal()`.
- Log/môi trường: `loadLogsData()`, `renderAdminLogs()`, `loadEnvironmentHistoryData()`, `renderEnvironmentHistory()`.
- Quạt/ngưỡng: `setupFanControl()`, `updateAdminFanUI()`, `loadThresholds()`, `setupThresholdControls()`.

Input là response JSON, WebSocket event và thao tác DOM; output là REST request hoặc DOM mới. Mỗi trang overview tối đa 6 log hôm nay; trang hiện tại được co về phạm vi hợp lệ khi dữ liệu đổi.

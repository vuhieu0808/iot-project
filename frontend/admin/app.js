/**
 * GymTag Admin Panel App Controller (With Backend JWT Auth)
 */

import { GymTagAPI } from "../shared/js/api.js?v=5.3";
import { wsClient } from "../shared/js/websocket.js?v=5.3";
import {
	formatTime,
	formatDate,
	formatDuration,
	escapeHtml,
	showToast,
} from "../shared/js/utils.js?v=5.3";

let isEditMode = false;
let cachedMembers = [];
let selectedLocker = null;
let selectedAssignCardId = null;
const OVERVIEW_LOGS_PER_PAGE = 6;
let overviewTodayLogs = [];
let overviewLogsCurrentPage = 1;

document.addEventListener("DOMContentLoaded", () => {
	setupAuth();
});

function setupAuth() {
	const loginOverlay = document.getElementById("admin-login-overlay");
	const loginForm = document.getElementById("admin-login-form");
	const usernameInput = document.getElementById("admin-username-input");
	const passkeyInput = document.getElementById("admin-passkey-input");
	const errorMsg = document.getElementById("login-error-msg");
	const btnLogout = document.getElementById("btn-admin-logout");

	const token = sessionStorage.getItem("gymtag_admin_token");

	if (token) {
		loginOverlay.classList.remove("active");
		initAdmin();
	} else {
		loginOverlay.classList.add("active");
	}

	// Handle Login submission
	loginForm.addEventListener("submit", async (e) => {
		e.preventDefault();
		const username = usernameInput ? usernameInput.value.trim() : "admin";
		const password = passkeyInput.value.trim();

		try {
			const res = await GymTagAPI.adminLogin(username, password);
			sessionStorage.setItem("gymtag_admin_token", res.token);
			loginOverlay.classList.remove("active");
			errorMsg.style.display = "none";
			passkeyInput.value = "";
			showToast("Đăng nhập Quản trị Admin thành công!", "success");
			initAdmin();
		} catch (err) {
			errorMsg.style.display = "block";
			passkeyInput.select();
		}
	});

	// Handle Logout
	if (btnLogout) {
		btnLogout.addEventListener("click", () => {
			sessionStorage.removeItem("gymtag_admin_token");
			wsClient.disconnect();
			loginOverlay.classList.add("active");
			showToast("Đã đăng xuất tài khoản Admin", "success");
		});
	}
}

async function initAdmin() {
	setupTabs();
	setupModal();
	setupLockerModal();
	setupFanControl();
	setupThresholdControls();
	setupOverviewPagination();
	setupWebSocket();
	await loadOverviewData();
}

/* ----------------------------------------------------
 * Tab Routing Navigation
 * ---------------------------------------------------- */
function setupTabs() {
	const navButtons = document.querySelectorAll(".sidebar-nav .nav-item");
	const tabPanes = document.querySelectorAll(".tab-pane");
	const pageTitle = document.getElementById("page-title");

	const titles = {
		overview: "Tổng Quan Hệ Thống",
		members: "Quản Lý Thành Viên",
		lockers: "Quản Lý Locker",
		logs: "Lịch Sử Ra Vào",
		environment: "Lịch Sử Môi Trường",
	};

	navButtons.forEach((btn) => {
		btn.addEventListener("click", () => {
			const tabName = btn.getAttribute("data-tab");

			navButtons.forEach((b) => b.classList.remove("active"));
			tabPanes.forEach((p) => p.classList.remove("active"));

			btn.classList.add("active");
			document.getElementById(`tab-${tabName}`).classList.add("active");
			pageTitle.textContent = titles[tabName] || "Admin Control";

			// Load specific tab data
			switch (tabName) {
				case "overview":
					loadOverviewData();
					break;
				case "members":
					loadMembersData();
					break;
				case "lockers":
					loadLockersData();
					loadLockerLogsData();
					break;
				case "logs":
					loadLogsData();
					break;
				case "environment":
					loadEnvironmentHistoryData();
					loadThresholds();
					break;
			}
		});
	});

	// Filter logs handlers
	document.getElementById("btn-filter-logs").addEventListener("click", () => {
		loadLogsData();
	});

	// Filter locker logs handlers
	document.getElementById("btn-filter-locker-logs")?.addEventListener("click", () => {
		loadLockerLogsData();
	});

	document.getElementById("btn-refresh-locker-logs")?.addEventListener("click", () => {
		loadLockerLogsData();
	});

	document.getElementById("filter-locker-number")?.addEventListener("change", () => {
		loadLockerLogsData();
	});

	document.getElementById("filter-locker-card-id")?.addEventListener("keydown", (e) => {
		if (e.key === "Enter") {
			e.preventDefault();
			loadLockerLogsData();
		}
	});

	document.getElementById("btn-refresh-env").addEventListener("click", () => {
		loadEnvironmentHistoryData();
		loadThresholds();
	});
}

/* ----------------------------------------------------
 * WebSocket Connection & Events
 * ---------------------------------------------------- */
function setupWebSocket() {
	const indicatorEl = document.getElementById("ws-indicator");
	const statusTextEl = document.getElementById("ws-status-text");

	wsClient.onStatusChange((status) => {
		indicatorEl.className = "ws-indicator";
		if (status === "connected") {
			indicatorEl.classList.add("connected");
			statusTextEl.textContent = "Realtime Live";
		} else if (status === "connecting") {
			statusTextEl.textContent = "Đang kết nối...";
		} else {
			indicatorEl.classList.add("disconnected");
			statusTextEl.textContent = "Mất kết nối";
		}
	});

	wsClient.on("checkin_event", () => {
		loadOverviewData();
		if (document.getElementById("tab-logs").classList.contains("active")) {
			loadLogsData();
		}
	});

	wsClient.on("checkout_event", () => {
		loadOverviewData();
		if (document.getElementById("tab-logs").classList.contains("active")) {
			loadLogsData();
		}
	});

	wsClient.on("locker_event", (data) => {
		if (data.lockers) {
			renderOverviewLockers(data.lockers);
			renderAdminLockers(data.lockers);
		} else {
			loadLockersData();
		}
		if (document.getElementById("tab-lockers")?.classList.contains("active")) {
			if (data.recent_logs) {
				renderAdminLockerLogs(data.recent_logs);
			} else {
				loadLockerLogsData();
			}
		}
	});

	wsClient.on("environment_update", (data) => {
		renderOverviewEnvironment(data);
		handleRealtimeEnvironmentUpdate(data);
	});

	wsClient.on("threshold_update", (data) => {
		if (data.temp_threshold !== undefined) {
			const tempInput = document.getElementById("threshold-temp");
			if (tempInput) tempInput.value = data.temp_threshold;
		}
		if (data.humidity_threshold !== undefined) {
			const humInput = document.getElementById("threshold-humidity");
			if (humInput) humInput.value = data.humidity_threshold;
		}
		showToast("Ngưỡng nhiệt độ & độ ẩm vừa được cập nhật!", "info");
	});

	const token = sessionStorage.getItem("gymtag_admin_token");
	if (token) {
		wsClient.connect(`/ws/admin?token=${encodeURIComponent(token)}`);
	}
}

/* ----------------------------------------------------
 * TAB 1: OVERVIEW DATA
 * ---------------------------------------------------- */
async function loadOverviewData() {
	try {
		const [statusData, lockers, logs] = await Promise.all([
			GymTagAPI.getPublicStatus().catch(() => null),
			GymTagAPI.getAdminLockers().catch(() => []),
			GymTagAPI.getAdminActivityLogs(500).catch(() => []),
		]);

		if (statusData) {
			document.getElementById("overview-occupancy").textContent =
				statusData.current_occupancy;
			renderOverviewEnvironment({
				temperature: statusData.temperature,
				humidity: statusData.humidity,
				fan_on: statusData.fan_on,
			});
		}

		renderOverviewLockers(lockers);
		renderOverviewLogs(logs);
	} catch (e) {
		console.error("Error loading overview data:", e);
	}
}

function renderOverviewEnvironment(data) {
	const temperatureEl = document.getElementById("overview-temperature");
	const humidityEl = document.getElementById("overview-humidity");
	if (!data) return;

	const tempStr =
		data.temperature !== null && data.temperature !== undefined
			? `${data.temperature.toFixed(1)}°C`
			: "--°C";
	const humStr =
		data.humidity !== null && data.humidity !== undefined
			? `${data.humidity.toFixed(1)}%`
			: "--%";

	temperatureEl.textContent = tempStr;
	humidityEl.textContent = humStr;
	updateAdminFanUI(data.fan_on);
}

function getLockerStats(lockers) {
	return lockers.reduce(
		(stats, locker) => {
			const status =
				locker.status || (locker.is_occupied ? "occupied" : "vacant");
			if (status === "broken") stats.broken += 1;
			else if (status === "occupied" || locker.is_occupied)
				stats.occupied += 1;
			else stats.vacant += 1;
			stats.total += 1;
			return stats;
		},
		{ vacant: 0, occupied: 0, broken: 0, total: 0 },
	);
}

function renderOverviewLockers(lockers) {
	if (!lockers) return;

	const stats = getLockerStats(lockers);
	document.getElementById("overview-locker-vacant").textContent =
		stats.vacant;
	document.getElementById("overview-locker-occupied").textContent =
		stats.occupied;
	document.getElementById("overview-locker-broken").textContent =
		stats.broken;
	document.getElementById("overview-locker-summary").textContent =
		`${stats.vacant} / ${stats.total} tủ trống`;
}

function renderOverviewLogs(logs) {
	const tbody = document.getElementById("overview-logs-tbody");
	if (!tbody || !logs) return;

	const now = new Date();
	overviewTodayLogs = logs
		.filter((log) => {
			const timestamp = new Date(log.timestamp);
			return (
				!Number.isNaN(timestamp.getTime()) &&
				timestamp.getFullYear() === now.getFullYear() &&
				timestamp.getMonth() === now.getMonth() &&
				timestamp.getDate() === now.getDate()
			);
		})
		.sort(
			(a, b) =>
				new Date(b.timestamp).getTime() -
				new Date(a.timestamp).getTime(),
		);

	const totalPages = Math.max(
		1,
		Math.ceil(overviewTodayLogs.length / OVERVIEW_LOGS_PER_PAGE),
	);
	overviewLogsCurrentPage = Math.min(
		Math.max(overviewLogsCurrentPage, 1),
		totalPages,
	);
	renderOverviewLogsPage();
}

function renderOverviewLogsPage() {
	const tbody = document.getElementById("overview-logs-tbody");
	const summary = document.getElementById("overview-logs-summary");
	const pagination = document.getElementById("overview-logs-pagination");
	if (!tbody || !summary || !pagination) return;

	summary.textContent = `${overviewTodayLogs.length} lượt hôm nay`;
	if (overviewTodayLogs.length === 0) {
		tbody.innerHTML =
			'<tr><td colspan="5" class="overview-empty-state">Hôm nay chưa có lượt quẹt thẻ nào.</td></tr>';
		pagination.innerHTML = "";
		return;
	}

	const totalPages = Math.ceil(
		overviewTodayLogs.length / OVERVIEW_LOGS_PER_PAGE,
	);
	overviewLogsCurrentPage = Math.min(
		Math.max(overviewLogsCurrentPage, 1),
		totalPages,
	);
	const start = (overviewLogsCurrentPage - 1) * OVERVIEW_LOGS_PER_PAGE;
	const pageLogs = overviewTodayLogs.slice(
		start,
		start + OVERVIEW_LOGS_PER_PAGE,
	);

	tbody.innerHTML = pageLogs
		.map(
			(log) => `
    <tr>
      <td>${formatTime(log.timestamp)}</td>
      <td><code>${escapeHtml(log.card_id || "--")}</code></td>
      <td>${escapeHtml(log.member_name || "--")}</td>
      <td><span class="badge badge-info">${escapeHtml((log.action || "--").toUpperCase())}</span></td>
      <td><span class="badge ${log.status === "granted" ? "badge-granted" : "badge-denied"}">${escapeHtml((log.status || "--").toUpperCase())}</span></td>
    </tr>
  `,
		)
		.join("");

	const pageButtons = Array.from({ length: totalPages }, (_, index) => {
		const page = index + 1;
		return `<button type="button" class="pagination-btn ${page === overviewLogsCurrentPage ? "active" : ""}" data-page="${page}" aria-label="Trang ${page}" ${page === overviewLogsCurrentPage ? 'aria-current="page"' : ""}>${page}</button>`;
	}).join("");

	pagination.innerHTML = `
    <button type="button" class="pagination-btn pagination-nav" data-page="${overviewLogsCurrentPage - 1}" ${overviewLogsCurrentPage === 1 ? "disabled" : ""}>Previous</button>
    <div class="pagination-pages">${pageButtons}</div>
    <button type="button" class="pagination-btn pagination-nav" data-page="${overviewLogsCurrentPage + 1}" ${overviewLogsCurrentPage === totalPages ? "disabled" : ""}>Next</button>
  `;
}

function setupOverviewPagination() {
	const pagination = document.getElementById("overview-logs-pagination");
	if (!pagination || pagination.dataset.initialized === "true") return;
	pagination.dataset.initialized = "true";
	pagination.addEventListener("click", (event) => {
		const button = event.target.closest("button[data-page]");
		if (!button || button.disabled) return;
		overviewLogsCurrentPage = Number(button.dataset.page);
		renderOverviewLogsPage();
	});
}

/* ----------------------------------------------------
 * TAB 2: MEMBERS MANAGEMENT & CRUD
 * ---------------------------------------------------- */
async function loadMembersData() {
	try {
		const members = await GymTagAPI.getAdminMembers();
		renderMembersTable(members);
	} catch (e) {
		showToast("Lỗi khi tải danh sách thành viên", "error");
	}
}

function renderMembersTable(members) {
	const tbody = document.getElementById("members-tbody");
	if (!tbody) return;

	if (members.length === 0) {
		tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">Chưa có thành viên nào. Hãy bấm "Thêm Thành Viên Mới".</td></tr>`;
		return;
	}

	tbody.innerHTML = members
		.map((m) => {
			const isExpired = new Date(m.membership_expiry) < new Date();
			let statusBadge = "";
			if (!m.is_active) {
				statusBadge = `<span class="badge badge-warning">🔒 Đã khóa</span>`;
			} else if (isExpired) {
				statusBadge = `<span class="badge badge-denied">Hết hạn</span>`;
			} else {
				statusBadge = `<span class="badge badge-granted">Hoạt động</span>`;
			}

			const activeToggleBtn = m.is_active
				? `<button class="btn btn-secondary btn-sm toggle-active-btn" data-card="${escapeHtml(m.card_id)}" data-active="false" title="Khóa tài khoản">🔒 Khóa</button>`
				: `<button class="btn btn-primary btn-sm toggle-active-btn" data-card="${escapeHtml(m.card_id)}" data-active="true" title="Mở khóa tài khoản">🔓 Mở khóa</button>`;

			return `
      <tr>
        <td><code>${escapeHtml(m.card_id)}</code></td>
        <td><strong>${escapeHtml(m.name)}</strong></td>
        <td>${escapeHtml(m.email || "-")}</td>
        <td>${escapeHtml(m.phone || "-")}</td>
        <td>${formatDate(m.membership_expiry)}</td>
        <td>${statusBadge}</td>
        <td>
          ${activeToggleBtn}
          <button class="btn btn-secondary btn-sm edit-member-btn" data-card="${escapeHtml(m.card_id)}">✏️ Sửa</button>
          <button class="btn btn-secondary btn-sm reset-pw-btn" data-card="${escapeHtml(m.card_id)}" title="Reset mật khẩu về 123456">🔑 Reset MK</button>
          <button class="btn btn-danger btn-sm delete-member-btn" data-card="${escapeHtml(m.card_id)}">🗑️ Xoá</button>
        </td>
      </tr>
    `;
		})
		.join("");

	// Attach action listeners
	document.querySelectorAll(".toggle-active-btn").forEach((btn) => {
		btn.addEventListener("click", async () => {
			const cardId = btn.getAttribute("data-card");
			const targetActive = btn.getAttribute("data-active") === "true";
			try {
				await GymTagAPI.toggleAdminMemberActive(cardId, targetActive);
				showToast(
					targetActive
						? `Đã mở khóa tài khoản ${cardId}`
						: `Đã khóa tài khoản ${cardId}`,
					"success",
				);
				loadMembersData();
			} catch (err) {
				showToast(`Lỗi: ${err.message}`, "error");
			}
		});
	});

	document.querySelectorAll(".edit-member-btn").forEach((btn) => {
		btn.addEventListener("click", () => {
			const cardId = btn.getAttribute("data-card");
			openEditModal(cardId);
		});
	});

	document.querySelectorAll(".reset-pw-btn").forEach((btn) => {
		btn.addEventListener("click", async () => {
			const cardId = btn.getAttribute("data-card");
			if (
				confirm(
					`Bạn có muốn reset mật khẩu của thành viên '${cardId}' về mặc định: 123456 ?`,
				)
			) {
				try {
					await GymTagAPI.resetAdminMemberPassword(cardId);
					showToast(
						`Đã reset mật khẩu của ${cardId} về 123456`,
						"success",
					);
				} catch (err) {
					showToast(`Lỗi: ${err.message}`, "error");
				}
			}
		});
	});

	document.querySelectorAll(".delete-member-btn").forEach((btn) => {
		btn.addEventListener("click", () => {
			const cardId = btn.getAttribute("data-card");
			confirmDeleteMember(cardId);
		});
	});
}

function setupModal() {
	const modal = document.getElementById("member-modal");
	const btnAdd = document.getElementById("btn-add-member");
	const btnClose = document.getElementById("btn-close-modal");
	const btnCancel = document.getElementById("btn-cancel-modal");
	const form = document.getElementById("member-form");

	btnAdd.addEventListener("click", () => {
		isEditMode = false;
		document.getElementById("modal-title").textContent =
			"Thêm Thành Viên Mới";
		document.getElementById("m-card-id").readOnly = false;
		form.reset();
		document.getElementById("m-active").checked = true;
		modal.classList.add("active");
	});

	const closeModal = () => modal.classList.remove("active");
	btnClose.addEventListener("click", closeModal);
	btnCancel.addEventListener("click", closeModal);

	form.addEventListener("submit", async (e) => {
		e.preventDefault();
		const cardId = document.getElementById("m-card-id").value.trim();
		const name = document.getElementById("m-name").value.trim();
		const email = document.getElementById("m-email").value.trim();
		const phone = document.getElementById("m-phone").value.trim();
		const expiry = document.getElementById("m-expiry").value;
		const isActive = document.getElementById("m-active").checked;

		try {
			await GymTagAPI.saveAdminMember({
				card_id: cardId,
				name: name,
				email: email || null,
				phone: phone || null,
				membership_expiry: expiry,
				is_active: isActive,
			});

			showToast(
				isEditMode
					? "Cập nhật thành viên thành công!"
					: "Đã thêm thành viên mới!",
				"success",
			);
			closeModal();
			loadMembersData();
		} catch (err) {
			showToast(`Lỗi: ${err.message}`, "error");
		}
	});
}

function renderMemberOptions(filterText = "") {
	const listEl = document.getElementById("assign-member-list");
	if (!listEl) return;

	const term = filterText.toLowerCase();
	const filtered = cachedMembers.filter((m) => {
		const nameMatch = m.name ? m.name.toLowerCase().includes(term) : false;
		const cardMatch = m.card_id
			? m.card_id.toLowerCase().includes(term)
			: false;
		const phoneMatch = m.phone ? m.phone.includes(term) : false;
		return nameMatch || cardMatch || phoneMatch;
	});

	if (filtered.length === 0) {
		listEl.innerHTML = `<div class="dropdown-item-empty">Không tìm thấy thành viên phù hợp</div>`;
		return;
	}

	listEl.innerHTML = filtered
		.map((m) => {
			const isSelected = selectedAssignCardId === m.card_id;
			return `
      <div class="dropdown-item ${isSelected ? "selected" : ""}" data-card="${escapeHtml(m.card_id)}" data-name="${escapeHtml(m.name)}">
        <div class="item-title">
          <span>${escapeHtml(m.name)}</span>
          <span class="item-card-badge">${escapeHtml(m.card_id)}</span>
        </div>
        <div class="item-sub">
          ${m.phone ? "SĐT: " + escapeHtml(m.phone) + " • " : ""}Hạn: ${formatDate(m.membership_expiry)}
        </div>
      </div>
    `;
		})
		.join("");

	listEl.querySelectorAll(".dropdown-item").forEach((itemEl) => {
		itemEl.addEventListener("click", (e) => {
			e.stopPropagation();
			const cardId = itemEl.getAttribute("data-card");
			const memberName = itemEl.getAttribute("data-name");
			selectedAssignCardId = cardId;

			const searchInput = document.getElementById("assign-member-search");
			if (searchInput) {
				searchInput.value = `[${cardId}] ${memberName}`;
			}

			const wrapper = document.getElementById("assign-member-wrapper");
			if (wrapper) {
				wrapper.classList.remove("open");
			}
		});
	});
}

function setupLockerModal() {
	const modal = document.getElementById("locker-modal");
	const btnClose = document.getElementById("btn-close-locker-modal");
	const btnCancel = document.getElementById("btn-cancel-locker-modal");
	const btnForceRelease = document.getElementById("btn-force-release");
	const btnForceAssign = document.getElementById("btn-force-assign");
	const btnToggleBroken = document.getElementById("btn-toggle-broken");
	const wrapper = document.getElementById("assign-member-wrapper");
	const searchInput = document.getElementById("assign-member-search");

	const closeModal = () => {
		modal.classList.remove("active");
		if (wrapper) wrapper.classList.remove("open");
		selectedLocker = null;
		selectedAssignCardId = null;
	};

	btnClose.addEventListener("click", closeModal);
	btnCancel.addEventListener("click", closeModal);

	if (searchInput && wrapper) {
		const openDropdown = () => {
			wrapper.classList.add("open");
			if (searchInput.value.startsWith("[")) {
				searchInput.select();
				renderMemberOptions("");
			} else {
				renderMemberOptions(searchInput.value.trim());
			}
		};

		searchInput.addEventListener("click", openDropdown);
		searchInput.addEventListener("focus", openDropdown);

		searchInput.addEventListener("input", () => {
			selectedAssignCardId = null;
			wrapper.classList.add("open");
			renderMemberOptions(searchInput.value.trim());
		});
	}

	document.addEventListener("click", (e) => {
		if (wrapper && !wrapper.contains(e.target)) {
			wrapper.classList.remove("open");
		}
	});

	// Force Release
	btnForceRelease.addEventListener("click", async () => {
		if (!selectedLocker) return;
		try {
			await GymTagAPI.forceReleaseLocker(selectedLocker.locker_number);
			showToast(
				`Đã force giải phóng Locker #${selectedLocker.locker_number}`,
				"success",
			);
			closeModal();
			loadLockersData();
			loadOverviewData();
		} catch (e) {
			showToast(`Lỗi: ${e.message}`, "error");
		}
	});

	// Force Assign
	btnForceAssign.addEventListener("click", async () => {
		if (!selectedLocker) return;
		const cardId =
			selectedAssignCardId ||
			(searchInput ? searchInput.value.trim() : "");
		if (!cardId) {
			showToast("Vui lòng chọn hoặc nhập Card ID thành viên!", "error");
			return;
		}
		try {
			await GymTagAPI.forceAssignLocker(
				selectedLocker.locker_number,
				cardId,
			);
			showToast(
				`Đã gán thành viên cho Locker #${selectedLocker.locker_number}`,
				"success",
			);
			closeModal();
			loadLockersData();
			loadOverviewData();
		} catch (e) {
			showToast(`Lỗi gán locker: ${e.message}`, "error");
		}
	});

	// Toggle Broken / Status
	btnToggleBroken.addEventListener("click", async () => {
		if (!selectedLocker) return;
		const currentStatus =
			selectedLocker.status ||
			(selectedLocker.is_occupied ? "occupied" : "vacant");
		const newStatus = currentStatus === "broken" ? "vacant" : "broken";

		try {
			await GymTagAPI.setLockerStatus(
				selectedLocker.locker_number,
				newStatus,
			);
			showToast(
				newStatus === "broken"
					? `Đã báo hỏng Locker #${selectedLocker.locker_number}`
					: `Đã khôi phục Locker #${selectedLocker.locker_number} về trạng thái Trống`,
				"success",
			);
			closeModal();
			loadLockersData();
			loadOverviewData();
		} catch (e) {
			showToast(`Lỗi cập nhật trạng thái: ${e.message}`, "error");
		}
	});
}

function openLockerModal(locker) {
	selectedLocker = locker;
	selectedAssignCardId = null;
	const modal = document.getElementById("locker-modal");
	const title = document.getElementById("locker-modal-title");
	const summary = document.getElementById("locker-info-summary");
	const btnForceRelease = document.getElementById("btn-force-release");
	const btnToggleBroken = document.getElementById("btn-toggle-broken");
	const groupForceAssign = document.getElementById("group-force-assign");
	const searchInput = document.getElementById("assign-member-search");
	const wrapper = document.getElementById("assign-member-wrapper");

	title.textContent = `🔐 Quản Lý Locker #${locker.locker_number}`;
	if (searchInput) searchInput.value = "";
	if (wrapper) wrapper.classList.remove("open");

	GymTagAPI.getAdminMembers()
		.then((members) => {
			cachedMembers = members || [];
			renderMemberOptions("");
		})
		.catch((err) => {
			console.error("Error fetching members:", err);
		});

	const status =
		locker.status || (locker.is_occupied ? "occupied" : "vacant");
	let statusBadgeHtml = "";

	if (status === "broken") {
		statusBadgeHtml = `<span class="badge badge-warning">⚠️ Bị hỏng / Bảo trì</span>`;
	} else if (status === "occupied" || locker.is_occupied) {
		statusBadgeHtml = `<span class="badge badge-denied">🔴 Đang dùng</span>`;
	} else {
		statusBadgeHtml = `<span class="badge badge-granted">🟢 Trống (Sẵn sàng)</span>`;
	}

	const holderInfo = locker.card_id
		? `Card ID: <code>${escapeHtml(locker.card_id)}</code><br><small style="color:var(--text-muted);">Gán lúc: ${formatTime(locker.assigned_at)}</small>`
		: "Không có người sử dụng";

	summary.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
      <strong>Locker #${locker.locker_number}</strong>
      ${statusBadgeHtml}
    </div>
    <div style="font-size:0.85rem; color:var(--text-secondary);">
      ${holderInfo}
    </div>
  `;

	if (status === "broken") {
		groupForceAssign.style.display = "none";
		btnForceRelease.style.display = "none";
		btnToggleBroken.style.display = "block";
		btnToggleBroken.className = "btn btn-primary style-full";
		btnToggleBroken.innerHTML = "🛠️ Đã Sửa Xong (Đưa về trạng thái Trống)";
	} else if (status === "occupied" || locker.is_occupied) {
		groupForceAssign.style.display = "none";
		btnForceRelease.style.display = "block";
		btnToggleBroken.style.display = "block";
		btnToggleBroken.className = "btn btn-danger style-full";
		btnToggleBroken.innerHTML = "⚠️ Báo Hỏng / Đánh Dấu Bảo Trì";
	} else {
		groupForceAssign.style.display = "block";
		btnForceRelease.style.display = "none";
		btnToggleBroken.style.display = "block";
		btnToggleBroken.className = "btn btn-danger style-full";
		btnToggleBroken.innerHTML = "⚠️ Báo Hỏng / Đánh Dấu Bảo Trì";
	}

	modal.classList.add("active");
}

async function openEditModal(cardId) {
	try {
		const member = await GymTagAPI.getAdminMemberById(cardId);
		if (!member) return;

		isEditMode = true;
		document.getElementById("modal-title").textContent =
			`Chỉnh Sửa Thành Viên: ${member.card_id}`;

		const cardInput = document.getElementById("m-card-id");
		cardInput.value = member.card_id;
		cardInput.readOnly = true;

		document.getElementById("m-name").value = member.name || "";
		document.getElementById("m-email").value = member.email || "";
		document.getElementById("m-phone").value = member.phone || "";
		document.getElementById("m-expiry").value = member.membership_expiry
			? member.membership_expiry.split("T")[0]
			: "";
		document.getElementById("m-active").checked =
			member.is_active !== false;

		document.getElementById("member-modal").classList.add("active");
	} catch (e) {
		showToast("Lỗi khi lấy thông tin thành viên", "error");
	}
}

async function confirmDeleteMember(cardId) {
	if (
		confirm(`Bạn có chắc chắn muốn xoá thành viên với Card ID '${cardId}'?`)
	) {
		try {
			await GymTagAPI.deleteAdminMember(cardId);
			showToast(`Đã xoá thành viên ${cardId}`, "success");
			loadMembersData();
		} catch (e) {
			showToast(`Lỗi xoá thành viên: ${e.message}`, "error");
		}
	}
}

/* ----------------------------------------------------
 * TAB 3: LOCKERS MANAGEMENT
 * ---------------------------------------------------- */
async function loadLockersData() {
	try {
		const lockers = await GymTagAPI.getAdminLockers();
		renderAdminLockers(lockers);
		loadLockerLogsData();
	} catch (e) {
		showToast("Lỗi tải danh sách locker", "error");
	}
}

async function loadLockerLogsData() {
	const selectEl = document.getElementById("filter-locker-number");
	const lockerNumVal = selectEl ? selectEl.value : "";
	const cardIdVal = document.getElementById("filter-locker-card-id")?.value.trim() || null;

	let parsedLockerNumber = null;
	if (lockerNumVal && lockerNumVal !== "") {
		const num = parseInt(lockerNumVal, 10);
		if (!isNaN(num) && num > 0) {
			parsedLockerNumber = num;
		}
	}

	try {
		const logs = await GymTagAPI.getAdminLockerLogs(
			100,
			parsedLockerNumber,
			cardIdVal,
		);
		renderAdminLockerLogs(logs || []);
	} catch (e) {
		console.error("Error loading locker activity logs:", e);
	}
}

function renderAdminLockerLogs(logs) {
	const tbody = document.getElementById("admin-locker-logs-tbody");
	if (!tbody || !logs) return;

	if (logs.length === 0) {
		tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted); padding:1.5rem;">Chưa có nhật ký hoạt động locker nào.</td></tr>`;
		return;
	}

	const actionConfig = {
		assign: { text: "MƯỢN TỦ", badgeClass: "badge-info" },
		access: { text: "MỞ TỦ", badgeClass: "badge-primary" },
		release: { text: "TRẢ TỦ", badgeClass: "badge-granted" },
		force_assign: { text: "FORCE GÁN", badgeClass: "badge-warning" },
		force_release: { text: "FORCE MỞ", badgeClass: "badge-warning" },
		status_change: { text: "ĐỔI TRẠNG THÁI", badgeClass: "badge-purple" },
		denied: { text: "TỪ CHỐI", badgeClass: "badge-denied" },
	};

	tbody.innerHTML = logs
		.map((log) => {
			const isGranted = log.status === "granted";
			const actionInfo = actionConfig[log.action] || {
				text: (log.action || "--").toUpperCase(),
				badgeClass: "badge-secondary",
			};
			const resultBadgeClass = isGranted ? "badge-granted" : "badge-denied";
			const resultText = isGranted ? "THÀNH CÔNG" : "TỪ CHỐI";
			const timeFormatted = formatTime(log.timestamp);
			const dateFormatted = formatDate(log.timestamp);
			const fullTimeDisplay = log.timestamp
				? `<b>${timeFormatted}</b> <small style="color:var(--text-muted); margin-left:4px;">${dateFormatted}</small>`
				: "-";

			const lockerBadge = log.locker_number
				? `<span class="badge badge-secondary" style="font-weight:700;">#${log.locker_number}</span>`
				: `<span style="color:var(--text-muted);">-</span>`;

			const cardStr = log.card_id
				? `<code>${escapeHtml(log.card_id)}</code>`
				: `<span style="color:var(--text-muted);">-</span>`;

			return `
      <tr>
        <td>${fullTimeDisplay}</td>
        <td>${lockerBadge}</td>
        <td>${cardStr}</td>
        <td><strong>${escapeHtml(log.member_name || "Unknown")}</strong></td>
        <td><span class="badge ${actionInfo.badgeClass}">${actionInfo.text}</span></td>
        <td><span class="badge ${resultBadgeClass}">${resultText}</span></td>
        <td><small style="color:var(--text-muted);">${escapeHtml(log.reason || "-")}</small></td>
      </tr>
    `;
		})
		.join("");
}

function updateLockerFilterOptions(lockers) {
	const select = document.getElementById("filter-locker-number");
	if (!select || !lockers) return;

	const currentVal = select.value || "";
	const existingOptions = Array.from(select.options)
		.map((opt) => opt.value)
		.filter((v) => v !== "");
	const newOptions = lockers.map((l) => String(l.locker_number));

	// If options haven't changed, just preserve selected value without recreating DOM
	const isSame = existingOptions.length === newOptions.length &&
		existingOptions.every((v, i) => v === newOptions[i]);

	if (isSame) {
		select.value = currentVal;
		return;
	}

	const isAllSelected = (!currentVal || currentVal === "") ? "selected" : "";
	const options = [`<option value="" ${isAllSelected}>Tất cả tủ</option>`];

	lockers.forEach((l) => {
		const num = l.locker_number;
		const isSelected = currentVal === String(num) ? "selected" : "";
		options.push(`<option value="${num}" ${isSelected}>Locker #${num}</option>`);
	});

	select.innerHTML = options.join("");
	select.value = currentVal;
}

function renderAdminLockers(lockers) {
	const container = document.getElementById("admin-locker-grid");
	const summary = document.getElementById("admin-locker-summary");
	if (!container || !lockers) return;

	updateLockerFilterOptions(lockers);

	const total = lockers.length;
	const occupied = lockers.filter(
		(l) => l.is_occupied || l.status === "occupied",
	).length;
	const broken = lockers.filter((l) => l.status === "broken").length;
	summary.textContent =
		`${occupied} / ${total} Locker đang dùng` +
		(broken > 0 ? ` (${broken} hỏng)` : "");

	container.innerHTML = lockers
		.map((l) => {
			const status = l.status || (l.is_occupied ? "occupied" : "vacant");
			let statusClass = "vacant";
			let statusText = "Trống";

			if (status === "broken") {
				statusClass = "broken";
				statusText = "Hỏng";
			} else if (status === "occupied" || l.is_occupied) {
				statusClass = "occupied";
				statusText = "Đang dùng";
			}

			const cardStr = l.card_id ? escapeHtml(l.card_id) : "-";
			const assignedTimeStr = l.assigned_at
				? formatTime(l.assigned_at)
				: "";

			return `
      <div class="locker-card ${statusClass} admin-clickable" data-locker="${l.locker_number}">
        <div class="locker-title">LOCKER</div>
        <div class="locker-number">#${l.locker_number}</div>
        <div class="locker-status-text">${statusText}</div>
        <div class="locker-holder">
          ${
				status === "broken"
					? '<small style="color:var(--status-warning);">🛠️ Bảo trì</small>'
					: status === "occupied" || l.is_occupied
						? `ID: <code>${cardStr}</code><br><small style="color:var(--text-muted);">${assignedTimeStr}</small>`
						: "Sẵn sàng"
			}
        </div>
      </div>
    `;
		})
		.join("");

	container
		.querySelectorAll(".locker-card.admin-clickable")
		.forEach((cardEl) => {
			cardEl.addEventListener("click", () => {
				const lockerNum = parseInt(
					cardEl.getAttribute("data-locker"),
					10,
				);
				const lockerObj = lockers.find(
					(l) => l.locker_number === lockerNum,
				);
				if (lockerObj) {
					openLockerModal(lockerObj);
				}
			});
		});
}

/* ----------------------------------------------------
 * TAB 4: ACCESS LOGS
 * ---------------------------------------------------- */
async function loadLogsData() {
	const cardIdFilter = document.getElementById("filter-card-id").value.trim();
	try {
		const logs = await GymTagAPI.getAdminActivityLogs(
			100,
			cardIdFilter || null,
		);
		renderAdminLogs(logs);
	} catch (e) {
		showToast("Lỗi tải nhật ký ra vào", "error");
	}
}

function renderAdminLogs(logs) {
	const tbody = document.getElementById("admin-logs-tbody");
	if (!tbody || !logs) return;

	if (logs.length === 0) {
		tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">Không tìm thấy nhật ký phù hợp.</td></tr>`;
		return;
	}

	tbody.innerHTML = logs
		.map((log) => {
			const isGranted = log.status === "granted";
			const badgeClass = isGranted
				? log.action === "checkin"
					? "badge-granted"
					: "badge-warning"
				: "badge-denied";

			return `
      <tr>
        <td>${formatTime(log.timestamp)}</td>
        <td><code>${escapeHtml(log.card_id)}</code></td>
        <td><strong>${escapeHtml(log.member_name)}</strong></td>
        <td><span class="badge badge-info">${log.action.toUpperCase()}</span></td>
        <td><span class="badge ${badgeClass}">${isGranted ? "CHO PHÉP" : "TỪ CHỐI"}</span></td>
        <td>${formatDuration(log.duration_minutes)}</td>
        <td><small style="color:var(--text-muted);">${escapeHtml(log.reason || "-")}</small></td>
      </tr>
    `;
		})
		.join("");
}

/* ----------------------------------------------------
 * TAB 5: ENVIRONMENT HISTORY
 * ---------------------------------------------------- */
let adminEnvHistory = [];

async function loadEnvironmentHistoryData() {
	try {
		adminEnvHistory = await GymTagAPI.getAdminEnvironmentHistory(50);
		renderEnvironmentHistory(adminEnvHistory);
	} catch (e) {
		showToast("Lỗi tải lịch sử môi trường", "error");
	}
}

function handleRealtimeEnvironmentUpdate(data) {
	if (!data || (data.temperature === undefined && data.humidity === undefined)) return;

	const newReading = {
		temperature: typeof data.temperature === "number" ? data.temperature : parseFloat(data.temperature),
		humidity: typeof data.humidity === "number" ? data.humidity : parseFloat(data.humidity),
		fan_on: Boolean(data.fan_on),
		timestamp: data.timestamp || new Date().toISOString(),
		manual_mode: data.manual_mode,
	};

	// Update live fan badge & mode
	updateAdminFanUI(newReading.fan_on, newReading.manual_mode);

	// Deduplicate: check if this reading is already recorded at top of history
	if (adminEnvHistory.length > 0) {
		const latest = adminEnvHistory[0];
		if (
			latest.timestamp === newReading.timestamp &&
			latest.temperature === newReading.temperature &&
			latest.humidity === newReading.humidity &&
			latest.fan_on === newReading.fan_on
		) {
			return;
		}
	}

	// Prepend to history cache in real time
	adminEnvHistory.unshift(newReading);
	if (adminEnvHistory.length > 50) {
		adminEnvHistory.pop();
	}

	// Live re-render table immediately
	renderEnvironmentHistory(adminEnvHistory);
}

function updateAdminFanUI(fanOn, manualMode) {
	const fanBadge = document.getElementById("admin-fan-badge");
	if (fanBadge && fanOn !== undefined && fanOn !== null) {
		fanBadge.textContent = fanOn ? "🌀 BẬT" : "🛑 TẮT";
		fanBadge.className = fanOn
			? "badge badge-info"
			: "badge badge-secondary";
	}

	const modeBadge = document.getElementById("admin-fan-mode-badge");
	if (modeBadge && manualMode !== undefined) {
		if (manualMode) {
			modeBadge.textContent = "🛠️ THỦ CÔNG (Admin)";
			modeBadge.className = "badge badge-warning";
			modeBadge.title = "Lệnh thủ công của Admin đang có hiệu lực tuyệt đối (Bỏ qua tự động).";
		} else {
			modeBadge.textContent = "🤖 TỰ ĐỘNG";
			modeBadge.className = "badge badge-success";
			modeBadge.title = "Tự động kích hoạt quạt khi nhiệt độ / độ ẩm vượt ngưỡng.";
		}
	}
}

function setupFanControl() {
	const btnOn = document.getElementById("btn-fan-on");
	const btnOff = document.getElementById("btn-fan-off");
	const btnAuto = document.getElementById("btn-fan-auto");

	if (btnOn) {
		btnOn.addEventListener("click", async () => {
			try {
				await GymTagAPI.controlAdminFan("on");
				showToast("Đã gửi lệnh ép BẬT quạt (Thủ công - Ưu tiên cao nhất)!", "success");
				updateAdminFanUI(true, true);
				loadEnvironmentHistoryData();
			} catch (e) {
				showToast(`Lỗi điều khiển quạt: ${e.message}`, "error");
			}
		});
	}

	if (btnOff) {
		btnOff.addEventListener("click", async () => {
			try {
				await GymTagAPI.controlAdminFan("off");
				showToast("Đã gửi lệnh ép TẮT quạt (Thủ công - Ưu tiên cao nhất)!", "success");
				updateAdminFanUI(false, true);
				loadEnvironmentHistoryData();
			} catch (e) {
				showToast(`Lỗi điều khiển quạt: ${e.message}`, "error");
			}
		});
	}

	if (btnAuto) {
		btnAuto.addEventListener("click", async () => {
			try {
				await GymTagAPI.controlAdminFan("auto");
				showToast("Đã chuyển quạt về chế độ TỰ ĐỘNG theo ngưỡng cảm biến!", "success");
				updateAdminFanUI(undefined, false);
				loadEnvironmentHistoryData();
			} catch (e) {
				showToast(`Lỗi chuyển chế độ: ${e.message}`, "error");
			}
		});
	}
}

/* ----------------------------------------------------
 * THRESHOLD CONFIGURATION
 * ---------------------------------------------------- */
// Ensure threshold API methods exist even if browser cached older api.js module
if (typeof GymTagAPI.getEnvironmentThresholds !== "function") {
	GymTagAPI.getEnvironmentThresholds = async () => {
		const token = sessionStorage.getItem("gymtag_admin_token");
		const res = await fetch("/api/admin/environment/thresholds", {
			headers: token ? { Authorization: `Bearer ${token}` } : {},
		});
		if (!res.ok) throw new Error("Không thể tải ngưỡng môi trường");
		return res.json();
	};
}

if (typeof GymTagAPI.updateEnvironmentThresholds !== "function") {
	GymTagAPI.updateEnvironmentThresholds = async (
		tempThreshold,
		humidityThreshold,
	) => {
		const token = sessionStorage.getItem("gymtag_admin_token");
		const res = await fetch("/api/admin/environment/thresholds", {
			method: "PUT",
			headers: {
				"Content-Type": "application/json",
				...(token ? { Authorization: `Bearer ${token}` } : {}),
			},
			body: JSON.stringify({
				temp_threshold: tempThreshold,
				humidity_threshold: humidityThreshold,
			}),
		});
		if (!res.ok) throw new Error("Không thể lưu ngưỡng môi trường");
		return res.json();
	};
}

if (typeof GymTagAPI.testTelegramAlert !== "function") {
	GymTagAPI.testTelegramAlert = async () => {
		const token = sessionStorage.getItem("gymtag_admin_token");
		const res = await fetch("/api/admin/telegram/test", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				...(token ? { Authorization: `Bearer ${token}` } : {}),
			},
		});
		if (!res.ok) {
			const data = await res.json().catch(() => ({}));
			throw new Error(data.detail || "Không thể gửi cảnh báo thử nghiệm");
		}
		return res.json();
	};
}

async function loadThresholds() {


	try {
		const data = await GymTagAPI.getEnvironmentThresholds();
		if (data) {
			if (
				data.temp_threshold !== undefined &&
				data.temp_threshold !== null
			) {
				const tempInput = document.getElementById("threshold-temp");
				if (tempInput)
					tempInput.value = parseFloat(data.temp_threshold).toFixed(
						1,
					);
			}
			if (
				data.humidity_threshold !== undefined &&
				data.humidity_threshold !== null
			) {
				const humInput = document.getElementById("threshold-humidity");
				if (humInput)
					humInput.value = parseFloat(
						data.humidity_threshold,
					).toFixed(1);
			}
		}
	} catch (e) {
		console.error("Error loading environment thresholds:", e);
	}
}

function adjustThreshold(targetId, step) {
	const input = document.getElementById(targetId);
	if (!input) return;

	const rawVal = input.value.toString().trim().replace(",", ".");
	let currentVal = parseFloat(rawVal);
	if (isNaN(currentVal)) {
		currentVal = targetId === "threshold-temp" ? 32.0 : 80.0;
	}

	const isDecimal = step % 1 !== 0 || targetId === "threshold-temp";
	let newVal = Math.max(0, Math.min(100, currentVal + step));
	input.value = isDecimal ? newVal.toFixed(1) : newVal.toFixed(0);
}

function setupThresholdControls() {
	// Delegate click for any .stepper-btn or .threshold-adjust button
	document.addEventListener("click", (e) => {
		const btn = e.target.closest(".stepper-btn, .threshold-adjust");
		if (!btn) return;

		e.preventDefault();
		e.stopPropagation();

		const targetId = btn.getAttribute("data-target");
		const step = parseFloat(btn.getAttribute("data-step"));
		if (targetId && !isNaN(step)) {
			adjustThreshold(targetId, step);
		}
	});

	// Keyboard navigation & validation for stepper inputs
	const attachInputEvents = (inputId, defaultStep) => {
		const input = document.getElementById(inputId);
		if (!input) return;

		input.addEventListener("keydown", (e) => {
			if (e.key === "ArrowUp") {
				e.preventDefault();
				adjustThreshold(inputId, defaultStep);
			} else if (e.key === "ArrowDown") {
				e.preventDefault();
				adjustThreshold(inputId, -defaultStep);
			} else if (e.key === "Enter") {
				e.preventDefault();
				document.getElementById("btn-save-thresholds")?.click();
			}
		});

		input.addEventListener("blur", () => {
			const raw = input.value.toString().trim().replace(",", ".");
			let val = parseFloat(raw);
			if (isNaN(val)) {
				val = inputId === "threshold-temp" ? 32.0 : 80.0;
			}
			val = Math.max(0, Math.min(100, val));
			input.value =
				inputId === "threshold-temp" ? val.toFixed(1) : val.toFixed(1);
		});
	};

	attachInputEvents("threshold-temp", 0.5);
	attachInputEvents("threshold-humidity", 1.0);

	// Save thresholds button
	const btnSave = document.getElementById("btn-save-thresholds");
	const statusEl = document.getElementById("threshold-save-status");

	if (btnSave) {
		btnSave.addEventListener("click", async () => {
			const tempInput = document.getElementById("threshold-temp");
			const humInput = document.getElementById("threshold-humidity");

			const tempVal = parseFloat(tempInput.value.replace(",", "."));
			const humVal = parseFloat(humInput.value.replace(",", "."));

			if (
				isNaN(tempVal) ||
				isNaN(humVal) ||
				tempVal < 0 ||
				tempVal > 100 ||
				humVal < 0 ||
				humVal > 100
			) {
				showToast(
					"Vui lòng nhập giá trị ngưỡng hợp lệ (từ 0 đến 100)!",
					"error",
				);
				return;
			}

			btnSave.disabled = true;
			btnSave.innerHTML = "<span>⏳ Đang lưu...</span>";

			try {
				await GymTagAPI.updateEnvironmentThresholds(tempVal, humVal);
				showToast(
					"Đã lưu cấu hình ngưỡng nhiệt độ & độ ẩm mới thành công!",
					"success",
				);
				if (statusEl) {
					statusEl.textContent = "✅ Đã lưu!";
					setTimeout(() => {
						statusEl.textContent = "";
					}, 3500);
				}
				loadEnvironmentHistoryData();
			} catch (e) {
				showToast(`Lỗi khi lưu ngưỡng: ${e.message}`, "error");
				if (statusEl) {
					statusEl.textContent = "❌ Lỗi";
					setTimeout(() => {
						statusEl.textContent = "";
					}, 3500);
				}
			} finally {
				btnSave.disabled = false;
				btnSave.innerHTML = "<span>💾 Lưu Cấu Hình</span>";
			}
		});
	}

	// Test Telegram Alert button
	const btnTestTelegram = document.getElementById("btn-test-telegram");
	if (btnTestTelegram) {
		btnTestTelegram.addEventListener("click", async () => {
			btnTestTelegram.disabled = true;
			btnTestTelegram.innerHTML = "<span>⏳ Đang gửi...</span>";
			try {
				await GymTagAPI.testTelegramAlert();
				showToast("✅ Đã gửi thông báo thử nghiệm tới Telegram thành công!", "success");
			} catch (err) {
				showToast(`❌ Thất bại: ${err.message}`, "error");
			} finally {
				btnTestTelegram.disabled = false;
				btnTestTelegram.innerHTML = "<span>📲 Thử Bot Telegram</span>";
			}
		});
	}

	// Pre-fetch thresholds
	loadThresholds();
}

function renderEnvironmentHistory(history) {
	const tbody = document.getElementById("env-history-tbody");
	if (!tbody || !history) return;

	if (history.length === 0) {
		tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">Chưa có dữ liệu lịch sử môi trường.</td></tr>`;
		return;
	}

	if (history.length > 0) {
		updateAdminFanUI(history[0].fan_on, history[0].manual_mode);
	}

	const tempThreshold =
		parseFloat(document.getElementById("threshold-temp")?.value) || 32.0;
	const humThreshold =
		parseFloat(document.getElementById("threshold-humidity")?.value) ||
		80.0;

	tbody.innerHTML = history
		.map((item) => {
			const isHighTemp = item.temperature > tempThreshold;
			const isHighHum = item.humidity > humThreshold;
			const timeFormatted = formatTime(item.timestamp);
			const dateFormatted = formatDate(item.timestamp);
			const fullTimeDisplay = item.timestamp
				? `<b>${timeFormatted}</b> <small style="color:var(--text-muted); margin-left:4px;">${dateFormatted}</small>`
				: "-";

			const tempNum = typeof item.temperature === "number" ? item.temperature : parseFloat(item.temperature);
			const humNum = typeof item.humidity === "number" ? item.humidity : parseFloat(item.humidity);

			return `
      <tr>
        <td>${fullTimeDisplay}</td>
        <td style="${isHighTemp ? "color:var(--status-danger); font-weight:bold;" : ""}">
          ${!isNaN(tempNum) ? tempNum.toFixed(1) : "--"} °C ${isHighTemp ? '<small title="Vượt ngưỡng">⚠️</small>' : ""}
        </td>
        <td style="${isHighHum ? "color:var(--status-danger); font-weight:bold;" : ""}">
          ${!isNaN(humNum) ? humNum.toFixed(1) : "--"} % ${isHighHum ? '<small title="Vượt ngưỡng">⚠️</small>' : ""}
        </td>
        <td>
          <span class="badge ${item.fan_on ? "badge-info" : "badge-secondary"}">
            ${item.fan_on ? "🌀 BẬT (Fan ON)" : "TẮT (Fan OFF)"}
          </span>
        </td>
      </tr>
    `;
		})
		.join("");
}

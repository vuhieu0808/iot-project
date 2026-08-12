/**
 * GymTag Admin Panel App Controller
 */

import { GymTagAPI } from '../shared/js/api.js';
import { wsClient } from '../shared/js/websocket.js';
import { formatTime, formatDate, formatDuration, escapeHtml, showToast } from '../shared/js/utils.js';

const ADMIN_PASSKEY = 'admin123';
let isEditMode = false;

document.addEventListener('DOMContentLoaded', () => {
  setupAuth();
});

function setupAuth() {
  const loginOverlay = document.getElementById('admin-login-overlay');
  const loginForm = document.getElementById('admin-login-form');
  const passkeyInput = document.getElementById('admin-passkey-input');
  const errorMsg = document.getElementById('login-error-msg');
  const btnLogout = document.getElementById('btn-admin-logout');

  // Check existing session
  if (sessionStorage.getItem('gymtag_admin_authed') === 'true') {
    loginOverlay.classList.remove('active');
    initAdmin();
  } else {
    loginOverlay.classList.add('active');
  }

  // Handle Login submission
  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const inputVal = passkeyInput.value.trim();

    if (inputVal === ADMIN_PASSKEY) {
      sessionStorage.setItem('gymtag_admin_authed', 'true');
      loginOverlay.classList.remove('active');
      errorMsg.style.display = 'none';
      passkeyInput.value = '';
      showToast('Đăng nhập Quản trị Admin thành công!', 'success');
      initAdmin();
    } else {
      errorMsg.style.display = 'block';
      passkeyInput.select();
    }
  });

  // Handle Logout
  if (btnLogout) {
    btnLogout.addEventListener('click', () => {
      sessionStorage.removeItem('gymtag_admin_authed');
      loginOverlay.classList.add('active');
      showToast('Đã đăng xuất tài khoản Admin', 'success');
    });
  }
}

async function initAdmin() {
  setupTabs();
  setupModal();
  setupWebSocket();
  await loadOverviewData();
}

/* ----------------------------------------------------
 * Tab Routing Navigation
 * ---------------------------------------------------- */
function setupTabs() {
  const navButtons = document.querySelectorAll('.sidebar-nav .nav-item');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const pageTitle = document.getElementById('page-title');

  const titles = {
    overview: 'Tổng Quan Hệ Thống',
    members: 'Quản Lý Thành Viên',
    lockers: 'Quản Lý Locker',
    logs: 'Lịch SửRa Vào',
    environment: 'Lịch Sử Môi Trường'
  };

  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabName = btn.getAttribute('data-tab');

      navButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      document.getElementById(`tab-${tabName}`).classList.add('active');
      pageTitle.textContent = titles[tabName] || 'Admin Control';

      // Load specific tab data
      switch (tabName) {
        case 'overview':
          loadOverviewData();
          break;
        case 'members':
          loadMembersData();
          break;
        case 'lockers':
          loadLockersData();
          break;
        case 'logs':
          loadLogsData();
          break;
        case 'environment':
          loadEnvironmentHistoryData();
          break;
      }
    });
  });

  // Filter logs handler
  document.getElementById('btn-filter-logs').addEventListener('click', () => {
    loadLogsData();
  });

  document.getElementById('btn-refresh-env').addEventListener('click', () => {
    loadEnvironmentHistoryData();
  });
}

/* ----------------------------------------------------
 * WebSocket Connection & Events
 * ---------------------------------------------------- */
function setupWebSocket() {
  const indicatorEl = document.getElementById('ws-indicator');
  const statusTextEl = document.getElementById('ws-status-text');

  wsClient.onStatusChange((status) => {
    indicatorEl.className = 'ws-indicator';
    if (status === 'connected') {
      indicatorEl.classList.add('connected');
      statusTextEl.textContent = 'Realtime Live';
    } else if (status === 'connecting') {
      statusTextEl.textContent = 'Đang kết nối...';
    } else {
      indicatorEl.classList.add('disconnected');
      statusTextEl.textContent = 'Mất kết nối';
    }
  });

  wsClient.on('checkin_event', () => {
    loadOverviewData();
    if (document.getElementById('tab-logs').classList.contains('active')) {
      loadLogsData();
    }
  });

  wsClient.on('locker_event', (data) => {
    if (data.lockers) {
      renderOverviewLockers(data.lockers);
      renderAdminLockers(data.lockers);
    } else {
      loadLockersData();
    }
  });

  wsClient.on('environment_update', (data) => {
    renderOverviewEnvironment(data);
  });

  wsClient.connect();
}

/* ----------------------------------------------------
 * TAB 1: OVERVIEW DATA
 * ---------------------------------------------------- */
async function loadOverviewData() {
  try {
    const [occupancy, envLatest, lockers, members, logs] = await Promise.all([
      GymTagAPI.getOccupancy(),
      GymTagAPI.getLatestEnvironment().catch(() => null),
      GymTagAPI.getLockers(),
      GymTagAPI.getMembers(),
      GymTagAPI.getCheckLogs(5)
    ]);

    document.getElementById('overview-occupancy').textContent = occupancy.current_occupancy;
    document.getElementById('overview-members').textContent = members.length;

    renderOverviewEnvironment(envLatest);
    renderOverviewLockers(lockers);
    renderOverviewLogs(logs);
  } catch (e) {
    console.error('Error loading overview data:', e);
  }
}

function renderOverviewEnvironment(data) {
  const envValEl = document.getElementById('overview-env');
  const fanSubEl = document.getElementById('overview-fan');
  if (!data) return;

  envValEl.textContent = `${data.temperature.toFixed(1)}°C / ${data.humidity.toFixed(1)}%`;
  fanSubEl.textContent = `Quạt thông gió: ${data.fan_on ? 'ĐANG BẬT' : 'ĐANG TẮT'}`;
}

function renderOverviewLockers(lockers) {
  const countEl = document.getElementById('overview-lockers');
  const gridEl = document.getElementById('overview-locker-grid');
  if (!lockers) return;

  const total = lockers.length;
  const occupied = lockers.filter(l => l.is_occupied).length;
  countEl.textContent = `${occupied} / ${total}`;

  gridEl.innerHTML = lockers.map(l => `
    <div class="locker-card ${l.is_occupied ? 'occupied' : 'vacant'}">
      <div class="locker-number">Locker #${l.locker_number}</div>
      <div class="locker-status-text">${l.is_occupied ? 'Đang dùng' : 'Trống'}</div>
    </div>
  `).join('');
}

function renderOverviewLogs(logs) {
  const tbody = document.getElementById('overview-logs-tbody');
  if (!tbody || !logs) return;

  tbody.innerHTML = logs.map(log => `
    <tr>
      <td>${formatTime(log.timestamp)}</td>
      <td><code>${escapeHtml(log.card_id)}</code></td>
      <td>${escapeHtml(log.member_name)}</td>
      <td><span class="badge badge-info">${log.action.toUpperCase()}</span></td>
      <td><span class="badge ${log.status === 'granted' ? 'badge-granted' : 'badge-denied'}">${log.status.toUpperCase()}</span></td>
    </tr>
  `).join('');
}

/* ----------------------------------------------------
 * TAB 2: MEMBERS MANAGEMENT & CRUD
 * ---------------------------------------------------- */
async function loadMembersData() {
  try {
    const members = await GymTagAPI.getMembers();
    renderMembersTable(members);
  } catch (e) {
    showToast('Lỗi khi tải danh sách thành viên', 'error');
  }
}

function renderMembersTable(members) {
  const tbody = document.getElementById('members-tbody');
  if (!tbody) return;

  if (members.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">Chưa có thành viên nào. Hãy bấm "Thêm Thành Viên Mới".</td></tr>`;
    return;
  }

  tbody.innerHTML = members.map(m => {
    const isExpired = new Date(m.membership_expiry) < new Date();
    const statusBadge = isExpired
      ? `<span class="badge badge-denied">Hết hạn</span>`
      : `<span class="badge badge-granted">Còn hạn</span>`;

    return `
      <tr>
        <td><code>${escapeHtml(m.card_id)}</code></td>
        <td><strong>${escapeHtml(m.name)}</strong></td>
        <td>${escapeHtml(m.email || '-')}</td>
        <td>${escapeHtml(m.phone || '-')}</td>
        <td>${formatDate(m.membership_expiry)}</td>
        <td>${statusBadge}</td>
        <td>
          <button class="btn btn-secondary btn-sm edit-member-btn" data-card="${escapeHtml(m.card_id)}">✏️ Sửa</button>
          <button class="btn btn-danger btn-sm delete-member-btn" data-card="${escapeHtml(m.card_id)}">🗑️ Xoá</button>
        </td>
      </tr>
    `;
  }).join('');

  // Attach action listeners
  document.querySelectorAll('.edit-member-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const cardId = btn.getAttribute('data-card');
      openEditModal(cardId);
    });
  });

  document.querySelectorAll('.delete-member-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const cardId = btn.getAttribute('data-card');
      confirmDeleteMember(cardId);
    });
  });
}

function setupModal() {
  const modal = document.getElementById('member-modal');
  const btnAdd = document.getElementById('btn-add-member');
  const btnClose = document.getElementById('btn-close-modal');
  const btnCancel = document.getElementById('btn-cancel-modal');
  const form = document.getElementById('member-form');

  btnAdd.addEventListener('click', () => {
    isEditMode = false;
    document.getElementById('modal-title').textContent = 'Thêm Thành Viên Mới';
    document.getElementById('m-card-id').readOnly = false;
    form.reset();
    modal.classList.add('active');
  });

  const closeModal = () => modal.classList.remove('active');
  btnClose.addEventListener('click', closeModal);
  btnCancel.addEventListener('click', closeModal);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const cardId = document.getElementById('m-card-id').value.trim();
    const name = document.getElementById('m-name').value.trim();
    const email = document.getElementById('m-email').value.trim();
    const phone = document.getElementById('m-phone').value.trim();
    const expiry = document.getElementById('m-expiry').value;

    try {
      await GymTagAPI.saveMember({
        card_id: cardId,
        name: name,
        email: email || null,
        phone: phone || null,
        membership_expiry: expiry,
        is_active: true
      });

      showToast(isEditMode ? 'Cập nhật thành viên thành công!' : 'Đã thêm thành viên mới!', 'success');
      closeModal();
      loadMembersData();
    } catch (err) {
      showToast(`Lỗi: ${err.message}`, 'error');
    }
  });
}

async function openEditModal(cardId) {
  try {
    const member = await GymTagAPI.getMemberById(cardId);
    if (!member) return;

    isEditMode = true;
    document.getElementById('modal-title').textContent = `Chỉnh Sửa Thành Viên: ${member.card_id}`;
    
    const cardInput = document.getElementById('m-card-id');
    cardInput.value = member.card_id;
    cardInput.readOnly = true;

    document.getElementById('m-name').value = member.name || '';
    document.getElementById('m-email').value = member.email || '';
    document.getElementById('m-phone').value = member.phone || '';
    document.getElementById('m-expiry').value = member.membership_expiry ? member.membership_expiry.split('T')[0] : '';

    document.getElementById('member-modal').classList.add('active');
  } catch (e) {
    showToast('Lỗi khi lấy thông tin thành viên', 'error');
  }
}

async function confirmDeleteMember(cardId) {
  if (confirm(`Bạn có chắc chắn muốn xoá thành viên với Card ID '${cardId}'?`)) {
    try {
      await GymTagAPI.deleteMember(cardId);
      showToast(`Đã xoá thành viên ${cardId}`, 'success');
      loadMembersData();
    } catch (e) {
      showToast(`Lỗi xoá thành viên: ${e.message}`, 'error');
    }
  }
}

/* ----------------------------------------------------
 * TAB 3: LOCKERS MANAGEMENT
 * ---------------------------------------------------- */
async function loadLockersData() {
  try {
    const lockers = await GymTagAPI.getLockers();
    renderAdminLockers(lockers);
  } catch (e) {
    showToast('Lỗi tải danh sách locker', 'error');
  }
}

function renderAdminLockers(lockers) {
  const container = document.getElementById('admin-locker-grid');
  const summary = document.getElementById('admin-locker-summary');
  if (!container || !lockers) return;

  const total = lockers.length;
  const occupied = lockers.filter(l => l.is_occupied).length;
  summary.textContent = `${occupied} / ${total} Locker đang có người dùng`;

  container.innerHTML = lockers.map(l => {
    const isOccupied = l.is_occupied;
    const cardStr = l.card_id ? escapeHtml(l.card_id) : '-';
    const assignedTimeStr = l.assigned_at ? formatTime(l.assigned_at) : '';

    return `
      <div class="locker-card ${isOccupied ? 'occupied' : 'vacant'}">
        <div class="locker-number">Locker #${l.locker_number}</div>
        <div class="locker-status-text">${isOccupied ? 'Đang dùng' : 'Trống'}</div>
        <div class="locker-holder">
          ${isOccupied ? `ID: <code>${cardStr}</code><br><small style="color:var(--text-muted);">${assignedTimeStr}</small>` : 'Sẵn sàng'}
        </div>
      </div>
    `;
  }).join('');
}

/* ----------------------------------------------------
 * TAB 4: ACCESS LOGS
 * ---------------------------------------------------- */
async function loadLogsData() {
  const cardIdFilter = document.getElementById('filter-card-id').value.trim();
  try {
    const logs = await GymTagAPI.getCheckLogs(100, cardIdFilter || null);
    renderAdminLogs(logs);
  } catch (e) {
    showToast('Lỗi tải nhật ký ra vào', 'error');
  }
}

function renderAdminLogs(logs) {
  const tbody = document.getElementById('admin-logs-tbody');
  if (!tbody || !logs) return;

  if (logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">Không tìm thấy nhật ký phù hợp.</td></tr>`;
    return;
  }

  tbody.innerHTML = logs.map(log => {
    const isGranted = log.status === 'granted';
    const badgeClass = isGranted
      ? (log.action === 'checkin' ? 'badge-granted' : 'badge-warning')
      : 'badge-denied';

    return `
      <tr>
        <td>${formatTime(log.timestamp)}</td>
        <td><code>${escapeHtml(log.card_id)}</code></td>
        <td><strong>${escapeHtml(log.member_name)}</strong></td>
        <td><span class="badge badge-info">${log.action.toUpperCase()}</span></td>
        <td><span class="badge ${badgeClass}">${isGranted ? 'CHO PHÉP' : 'TỪ CHỐI'}</span></td>
        <td>${formatDuration(log.duration_minutes)}</td>
        <td><small style="color:var(--text-muted);">${escapeHtml(log.reason || '-')}</small></td>
      </tr>
    `;
  }).join('');
}

/* ----------------------------------------------------
 * TAB 5: ENVIRONMENT HISTORY
 * ---------------------------------------------------- */
async function loadEnvironmentHistoryData() {
  try {
    const history = await GymTagAPI.getEnvironmentHistory(50);
    renderEnvironmentHistory(history);
  } catch (e) {
    showToast('Lỗi tải lịch sử môi trường', 'error');
  }
}

function renderEnvironmentHistory(history) {
  const tbody = document.getElementById('env-history-tbody');
  if (!tbody || !history) return;

  if (history.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">Chưa có dữ liệu lịch sử môi trường.</td></tr>`;
    return;
  }

  tbody.innerHTML = history.map(item => {
    const isHighTemp = item.temperature >= 32.0;
    const isHighHum = item.humidity >= 80.0;
    const isWarning = isHighTemp || isHighHum;

    return `
      <tr>
        <td>${formatTime(item.timestamp)}</td>
        <td style="${isHighTemp ? 'color:var(--status-danger); font-weight:bold;' : ''}">${item.temperature.toFixed(1)} °C</td>
        <td style="${isHighHum ? 'color:var(--status-danger); font-weight:bold;' : ''}">${item.humidity.toFixed(1)} %</td>
        <td>
          <span class="badge ${item.fan_on ? 'badge-info' : 'badge-secondary'}">
            ${item.fan_on ? '🌀 BẬT (Fan ON)' : 'TẮT (Fan OFF)'}
          </span>
        </td>
      </tr>
    `;
  }).join('');
}

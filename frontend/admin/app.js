/**
 * GymTag Admin Panel App Controller
 */

import { GymTagAPI } from '../shared/js/api.js?v=3.2';
import { wsClient } from '../shared/js/websocket.js';
import { formatTime, formatDate, formatDuration, escapeHtml, showToast } from '../shared/js/utils.js';

const ADMIN_PASSKEY = 'admin123';
let isEditMode = false;
let cachedMembers = [];


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
  setupLockerModal();
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
    logs: 'Lịch Sử Ra Vào',
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
  const occupied = lockers.filter(l => l.is_occupied || l.status === 'occupied').length;
  const broken = lockers.filter(l => l.status === 'broken').length;
  countEl.textContent = `${occupied} / ${total}${broken > 0 ? ` (${broken} hỏng)` : ''}`;

  gridEl.innerHTML = lockers.map(l => {
    const status = l.status || (l.is_occupied ? 'occupied' : 'vacant');
    let statusClass = 'vacant';
    let statusText = 'Trống';

    if (status === 'broken') {
      statusClass = 'broken';
      statusText = 'Hỏng';
    } else if (status === 'occupied' || l.is_occupied) {
      statusClass = 'occupied';
      statusText = 'Đang dùng';
    }

    return `
      <div class="locker-card ${statusClass} admin-clickable" data-locker="${l.locker_number}">
        <div class="locker-title">LOCKER</div>
        <div class="locker-number">#${l.locker_number}</div>
        <div class="locker-status-text">${statusText}</div>
      </div>
    `;
  }).join('');

  gridEl.querySelectorAll('.locker-card.admin-clickable').forEach(cardEl => {
    cardEl.addEventListener('click', () => {
      const lockerNum = parseInt(cardEl.getAttribute('data-locker'), 10);
      const lockerObj = lockers.find(l => l.locker_number === lockerNum);
      if (lockerObj) {
        openLockerModal(lockerObj);
      }
    });
  });
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

let selectedLocker = null;
let selectedAssignCardId = null;

function renderMemberOptions(filterText = '') {
  const listEl = document.getElementById('assign-member-list');
  if (!listEl) return;

  const term = filterText.toLowerCase();
  const filtered = cachedMembers.filter(m => {
    const nameMatch = m.name ? m.name.toLowerCase().includes(term) : false;
    const cardMatch = m.card_id ? m.card_id.toLowerCase().includes(term) : false;
    const phoneMatch = m.phone ? m.phone.includes(term) : false;
    return nameMatch || cardMatch || phoneMatch;
  });

  if (filtered.length === 0) {
    listEl.innerHTML = `<div class="dropdown-item-empty">Không tìm thấy thành viên phù hợp</div>`;
    return;
  }

  listEl.innerHTML = filtered.map(m => {
    const isSelected = selectedAssignCardId === m.card_id;
    return `
      <div class="dropdown-item ${isSelected ? 'selected' : ''}" data-card="${escapeHtml(m.card_id)}" data-name="${escapeHtml(m.name)}">
        <div class="item-title">
          <span>${escapeHtml(m.name)}</span>
          <span class="item-card-badge">${escapeHtml(m.card_id)}</span>
        </div>
        <div class="item-sub">
          ${m.phone ? 'SĐT: ' + escapeHtml(m.phone) + ' • ' : ''}Hạn: ${formatDate(m.membership_expiry)}
        </div>
      </div>
    `;
  }).join('');

  // Attach click listener for option selection
  listEl.querySelectorAll('.dropdown-item').forEach(itemEl => {
    itemEl.addEventListener('click', (e) => {
      e.stopPropagation();
      const cardId = itemEl.getAttribute('data-card');
      const memberName = itemEl.getAttribute('data-name');
      selectedAssignCardId = cardId;

      const searchInput = document.getElementById('assign-member-search');
      if (searchInput) {
        searchInput.value = `[${cardId}] ${memberName}`;
      }

      const wrapper = document.getElementById('assign-member-wrapper');
      if (wrapper) {
        wrapper.classList.remove('open');
      }
    });
  });
}

function setupLockerModal() {
  const modal = document.getElementById('locker-modal');
  const btnClose = document.getElementById('btn-close-locker-modal');
  const btnCancel = document.getElementById('btn-cancel-locker-modal');
  const btnForceRelease = document.getElementById('btn-force-release');
  const btnForceAssign = document.getElementById('btn-force-assign');
  const btnToggleBroken = document.getElementById('btn-toggle-broken');
  const wrapper = document.getElementById('assign-member-wrapper');
  const searchInput = document.getElementById('assign-member-search');

  const closeModal = () => {
    modal.classList.remove('active');
    if (wrapper) wrapper.classList.remove('open');
    selectedLocker = null;
    selectedAssignCardId = null;
  };

  btnClose.addEventListener('click', closeModal);
  btnCancel.addEventListener('click', closeModal);

  if (searchInput && wrapper) {
    const openDropdown = () => {
      wrapper.classList.add('open');
      if (searchInput.value.startsWith('[')) {
        searchInput.select();
        renderMemberOptions('');
      } else {
        renderMemberOptions(searchInput.value.trim());
      }
    };

    searchInput.addEventListener('click', openDropdown);
    searchInput.addEventListener('focus', openDropdown);

    searchInput.addEventListener('input', () => {
      selectedAssignCardId = null;
      wrapper.classList.add('open');
      renderMemberOptions(searchInput.value.trim());
    });
  }


  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (wrapper && !wrapper.contains(e.target)) {
      wrapper.classList.remove('open');
    }
  });

  // Force Release
  btnForceRelease.addEventListener('click', async () => {
    if (!selectedLocker) return;
    try {
      await GymTagAPI.forceReleaseLocker(selectedLocker.locker_number);
      showToast(`Đã force giải phóng Locker #${selectedLocker.locker_number}`, 'success');
      closeModal();
      loadLockersData();
      loadOverviewData();
    } catch (e) {
      showToast(`Lỗi: ${e.message}`, 'error');
    }
  });

  // Force Assign
  btnForceAssign.addEventListener('click', async () => {
    if (!selectedLocker) return;
    const cardId = selectedAssignCardId || (searchInput ? searchInput.value.trim() : '');
    if (!cardId) {
      showToast('Vui lòng chọn hoặc nhập Card ID thành viên!', 'error');
      return;
    }
    try {
      await GymTagAPI.forceAssignLocker(selectedLocker.locker_number, cardId);
      showToast(`Đã gán thành viên cho Locker #${selectedLocker.locker_number}`, 'success');
      closeModal();
      loadLockersData();
      loadOverviewData();
    } catch (e) {
      showToast(`Lỗi gán locker: ${e.message}`, 'error');
    }
  });

  // Toggle Broken / Status
  btnToggleBroken.addEventListener('click', async () => {
    if (!selectedLocker) return;
    const currentStatus = selectedLocker.status || (selectedLocker.is_occupied ? 'occupied' : 'vacant');
    const newStatus = currentStatus === 'broken' ? 'vacant' : 'broken';

    try {
      await GymTagAPI.setLockerStatus(selectedLocker.locker_number, newStatus);
      showToast(
        newStatus === 'broken'
          ? `Đã báo hỏng Locker #${selectedLocker.locker_number}`
          : `Đã khôi phục Locker #${selectedLocker.locker_number} về trạng thái Trống`,
        'success'
      );
      closeModal();
      loadLockersData();
      loadOverviewData();
    } catch (e) {
      showToast(`Lỗi cập nhật trạng thái: ${e.message}`, 'error');
    }
  });
}


function openLockerModal(locker) {
  selectedLocker = locker;
  selectedAssignCardId = null;
  const modal = document.getElementById('locker-modal');
  const title = document.getElementById('locker-modal-title');
  const summary = document.getElementById('locker-info-summary');
  const btnForceRelease = document.getElementById('btn-force-release');
  const btnToggleBroken = document.getElementById('btn-toggle-broken');
  const groupForceAssign = document.getElementById('group-force-assign');
  const searchInput = document.getElementById('assign-member-search');
  const wrapper = document.getElementById('assign-member-wrapper');

  title.textContent = `🔐 Quản Lý Locker #${locker.locker_number}`;
  if (searchInput) searchInput.value = '';
  if (wrapper) wrapper.classList.remove('open');

  // Load members for assign dropdown
  GymTagAPI.getMembers()
    .then(members => {
      cachedMembers = members || [];
      renderMemberOptions('');
    })
    .catch(err => {
      console.error('Error fetching members:', err);
    });



  const status = locker.status || (locker.is_occupied ? 'occupied' : 'vacant');

  let statusBadgeHtml = '';

  if (status === 'broken') {
    statusBadgeHtml = `<span class="badge badge-warning">⚠️ Bị hỏng / Bảo trì</span>`;
  } else if (status === 'occupied' || locker.is_occupied) {
    statusBadgeHtml = `<span class="badge badge-denied">🔴 Đang dùng</span>`;
  } else {
    statusBadgeHtml = `<span class="badge badge-granted">🟢 Trống (Sẵn sàng)</span>`;
  }

  const holderInfo = locker.card_id
    ? `Card ID: <code>${escapeHtml(locker.card_id)}</code><br><small style="color:var(--text-muted);">Gán lúc: ${formatTime(locker.assigned_at)}</small>`
    : 'Không có người sử dụng';

  summary.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
      <strong>Locker #${locker.locker_number}</strong>
      ${statusBadgeHtml}
    </div>
    <div style="font-size:0.85rem; color:var(--text-secondary);">
      ${holderInfo}
    </div>
  `;

  // UI state based on locker status
  if (status === 'broken') {
    groupForceAssign.style.display = 'none';
    btnForceRelease.style.display = 'none';
    btnToggleBroken.style.display = 'block';
    btnToggleBroken.className = 'btn btn-primary style-full';
    btnToggleBroken.innerHTML = '🛠️ Đã Sửa Xong (Đưa về trạng thái Trống)';
  } else if (status === 'occupied' || locker.is_occupied) {
    groupForceAssign.style.display = 'none';
    btnForceRelease.style.display = 'block';
    btnToggleBroken.style.display = 'block';
    btnToggleBroken.className = 'btn btn-danger style-full';
    btnToggleBroken.innerHTML = '⚠️ Báo Hỏng / Đánh Dấu Bảo Trì';
  } else {
    groupForceAssign.style.display = 'block';
    btnForceRelease.style.display = 'none';
    btnToggleBroken.style.display = 'block';
    btnToggleBroken.className = 'btn btn-danger style-full';
    btnToggleBroken.innerHTML = '⚠️ Báo Hỏng / Đánh Dấu Bảo Trì';
  }

  modal.classList.add('active');
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
  const occupied = lockers.filter(l => l.is_occupied || l.status === 'occupied').length;
  const broken = lockers.filter(l => l.status === 'broken').length;
  summary.textContent = `${occupied} / ${total} Locker đang dùng` + (broken > 0 ? ` (${broken} hỏng)` : '');

  container.innerHTML = lockers.map(l => {
    const status = l.status || (l.is_occupied ? 'occupied' : 'vacant');
    let statusClass = 'vacant';
    let statusText = 'Trống';

    if (status === 'broken') {
      statusClass = 'broken';
      statusText = 'Hỏng';
    } else if (status === 'occupied' || l.is_occupied) {
      statusClass = 'occupied';
      statusText = 'Đang dùng';
    }

    const cardStr = l.card_id ? escapeHtml(l.card_id) : '-';
    const assignedTimeStr = l.assigned_at ? formatTime(l.assigned_at) : '';

    return `
      <div class="locker-card ${statusClass} admin-clickable" data-locker="${l.locker_number}">
        <div class="locker-title">LOCKER</div>
        <div class="locker-number">#${l.locker_number}</div>
        <div class="locker-status-text">${statusText}</div>
        <div class="locker-holder">
          ${status === 'broken'
            ? '<small style="color:var(--status-warning);">🛠️ Bảo trì</small>'
            : (status === 'occupied' || l.is_occupied
              ? `ID: <code>${cardStr}</code><br><small style="color:var(--text-muted);">${assignedTimeStr}</small>`
              : 'Sẵn sàng')}
        </div>
      </div>
    `;
  }).join('');

  // Attach click listener for opening admin modal on locker click
  container.querySelectorAll('.locker-card.admin-clickable').forEach(cardEl => {
    cardEl.addEventListener('click', () => {
      const lockerNum = parseInt(cardEl.getAttribute('data-locker'), 10);
      const lockerObj = lockers.find(l => l.locker_number === lockerNum);
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

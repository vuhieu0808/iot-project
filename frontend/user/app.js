import { GymTagAPI } from '../shared/js/api.js?v=5.0';
import { formatTime, formatDate, formatDuration, escapeHtml, showToast } from '../shared/js/utils.js?v=5.0';

document.addEventListener('DOMContentLoaded', () => {
  initUserPortal();
});

function initUserPortal() {
  setupAuth();
  setupChangePasswordModal();
}

function setupAuth() {
  const loginSection = document.getElementById('user-login-section');
  const dashboardContainer = document.getElementById('user-dashboard-container');
  const loginForm = document.getElementById('user-login-form');
  const cardIdInput = document.getElementById('user-card-id-input');
  const passwordInput = document.getElementById('user-password-input');
  const errorMsg = document.getElementById('login-error-msg');
  const btnLogout = document.getElementById('btn-user-logout');
  const btnChangePw = document.getElementById('btn-change-password');

  const token = sessionStorage.getItem('gymtag_user_token');

  if (token) {
    loginSection.style.display = 'none';
    dashboardContainer.style.display = 'block';
    if (btnLogout) btnLogout.style.display = 'inline-flex';
    if (btnChangePw) btnChangePw.style.display = 'inline-flex';
    loadUserDashboard();
  } else {
    loginSection.style.display = 'block';
    dashboardContainer.style.display = 'none';
    if (btnLogout) btnLogout.style.display = 'none';
    if (btnChangePw) btnChangePw.style.display = 'none';
  }

  // Handle Login submission
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const cardId = cardIdInput.value.trim();
    const password = passwordInput.value.trim();

    try {
      const res = await GymTagAPI.userLogin(cardId, password);
      sessionStorage.setItem('gymtag_user_token', res.token);
      sessionStorage.setItem('gymtag_user_card_id', res.card_id);

      loginSection.style.display = 'none';
      dashboardContainer.style.display = 'block';
      if (btnLogout) btnLogout.style.display = 'inline-flex';
      if (btnChangePw) btnChangePw.style.display = 'inline-flex';

      errorMsg.style.display = 'none';
      passwordInput.value = '';
      showToast(`Đăng nhập thành công! Chào mừng ${res.name}`, 'success');

      loadUserDashboard();
    } catch (err) {
      errorMsg.textContent = `⚠️ ${err.message || 'Mã thẻ hoặc mật khẩu không chính xác'}`;
      errorMsg.style.display = 'block';
      passwordInput.select();
    }
  });

  // Handle Logout
  if (btnLogout) {
    btnLogout.addEventListener('click', () => {
      sessionStorage.removeItem('gymtag_user_token');
      sessionStorage.removeItem('gymtag_user_card_id');

      loginSection.style.display = 'block';
      dashboardContainer.style.display = 'none';
      btnLogout.style.display = 'none';
      if (btnChangePw) btnChangePw.style.display = 'none';

      showToast('Đã đăng xuất khỏi tài khoản thành viên', 'success');
    });
  }
}

async function loadUserDashboard() {
  try {
    const [profile, history, locker, stats] = await Promise.all([
      GymTagAPI.getUserMeProfile(),
      GymTagAPI.getUserMeHistory(50).catch(() => []),
      GymTagAPI.getUserMeLocker().catch(() => null),
      GymTagAPI.getUserMeStats().catch(() => ({ total_sessions: 0, total_workout_minutes: 0 })),
    ]);

    const bannerName = document.getElementById('banner-user-name');
    if (bannerName) bannerName.textContent = profile.name;

    renderProfile(profile);
    renderLocker(locker);
    renderStats(stats);
    renderHistory(history);
  } catch (err) {
    showToast(`Không thể tải thông tin cá nhân: ${err.message}`, 'error');
    if (err.message.includes('401') || err.message.includes('Unauthorized') || err.message.includes('expired')) {
      sessionStorage.removeItem('gymtag_user_token');
      location.reload();
    }
  }
}

function renderProfile(profile) {
  document.getElementById('m-name').textContent = profile.name;
  document.getElementById('m-card-badge').textContent = `Card ID: ${profile.card_id}`;

  const expiryEl = document.getElementById('m-expiry');
  const statusBadgeEl = document.getElementById('m-status-badge');

  expiryEl.textContent = formatDate(profile.membership_expiry);

  if (profile.is_expired) {
    statusBadgeEl.className = 'badge badge-denied';
    statusBadgeEl.textContent = 'ĐÃ HẾT HẠN';
  } else if (!profile.is_active) {
    statusBadgeEl.className = 'badge badge-warning';
    statusBadgeEl.textContent = 'BỊ KHÓA';
  } else {
    statusBadgeEl.className = 'badge badge-granted';
    statusBadgeEl.textContent = 'ĐANG HOẠT ĐỘNG';
  }
}

function renderLocker(locker) {
  const lockerEl = document.getElementById('m-locker');
  const lockerTimeEl = document.getElementById('m-locker-time');

  if (locker && (locker.is_occupied || locker.status === 'occupied')) {
    lockerEl.textContent = `Locker #${locker.locker_number}`;
    lockerEl.style.color = 'var(--accent-cyan)';
    lockerTimeEl.textContent = locker.assigned_at ? `Gán lúc: ${formatTime(locker.assigned_at)}` : 'Đang giữ';
  } else {
    lockerEl.textContent = 'Chưa đăng ký';
    lockerEl.style.color = 'var(--text-muted)';
    lockerTimeEl.textContent = 'Bạn chưa giữ locker nào';
  }
}

function renderStats(stats) {
  document.getElementById('m-stats-hours').textContent = formatDuration(stats.total_workout_minutes);
  document.getElementById('m-stats-sessions').textContent = `${stats.total_sessions} buổi tập đã hoàn thành`;
}

function renderHistory(logs) {
  const tbody = document.getElementById('user-logs-tbody');
  const badgeEl = document.getElementById('user-logs-badge');
  if (!tbody) return;

  badgeEl.textContent = `${logs.length} lượt quẹt thẻ`;

  if (logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding: 2rem;">Chưa có lượt quẹt thẻ nào ghi nhận cho thẻ này.</td></tr>`;
    return;
  }

  tbody.innerHTML = logs.map(log => {
    const isGranted = log.status === 'granted';
    const badgeClass = isGranted
      ? (log.action === 'checkin' ? 'badge-granted' : 'badge-warning')
      : 'badge-denied';

    const actionText = log.action === 'checkin' ? 'CHECK-IN' : 'CHECK-OUT';
    const statusText = isGranted ? 'CHO PHÉP' : 'TỪ CHỐI';

    return `
      <tr>
        <td>${formatTime(log.timestamp)}</td>
        <td><span class="badge badge-info">${actionText}</span></td>
        <td><span class="badge ${badgeClass}">${statusText}</span></td>
        <td>${formatDuration(log.duration_minutes)}</td>
        <td><small style="color:var(--text-muted);">${escapeHtml(log.reason || '-')}</small></td>
      </tr>
    `;
  }).join('');
}

function setupChangePasswordModal() {
  const modal = document.getElementById('change-pw-modal');
  const btnHeaderPw = document.getElementById('btn-change-password');
  const btnBannerPw = document.getElementById('btn-quick-change-pw');
  const btnClose = document.getElementById('btn-close-pw-modal');
  const btnCancel = document.getElementById('btn-cancel-pw-modal');
  const form = document.getElementById('change-pw-form');
  const oldPwInput = document.getElementById('old-pw-input');
  const newPwInput = document.getElementById('new-pw-input');
  const confirmPwInput = document.getElementById('confirm-pw-input');
  const errorMsg = document.getElementById('change-pw-error-msg');

  const openModal = () => {
    form.reset();
    errorMsg.style.display = 'none';
    modal.classList.add('active');
  };

  const closeModal = () => {
    modal.classList.remove('active');
  };

  if (btnHeaderPw) btnHeaderPw.addEventListener('click', openModal);
  if (btnBannerPw) btnBannerPw.addEventListener('click', openModal);
  if (btnClose) btnClose.addEventListener('click', closeModal);
  if (btnCancel) btnCancel.addEventListener('click', closeModal);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const oldPw = oldPwInput.value.trim();
    const newPw = newPwInput.value.trim();
    const confirmPw = confirmPwInput.value.trim();

    if (newPw !== confirmPw) {
      errorMsg.textContent = '⚠️ Mật khẩu mới và mật khẩu xác nhận không khớp!';
      errorMsg.style.display = 'block';
      confirmPwInput.select();
      return;
    }

    try {
      await GymTagAPI.userChangePassword(oldPw, newPw);
      showToast('Đổi mật khẩu thành công!', 'success');
      closeModal();
    } catch (err) {
      errorMsg.textContent = `⚠️ Lỗi: ${err.message || 'Đổi mật khẩu thất bại'}`;
      errorMsg.style.display = 'block';
    }
  });
}

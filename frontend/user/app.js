import { GymTagAPI } from '../shared/js/api.js?v=3.2';
import { wsClient } from '../shared/js/websocket.js';
import { formatTime, formatDuration, escapeHtml } from '../shared/js/utils.js';

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
});

async function initDashboard() {
  setupWebSocket();
  await loadInitialData();
}

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
      statusTextEl.textContent = 'Mất kết nối (Đang thử lại)';
    }
  });

  // Listen for realtime events from Backend WS
  wsClient.on('checkin_event', (data) => {
    fetchOccupancy();
    fetchLogs();
  });

  wsClient.on('locker_event', (data) => {
    if (data.lockers) {
      renderLockers(data.lockers);
    } else {
      fetchLockers();
    }
  });

  wsClient.on('environment_update', (data) => {
    renderEnvironment(data);
  });

  wsClient.connect();
}

async function loadInitialData() {
  try {
    await Promise.all([
      fetchOccupancy(),
      fetchEnvironment(),
      fetchLockers(),
      fetchLogs()
    ]);
  } catch (e) {
    console.error('Error fetching initial dashboard data:', e);
  }
}

async function fetchOccupancy() {
  try {
    const res = await GymTagAPI.getOccupancy();
    const countEl = document.getElementById('val-occupancy');
    countEl.textContent = res.current_occupancy;
  } catch (e) {
    console.error('Failed to fetch occupancy:', e);
  }
}

async function fetchEnvironment() {
  try {
    const data = await GymTagAPI.getLatestEnvironment();
    renderEnvironment(data);
  } catch (e) {
    console.error('Failed to fetch environment:', e);
  }
}

function renderEnvironment(data) {
  if (!data) return;

  const tempEl = document.getElementById('val-temp');
  const humidityEl = document.getElementById('val-humidity');
  const fanEl = document.getElementById('val-fan');
  const fanIconBg = document.getElementById('fan-icon-bg');

  tempEl.textContent = `${data.temperature.toFixed(1)} °C`;
  humidityEl.textContent = `${data.humidity.toFixed(1)} %`;

  if (data.fan_on) {
    fanEl.textContent = 'ĐANG BẬT';
    fanEl.style.color = 'var(--accent-cyan)';
    fanIconBg.innerHTML = '<span class="spin-fan">🌀</span>';
  } else {
    fanEl.textContent = 'ĐANG TẮT';
    fanEl.style.color = 'var(--text-muted)';
    fanIconBg.innerHTML = '💨';
  }
}

async function fetchLockers() {
  try {
    const lockers = await GymTagAPI.getLockers();
    renderLockers(lockers);
  } catch (e) {
    console.error('Failed to fetch lockers:', e);
  }
}

function renderLockers(lockers) {
  const container = document.getElementById('locker-grid');
  const summaryEl = document.getElementById('locker-count-summary');
  if (!container || !lockers) return;

  const total = lockers.length;
  const vacantCount = lockers.filter(l => l.status === 'vacant' || (!l.is_occupied && l.status !== 'broken')).length;
  const brokenCount = lockers.filter(l => l.status === 'broken').length;
  summaryEl.textContent = `${vacantCount} / ${total} Trống` + (brokenCount > 0 ? ` (${brokenCount} hỏng)` : '');

  if (lockers.length === 0) {
    container.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;">Chưa có dữ liệu locker.</div>`;
    return;
  }

  container.innerHTML = lockers.map(l => {
    const status = l.status || (l.is_occupied ? 'occupied' : 'vacant');
    let statusClass = 'vacant';
    let statusText = 'Trống';
    let holderText = 'Sẵn sàng';

    if (status === 'broken') {
      statusClass = 'broken';
      statusText = 'Hỏng';
      holderText = 'Bảo trì';
    } else if (status === 'occupied' || l.is_occupied) {
      statusClass = 'occupied';
      statusText = 'Đang dùng';
      holderText = 'Đã có người';
    }

    return `
      <div class="locker-card ${statusClass}">
        <div class="locker-title">LOCKER</div>
        <div class="locker-number">#${l.locker_number}</div>
        <div class="locker-status-text">${statusText}</div>
        <div class="locker-holder">${holderText}</div>
      </div>
    `;
  }).join('');
}


async function fetchLogs() {
  try {
    const logs = await GymTagAPI.getCheckLogs(15);
    renderLogs(logs);
  } catch (e) {
    console.error('Failed to fetch check logs:', e);
  }
}

function renderLogs(logs) {
  const tbody = document.getElementById('logs-tbody');
  if (!tbody || !logs) return;

  if (logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">Chưa có lượt quẹt thẻ nào.</td></tr>`;
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
      </tr>
    `;
  }).join('');
}

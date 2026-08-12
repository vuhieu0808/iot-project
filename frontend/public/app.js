import { GymTagAPI } from '../shared/js/api.js?v=4.0';
import { wsClient } from '../shared/js/websocket.js?v=4.0';

document.addEventListener('DOMContentLoaded', () => {
  initPublicDashboard();
});

async function initPublicDashboard() {
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
      statusTextEl.textContent = 'Mất kết nối';
    }
  });

  // Listen for realtime events on Public WS channel
  wsClient.on('occupancy_update', (data) => {
    if (data && data.current_occupancy !== undefined) {
      document.getElementById('val-occupancy').textContent = data.current_occupancy;
    }
  });

  wsClient.on('locker_status_update', (data) => {
    if (data && data.lockers) {
      renderLockers(data.lockers);
    } else {
      fetchLockers();
    }
  });

  wsClient.on('environment_update', (data) => {
    renderEnvironment(data);
  });

  // Connect to public WebSocket stream
  wsClient.connect('/ws/public');
}

async function loadInitialData() {
  try {
    await Promise.all([
      fetchStatus(),
      fetchLockers()
    ]);
  } catch (e) {
    console.error('Error fetching initial public dashboard data:', e);
  }
}

async function fetchStatus() {
  try {
    const statusData = await GymTagAPI.getPublicStatus();
    document.getElementById('val-occupancy').textContent = statusData.current_occupancy;
    renderEnvironment({
      temperature: statusData.temperature,
      humidity: statusData.humidity,
      fan_on: statusData.fan_on
    });
  } catch (e) {
    console.error('Failed to fetch public status:', e);
  }
}

function renderEnvironment(data) {
  if (!data) return;

  const tempEl = document.getElementById('val-temp');
  const humidityEl = document.getElementById('val-humidity');
  const fanEl = document.getElementById('val-fan');
  const fanIconBg = document.getElementById('fan-icon-bg');

  if (data.temperature !== null && data.temperature !== undefined) {
    tempEl.textContent = `${data.temperature.toFixed(1)} °C`;
  } else {
    tempEl.textContent = '-- °C';
  }

  if (data.humidity !== null && data.humidity !== undefined) {
    humidityEl.textContent = `${data.humidity.toFixed(1)} %`;
  } else {
    humidityEl.textContent = '-- %';
  }

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
    const lockers = await GymTagAPI.getPublicLockers();
    renderLockers(lockers);
  } catch (e) {
    console.error('Failed to fetch public lockers:', e);
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

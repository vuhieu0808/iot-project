/**
 * GymTag - Utility Functions
 */

export function formatTime(isoString) {
  if (!isoString) return '-';
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch (e) {
    return isoString;
  }
}

export function formatDate(isoString) {
  if (!isoString) return '-';
  try {
    const date = new Date(isoString);
    return date.toLocaleDateString('vi-VN', { year: 'numeric', month: '2-digit', day: '2-digit' });
  } catch (e) {
    return isoString;
  }
}

export function formatDuration(minutes) {
  if (minutes === null || minutes === undefined) return '-';
  const num = parseFloat(minutes);
  if (isNaN(num)) return '-';
  
  if (num < 1) {
    return `${Math.round(num * 60)} giây`;
  } else if (num < 60) {
    return `${num.toFixed(1)} phút`;
  } else {
    const hrs = Math.floor(num / 60);
    const mins = Math.round(num % 60);
    return `${hrs} giờ ${mins} phút`;
  }
}

export function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icon = type === 'success' ? '✅' : '❌';
  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

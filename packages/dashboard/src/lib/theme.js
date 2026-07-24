const KEY = 'dashboard.theme';

export function readTheme() {
  return localStorage.getItem(KEY) === 'dark' ? 'dark' : 'light';
}

export function saveTheme(theme) {
  localStorage.setItem(KEY, theme);
}

export function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
}

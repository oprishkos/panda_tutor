(function () {
  'use strict';

  // Theme
  const themeKey = 'theme';
  const root = document.documentElement;
  const saved = localStorage.getItem(themeKey) || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  root.setAttribute('data-theme', saved);

  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      const current = root.getAttribute('data-theme') || 'light';
      const next = current === 'light' ? 'dark' : 'light';
      root.setAttribute('data-theme', next);
      localStorage.setItem(themeKey, next);
    });
  }

  // Mobile nav
  const navToggle = document.getElementById('navToggle');
  const nav = document.querySelector('.nav');
  if (navToggle && nav) {
    navToggle.addEventListener('click', function () {
      nav.classList.toggle('open');
    });
  }

  // Toast helper
  window.showToast = function (message, type) {
    type = type || 'info';
    const container = document.getElementById('toast-container');
    if (!container) return;
    const el = document.createElement('div');
    el.className = 'toast toast-' + type;
    el.textContent = message;
    container.appendChild(el);
    setTimeout(function () {
      el.remove();
    }, 4000);
  };

  // Auto-hide flash after 5s
  document.querySelectorAll('.flash').forEach(function (el) {
    setTimeout(function () {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.3s';
      setTimeout(function () { el.remove(); }, 300);
    }, 5000);
  });
})();
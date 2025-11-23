/* ============================================
   THEME.JS - Theme Switching
   ============================================ */
document.addEventListener('DOMContentLoaded', function() {
const html = document.documentElement;
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');if (!themeToggle || !themeIcon) return;// Icons as SVG paths
const moonIcon = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="currentColor"/>';
const sunIcon = '<circle cx="12" cy="12" r="5" fill="currentColor"/><line x1="12" y1="1" x2="12" y2="3" stroke="currentColor" stroke-width="2"/><line x1="12" y1="21" x2="12" y2="23" stroke="currentColor" stroke-width="2"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" stroke="currentColor" stroke-width="2"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" stroke="currentColor" stroke-width="2"/><line x1="1" y1="12" x2="3" y2="12" stroke="currentColor" stroke-width="2"/><line x1="21" y1="12" x2="23" y2="12" stroke="currentColor" stroke-width="2"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" stroke="currentColor" stroke-width="2"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" stroke="currentColor" stroke-width="2"/>';// Check for saved theme preference or system preference
const savedTheme = localStorage.getItem('theme');
const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;// Set initial theme
let currentTheme = savedTheme || (systemPrefersDark ? 'dark' : 'light');
html.setAttribute('data-theme', currentTheme);
updateIcon(currentTheme);// Toggle theme on button click
themeToggle.addEventListener('click', function(e) {
e.preventDefault();
e.stopPropagation();const newTheme = html.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
html.setAttribute('data-theme', newTheme);
localStorage.setItem('theme', newTheme);
updateIcon(newTheme);// Add smooth transition
document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
setTimeout(() => {
  document.body.style.transition = '';
}, 300);
});function updateIcon(theme) {
if (theme === 'dark') {
themeIcon.innerHTML = sunIcon;
} else {
themeIcon.innerHTML = moonIcon;
}
}// Listen for system theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
if (!localStorage.getItem('theme')) {
const newTheme = e.matches ? 'dark' : 'light';
html.setAttribute('data-theme', newTheme);
updateIcon(newTheme);
}
});
});

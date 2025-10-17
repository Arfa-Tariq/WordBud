document.addEventListener('DOMContentLoaded', function () {
  const html = document.documentElement;
  const toggleBtn = document.getElementById('themeToggleBtn');

  // Detect saved preference or system preference
  const savedTheme = localStorage.getItem('theme');
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  if (savedTheme) {
    html.dataset.theme = savedTheme;
  } else {
    html.dataset.theme = systemPrefersDark ? 'dark' : 'light';
  }

  // Toggle theme manually
  toggleBtn.addEventListener('click', function () {
    const newTheme = html.dataset.theme === 'light' ? 'dark' : 'light';
    html.dataset.theme = newTheme;
    localStorage.setItem('theme', newTheme);
  });
});

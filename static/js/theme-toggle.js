function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute("data-theme") || "light";
  const next = current === "light" ? "dark" : "light";
  html.setAttribute("data-theme", next);
  localStorage.setItem("wb-theme", next);
}

document.addEventListener("DOMContentLoaded", () => {
  const saved = localStorage.getItem("wb-theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
});

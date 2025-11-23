/* ============================================
   UI.JS - General UI Interactions
   ============================================ */
document.addEventListener('DOMContentLoaded', function() {
// Mobile Menu Toggle
const mobileToggle = document.getElementById('mobileToggle');
const navMenu = document.getElementById('navMenu');
if (mobileToggle && navMenu) {
mobileToggle.addEventListener('click', function() {
navMenu.classList.toggle('active');
  // Animate icon
  const icon = this.querySelector('svg');
  if (navMenu.classList.contains('active')) {
    icon.innerHTML = '<path d="M6 18L18 6M6 6l12 12"/>';
  } else {
    icon.innerHTML = '<path d="M4 6h16M4 12h16M4 18h16"/>';
  }
});

// Close menu when clicking outside
document.addEventListener('click', function(e) {
  if (!mobileToggle.contains(e.target) && !navMenu.contains(e.target)) {
    navMenu.classList.remove('active');
    const icon = mobileToggle.querySelector('svg');
    icon.innerHTML = '<path d="M4 6h16M4 12h16M4 18h16"/>';
  }
});
}
// Active Nav Link Highlighting
const currentPath = window.location.pathname;
const navLinks = document.querySelectorAll('.wb-navbar-link');
navLinks.forEach(link => {
const href = link.getAttribute('href');
if (href && (href === currentPath || currentPath.startsWith(href))) {
link.classList.add('active');
}
});
// Scroll-based Navbar Shadow
const navbar = document.querySelector('.wb-navbar');
if (navbar) {
window.addEventListener('scroll', function() {
if (window.scrollY > 10) {
navbar.style.boxShadow = 'var(--wb-shadow-md)';
} else {
navbar.style.boxShadow = 'none';
}
});
}
// Animate on Scroll Observer
const animateOnScroll = document.querySelectorAll('.wb-animate-on-scroll');
if (animateOnScroll.length > 0) {
const observer = new IntersectionObserver((entries) => {
entries.forEach(entry => {
if (entry.isIntersecting) {
entry.target.classList.add('wb-visible');
}
});
}, {
threshold: 0.1,
rootMargin: '0px 0px -50px 0px'
});
animateOnScroll.forEach(el => observer.observe(el));
}
// Auto-dismiss alerts after 5 seconds
const alerts = document.querySelectorAll('.wb-alert');
alerts.forEach(alert => {
setTimeout(() => {
alert.style.transition = 'opacity 0.3s';
alert.style.opacity = '0';
setTimeout(() => alert.remove(), 300);
}, 5000);
});
//Smooth Scroll for Anchor Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
anchor.addEventListener('click', function(e) {
const href = this.getAttribute('href');
if (href !== '#' && href !== '#!') {
e.preventDefault();
const target = document.querySelector(href);
if (target) {
target.scrollIntoView({
behavior: 'smooth',
block: 'start'
});
}
}
});
});
// Form Input Focus Effects
const formInputs = document.querySelectorAll('.wb-input, .wb-textarea, .wb-select');
formInputs.forEach(input => {
// Add filled class when input has value
const checkFilled = () => {
if (input.value) {
input.classList.add('wb-filled');
} else {
input.classList.remove('wb-filled');
}
};
input.addEventListener('blur', checkFilled);
input.addEventListener('input', checkFilled);
checkFilled(); // Check on load
});
// Copy to Clipboard Utility
window.copyToClipboard = function(text, button) {
navigator.clipboard.writeText(text).then(() => {
const originalText = button.innerHTML;
button.innerHTML = '✓ Copied!';
button.classList.add('wb-btn-success');
  setTimeout(() => {
    button.innerHTML = originalText;
    button.classList.remove('wb-btn-success');
  }, 2000);
}).catch(err => {
  console.error('Copy failed:', err);
});
};
// Tooltip (simple implementation)
const tooltips = document.querySelectorAll('[data-tooltip]');
tooltips.forEach(el => {
el.addEventListener('mouseenter', function() {
const tooltip = document.createElement('div');
tooltip.className = 'wb-tooltip';
tooltip.textContent = this.getAttribute('data-tooltip');
tooltip.style.cssText = "position: absolute; background: var(--wb-text-primary); color: var(--wb-bg-primary); padding: 0.5rem 0.75rem; border-radius: var(--wb-radius-sm); font-size: var(--wb-text-sm); white-space: nowrap; z-index: 1000; pointer-events: none; opacity: 0; transition: opacity 0.2s;";
  document.body.appendChild(tooltip);
  
  const rect = this.getBoundingClientRect();
  tooltip.style.top = `${rect.top - tooltip.offsetHeight - 8}px`;
  tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;
  
  setTimeout(() => tooltip.style.opacity = '1', 10);
  
  this._tooltip = tooltip;
});

el.addEventListener('mouseleave', function() {
  if (this._tooltip) {
    this._tooltip.style.opacity = '0';
    setTimeout(() => this._tooltip.remove(), 200);
    delete this._tooltip;
  }
});
});
// Keyboard Navigation Enhancement
document.addEventListener('keydown', function(e) {
// ESC to close modals/menus
if (e.key === 'Escape') {
const activeModal = document.querySelector('.wb-modal.active');
if (activeModal) {
activeModal.classList.remove('active');
}
  if (navMenu && navMenu.classList.contains('active')) {
    navMenu.classList.remove('active');
  }
}
});
// Lazy Load Images
if ('IntersectionObserver' in window) {
const lazyImages = document.querySelectorAll('img[data-src]');
const imageObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
      imageObserver.unobserve(img);
    }
  });
});

lazyImages.forEach(img => imageObserver.observe(img));
}
// Print Page Setup
window.addEventListener('beforeprint', function() {
document.body.classList.add('wb-printing');
});
window.addEventListener('afterprint', function() {
document.body.classList.remove('wb-printing');
});
});
// Export utility functions
window.WB = {
copyToClipboard: window.copyToClipboard,
showToast: function(message, type = 'info') {
const toast = document.createElement('div');
toast.className = `wb-toast wb-toast-${type}`;
toast.textContent = message;
toast.style.cssText = "position: fixed; bottom: 2rem; right: 2rem; padding: 1rem 1.5rem; background: var(--wb-bg-primary); border: 1px solid var(--wb-border); border-radius: var(--wb-radius-md); box-shadow: var(--wb-shadow-lg); z-index: 9999; animation: wb-slide-up 0.3s ease-out;";

document.body.appendChild(toast);

setTimeout(() => {
  toast.style.animation = 'wb-fade-out 0.3s ease-out';
  setTimeout(() => toast.remove(), 300);
}, 3000);
}
};

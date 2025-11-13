document.addEventListener('DOMContentLoaded', function() {
  const headers = document.querySelectorAll('.nav-header[data-target]');
  headers.forEach(header => {
    header.addEventListener('click', function() {
      const target = document.getElementById(this.dataset.target);
      const expanded = this.getAttribute('aria-expanded') === 'true';
      this.setAttribute('aria-expanded', !expanded);
      target.classList.toggle('collapsed');
      localStorage.setItem('section-' + this.dataset.sectionId, !expanded);
    });
  });

  document.getElementById('sidebar-toggle-btn')?.addEventListener('click', function() {
    document.getElementById('sidebar').classList.toggle('hidden');
    document.getElementById('main-content').classList.toggle('expanded');
    this.classList.toggle('sidebar-hidden');
  });

  document.getElementById('toggle-all-btn')?.addEventListener('click', function() {
    const submenus = document.querySelectorAll('.nav-submenu');
    const headers = document.querySelectorAll('.nav-header[data-target]');
    const allCollapsed = Array.from(submenus).every(menu => menu.classList.contains('collapsed'));

    if (allCollapsed) {
      // Expand all
      submenus.forEach(menu => menu.classList.remove('collapsed'));
      headers.forEach(header => header.setAttribute('aria-expanded', 'true'));

      // Update button text and icon
      const icon = this.querySelector('i');
      const text = this.querySelector('#toggle-btn-text');
      icon.className = 'fas fa-compress-alt';
      text.textContent = 'Collapse All';
      this.title = 'Collapse All Sections';
    } else {
      // Collapse all
      submenus.forEach(menu => menu.classList.add('collapsed'));
      headers.forEach(header => header.setAttribute('aria-expanded', 'false'));

      // Update button text and icon
      const icon = this.querySelector('i');
      const text = this.querySelector('#toggle-btn-text');
      icon.className = 'fas fa-expand-alt';
      text.textContent = 'Expand All';
      this.title = 'Expand All Sections';
    }
  });

  // Handle active navigation state
  function updateActiveNav() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(item => {
      const itemPath = new URL(item.getAttribute('href'), window.location.origin).pathname;
      if (itemPath === currentPath) {
        item.classList.add('nav-active');
      } else {
        item.classList.remove('nav-active');
      }
    });
  }

  // Update active nav on page load
  updateActiveNav();

  // Update active nav after HTMX navigation
  document.body.addEventListener('htmx:afterSwap', function(event) {
    if (event.detail.target.id === 'main-content') {
      updateActiveNav();
    }
  });
});

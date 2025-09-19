// static/js/admin_navbar.js
// Injects the admin navbar instantly at the top of the body
(function() {
  function injectNavbarIfMissing() {
    if (document.querySelector('nav.navbar')) {
      return; // A navbar already exists on this page
    }
    const wrapper = document.createElement('div');
    wrapper.innerHTML = `
<nav class="navbar navbar-expand-lg navbar-dark app-navbar">
  <div class="container">
    <a class="navbar-brand" href="/">
      <i class="fas fa-user-graduate"></i> Tutor Dashboard
    </a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav me-auto">
        <li class="nav-item"><a class="nav-link" href="/"> <i class="fas fa-tachometer-alt"></i> Dashboard</a></li>
        <li class="nav-item"><a class="nav-link" href="/charts"> <i class="fas fa-chart-bar"></i> Charts</a></li>
        <li class="nav-item"><a class="nav-link" href="/calendar"> <i class="fas fa-calendar-alt"></i> Calendar</a></li>
        <li class="nav-item admin-only"><a class="nav-link" href="/admin/users"> <i class="fas fa-users-cog"></i> Users</a></li>
        <li class="nav-item lead-tutor-only"><a class="nav-link" href="/admin/shifts"> <i class="fas fa-business-time"></i> Shifts</a></li>
        <li class="nav-item admin-only"><a class="nav-link" href="/admin/audit-logs"> <i class="fas fa-history"></i> Audit Logs</a></li>
      </ul>
      <div class="dropdown" style="position: relative; z-index: 1050;">
        <button class="btn btn-outline-light btn-user dropdown-toggle" type="button" data-bs-toggle="dropdown">
          <i class="fas fa-user-circle"></i> <span id="userDisplayName">Loading...</span>
        </button>
        <ul class="dropdown-menu dropdown-menu-end" style="z-index: 1051; position: absolute; right: 0; left: auto; min-width: 200px;">
          <li><h6 class="dropdown-header" id="userEmail">Loading...</h6></li>
          <li><hr class="dropdown-divider"></li>
          <li><a class="dropdown-item" href="/profile"><i class="fas fa-user"></i> Profile</a></li>
          <li><a class="dropdown-item" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
        </ul>
      </div>
    </div>
  </div>
</nav>`;
    const nav = wrapper.firstElementChild;
    document.body.insertBefore(nav, document.body.firstChild);

    // Ensure theme toggle appears if theme switcher loaded before navbar
    if (window.themeSwitcher && typeof window.themeSwitcher.createThemeToggle === 'function') {
      try {
        window.themeSwitcher.createThemeToggle();
        window.themeSwitcher.updateThemeToggle();
      } catch (e) {
        console.warn('Theme toggle injection failed:', e);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectNavbarIfMissing);
  } else {
    injectNavbarIfMissing();
  }

  // Load user data with error handling
  fetch('/api/user-info')
    .then(res => {
      if (!res.ok) {
        throw new Error('User not authenticated');
      }
      return res.json();
    })
    .then(user => {
      if (user && user.email) {
        const displayName = user.full_name || user.email.split('@')[0] || 'User';
        const userEmail = user.email || 'Unknown';
        
        const displayNameEl = document.getElementById('userDisplayName');
        const userEmailEl = document.getElementById('userEmail');
        
        if (displayNameEl) displayNameEl.textContent = displayName;
        if (userEmailEl) userEmailEl.textContent = userEmail;
        
        // Handle role-based visibility (progressive)
        // Normalize role (case-insensitive, spaces -> underscores)
        const role = ((user.role || 'tutor') + '').toLowerCase().replace(/\s+/g, '_');
        // Admin-only visible only to admin
        if (role !== 'admin') {
          document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
        }
        // Manager-only visible to manager and admin
        if (role !== 'admin' && role !== 'manager') {
          document.querySelectorAll('.manager-only').forEach(el => el.style.display = 'none');
        }
        // Lead-tutor-only visible to lead_tutor, manager, admin
        if (role !== 'admin' && role !== 'manager' && role !== 'lead_tutor') {
          document.querySelectorAll('.lead-tutor-only').forEach(el => el.style.display = 'none');
        }

        // If a pre-existing navbar didn't include the Shifts link, add it for eligible roles
        if (role === 'lead_tutor' || role === 'manager' || role === 'admin') {
          let existingShifts = document.querySelector('nav.navbar a.nav-link[href="/admin/shifts"]');
          if (!existingShifts) {
            const navList = document.querySelector('nav.navbar .navbar-nav') || document.querySelector('#navbarNav ul');
            if (navList) {
              const li = document.createElement('li');
              li.className = 'nav-item';
              li.innerHTML = '<a class="nav-link" href="/admin/shifts"> <i class="fas fa-business-time"></i> Shifts</a>';
              navList.appendChild(li);
              existingShifts = li.querySelector('a.nav-link');
            }
          }
          // Ensure it is visible (in case of CSS display:none)
          if (existingShifts) {
            const li = existingShifts.closest('li');
            if (li) li.style.display = '';
          }
        }
      }
    })
    .catch(error => {
      console.log('User not authenticated or error loading user data:', error.message);
      // Set default values for unauthenticated users
      const displayNameEl = document.getElementById('userDisplayName');
      const userEmailEl = document.getElementById('userEmail');
      
      if (displayNameEl) displayNameEl.textContent = 'Guest';
      if (userEmailEl) userEmailEl.textContent = 'Not logged in';
      
      // Hide admin elements for unauthenticated users
      document.querySelectorAll('.admin-only, .manager-only, .lead-tutor-only').forEach(el => el.style.display = 'none');
    });
})(); 
// static/js/admin_navbar.js
// Injects the admin navbar instantly at the top of the body
(function() {
  document.write(`
<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
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
        <li class="nav-item admin-only"><a class="nav-link" href="/admin/audit-logs"> <i class="fas fa-history"></i> Audit Logs</a></li>
        <li class="nav-item admin-only"><a class="nav-link" href="/admin/shifts"> <i class="fas fa-calendar-day"></i> Shifts</a></li>
      </ul>
      <div class="dropdown">
        <button class="btn btn-outline-light dropdown-toggle" type="button" data-bs-toggle="dropdown">
          <i class="fas fa-user-circle"></i> <span id="userDisplayName">Loading...</span>
        </button>
        <ul class="dropdown-menu dropdown-menu-end">
          <li><h6 class="dropdown-header" id="userEmail">Loading...</h6></li>
          <li><hr class="dropdown-divider"></li>
          <li><a class="dropdown-item" href="/profile"><i class="fas fa-user"></i> Profile</a></li>
          <li><a class="dropdown-item" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
        </ul>
      </div>
    </div>
  </div>
</nav>
  `);
  
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
        
        // Handle role-based visibility
        if (user.role && user.role !== 'admin' && user.role !== 'manager') {
          document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
        }
        if (user.role && user.role !== 'admin' && user.role !== 'manager') {
          document.querySelectorAll('.manager-only').forEach(el => el.style.display = 'none');
          document.querySelectorAll('.lead-tutor-only').forEach(el => el.style.display = 'none');
        }
        if (user.role && (user.role === 'tutor' || user.role === 'lead_tutor')) {
          document.querySelectorAll('.admin-only, .manager-only, .lead-tutor-only').forEach(el => el.style.display = 'none');
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
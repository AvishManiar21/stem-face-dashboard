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
          <li><a class="dropdown-item" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
        </ul>
      </div>
    </div>
  </div>
</nav>
  `);
  fetch('/api/user-info')
    .then(res => res.json())
    .then(user => {
      document.getElementById('userDisplayName').textContent = user.full_name || user.email.split('@')[0];
      document.getElementById('userEmail').textContent = user.email;
      if (user.role !== 'admin' && user.role !== 'manager') {
        document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
      }
    });
})(); 
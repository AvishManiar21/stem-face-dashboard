(function() {
  document.body.insertAdjacentHTML('afterbegin', `
<nav class="sticky top-0 z-50 bg-blue-600 dark:bg-blue-900 shadow">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between h-16">
      <div class="flex items-center">
        <a href="/" class="flex items-center text-white text-xl font-bold mr-8">
          <i class="fas fa-user-graduate mr-2"></i> Tutor Dashboard
        </a>
        <div class="hidden md:flex space-x-2">
          <a href="/" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 dark:hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-white transition nav-link" id="nav-dashboard"><i class="fas fa-tachometer-alt mr-1"></i>Dashboard</a>
          <a href="/charts" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 dark:hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-white transition nav-link" id="nav-charts"><i class="fas fa-chart-bar mr-1"></i>Charts</a>
          <a href="/calendar" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 dark:hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-white transition nav-link" id="nav-calendar"><i class="fas fa-calendar-alt mr-1"></i>Calendar</a>
          <a href="/admin/users" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 dark:hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-white transition nav-link admin-only" id="nav-users"><i class="fas fa-users-cog mr-1"></i>Users</a>
          <a href="/admin/audit-logs" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 dark:hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-white transition nav-link admin-only" id="nav-audit"><i class="fas fa-history mr-1"></i>Audit Logs</a>
          <a href="/admin/shifts" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 dark:hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-white transition nav-link admin-only" id="nav-shifts"><i class="fas fa-calendar-day mr-1"></i>Shifts</a>
        </div>
      </div>
      <div class="flex items-center">
        <div class="relative">
          <button class="flex items-center text-white focus:outline-none focus:ring-2 focus:ring-white" id="userDropdownBtn">
            <i class="fas fa-user-circle text-2xl mr-2"></i>
            <span id="userDisplayName" class="font-medium">Loading...</span>
            <svg class="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
          </button>
          <div id="userDropdownMenu" class="hidden absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 ring-1 ring-black ring-opacity-5 z-50">
            <div class="px-4 py-2 text-sm text-gray-700 dark:text-gray-200" id="userEmail">Loading...</div>
            <div class="border-t border-gray-100 dark:border-gray-700"></div>
            <a href="/logout" class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"><i class="fas fa-sign-out-alt mr-2"></i>Logout</a>
          </div>
        </div>
        <button class="md:hidden ml-4 text-white focus:outline-none" id="navbarBurger" aria-label="Open menu">
          <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
        </button>
      </div>
    </div>
    <div class="md:hidden" id="mobileNav" style="display:none;">
      <div class="pt-2 pb-3 space-y-1">
        <a href="/" class="block px-3 py-2 rounded-md text-base font-medium text-white hover:bg-blue-700 dark:hover:bg-blue-800 nav-link" id="mobile-nav-dashboard"><i class="fas fa-tachometer-alt mr-1"></i>Dashboard</a>
        <a href="/charts" class="block px-3 py-2 rounded-md text-base font-medium text-white hover:bg-blue-700 dark:hover:bg-blue-800 nav-link" id="mobile-nav-charts"><i class="fas fa-chart-bar mr-1"></i>Charts</a>
        <a href="/calendar" class="block px-3 py-2 rounded-md text-base font-medium text-white hover:bg-blue-700 dark:hover:bg-blue-800 nav-link" id="mobile-nav-calendar"><i class="fas fa-calendar-alt mr-1"></i>Calendar</a>
        <a href="/admin/users" class="block px-3 py-2 rounded-md text-base font-medium text-white hover:bg-blue-700 dark:hover:bg-blue-800 nav-link admin-only" id="mobile-nav-users"><i class="fas fa-users-cog mr-1"></i>Users</a>
        <a href="/admin/audit-logs" class="block px-3 py-2 rounded-md text-base font-medium text-white hover:bg-blue-700 dark:hover:bg-blue-800 nav-link admin-only" id="mobile-nav-audit"><i class="fas fa-history mr-1"></i>Audit Logs</a>
        <a href="/admin/shifts" class="block px-3 py-2 rounded-md text-base font-medium text-white hover:bg-blue-700 dark:hover:bg-blue-800 nav-link admin-only" id="mobile-nav-shifts"><i class="fas fa-calendar-day mr-1"></i>Shifts</a>
      </div>
    </div>
  </div>
</nav>
  `);

  // User info and admin-only links
  fetch('/api/user-info')
    .then(res => res.json())
    .then(user => {
      document.getElementById('userDisplayName').textContent = user.full_name || user.email.split('@')[0];
      document.getElementById('userEmail').textContent = user.email;
      if (user.role !== 'admin' && user.role !== 'manager') {
        document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
      }
    });
  // Dropdown logic
  setTimeout(function() {
    const userDropdownBtn = document.getElementById('userDropdownBtn');
    const userDropdownMenu = document.getElementById('userDropdownMenu');
    if (userDropdownBtn && userDropdownMenu) {
      userDropdownBtn.addEventListener('click', () => {
        userDropdownMenu.classList.toggle('hidden');
      });
      document.addEventListener('click', (e) => {
        if (!userDropdownBtn.contains(e.target) && !userDropdownMenu.contains(e.target)) {
          userDropdownMenu.classList.add('hidden');
        }
      });
    }
    // Mobile nav logic
    const burger = document.getElementById('navbarBurger');
    const mobileNav = document.getElementById('mobileNav');
    if (burger && mobileNav) {
      burger.addEventListener('click', () => {
        mobileNav.style.display = mobileNav.style.display === 'none' ? 'block' : 'none';
      });
    }
    // Highlight current page
    const path = window.location.pathname;
    const navMap = {
      '/': ['nav-dashboard', 'mobile-nav-dashboard'],
      '/charts': ['nav-charts', 'mobile-nav-charts'],
      '/calendar': ['nav-calendar', 'mobile-nav-calendar'],
      '/admin/users': ['nav-users', 'mobile-nav-users'],
      '/admin/audit-logs': ['nav-audit', 'mobile-nav-audit'],
      '/admin/shifts': ['nav-shifts', 'mobile-nav-shifts']
    };
    Object.entries(navMap).forEach(([route, ids]) => {
      if (path === route) {
        ids.forEach(id => {
          const el = document.getElementById(id);
          if (el) el.classList.add('bg-blue-800', 'dark:bg-blue-700', 'text-white');
        });
      }
    });
  }, 0);
})(); 
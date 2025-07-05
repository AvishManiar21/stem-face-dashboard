// ===== THEME SWITCHER FUNCTIONALITY =====

class ThemeSwitcher {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        // Set initial theme
        this.setTheme(this.currentTheme);
        
        // Create theme toggle button if it doesn't exist
        this.createThemeToggle();
        
        // Add event listeners
        this.addEventListeners();
        
        // Apply theme to all elements
        this.applyThemeToElements();
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        this.currentTheme = theme;
        
        // Update theme toggle button
        this.updateThemeToggle();
        
        // Trigger custom event for other components
        document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
        
        // Add animation class
        document.body.classList.add('theme-transition');
        setTimeout(() => {
            document.body.classList.remove('theme-transition');
        }, 300);
    }

    createThemeToggle() {
        // Check if toggle already exists
        if (document.getElementById('theme-toggle')) return;

        // Create theme toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'theme-toggle';
        toggleBtn.className = 'btn btn-outline-primary theme-toggle-btn';
        toggleBtn.innerHTML = `
            <i class="fas fa-sun light-icon"></i>
            <i class="fas fa-moon dark-icon"></i>
            <span class="theme-text">${this.currentTheme === 'light' ? 'Dark' : 'Light'} Mode</span>
        `;
        toggleBtn.title = `Switch to ${this.currentTheme === 'light' ? 'Dark' : 'Light'} Mode`;

        // Add to navbar
        const navbar = document.querySelector('.navbar-nav');
        if (navbar) {
            const navItem = document.createElement('li');
            navItem.className = 'nav-item';
            navItem.appendChild(toggleBtn);
            navbar.appendChild(navItem);
        }

        // Add to mobile menu if exists
        const mobileMenu = document.querySelector('.navbar-collapse');
        if (mobileMenu) {
            const mobileItem = document.createElement('div');
            mobileItem.className = 'nav-item d-md-none';
            mobileItem.appendChild(toggleBtn.cloneNode(true));
            mobileMenu.appendChild(mobileItem);
        }
    }

    updateThemeToggle() {
        const toggleBtn = document.getElementById('theme-toggle');
        if (!toggleBtn) return;

        const lightIcon = toggleBtn.querySelector('.light-icon');
        const darkIcon = toggleBtn.querySelector('.dark-icon');
        const themeText = toggleBtn.querySelector('.theme-text');

        if (this.currentTheme === 'dark') {
            lightIcon.style.display = 'inline-block';
            darkIcon.style.display = 'none';
            themeText.textContent = 'Light Mode';
            toggleBtn.title = 'Switch to Light Mode';
        } else {
            lightIcon.style.display = 'none';
            darkIcon.style.display = 'inline-block';
            themeText.textContent = 'Dark Mode';
            toggleBtn.title = 'Switch to Dark Mode';
        }
    }

    addEventListeners() {
        // Theme toggle button click
        document.addEventListener('click', (e) => {
            if (e.target.closest('#theme-toggle')) {
                e.preventDefault();
                this.toggleTheme();
            }
        });

        // Keyboard shortcut (Ctrl/Cmd + T)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 't') {
                e.preventDefault();
                this.toggleTheme();
            }
        });

        // System theme preference change
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                if (!localStorage.getItem('theme')) {
                    this.setTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    applyThemeToElements() {
        // Apply theme-specific classes to elements
        const elements = document.querySelectorAll('[data-theme-class]');
        elements.forEach(element => {
            const themeClass = element.getAttribute('data-theme-class');
            if (themeClass) {
                element.classList.add(`${themeClass}-${this.currentTheme}`);
            }
        });

        // Update chart colors if charts exist
        this.updateChartColors();
    }

    updateChartColors() {
        // Update Chart.js colors if charts exist
        if (typeof Chart !== 'undefined') {
            Chart.defaults.color = getComputedStyle(document.documentElement)
                .getPropertyValue('--text-primary');
            
            // Update existing charts
            Chart.instances.forEach(chart => {
                if (chart.config.type === 'line' || chart.config.type === 'bar') {
                    chart.config.options.scales.x.grid.color = getComputedStyle(document.documentElement)
                        .getPropertyValue('--border-color');
                    chart.config.options.scales.y.grid.color = getComputedStyle(document.documentElement)
                        .getPropertyValue('--border-color');
                }
                chart.update('none');
            });
        }
    }
}

// ===== ENHANCED HOVER EFFECTS =====

class HoverEffects {
    constructor() {
        this.init();
    }

    init() {
        this.addCardHoverEffects();
        this.addButtonHoverEffects();
        this.addTableHoverEffects();
        this.addNavHoverEffects();
        this.addFormHoverEffects();
    }

    addCardHoverEffects() {
        const cards = document.querySelectorAll('.card, .kpi-card, .prediction-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', this.handleCardHover.bind(this));
            card.addEventListener('mouseleave', this.handleCardLeave.bind(this));
        });
    }

    handleCardHover(e) {
        const card = e.currentTarget;
        card.style.transform = 'translateY(-8px) scale(1.02)';
        card.style.boxShadow = 'var(--shadow-xl), var(--shadow-glow)';
        
        // Add ripple effect
        this.createRippleEffect(card, e);
    }

    handleCardLeave(e) {
        const card = e.currentTarget;
        card.style.transform = '';
        card.style.boxShadow = '';
    }

    addButtonHoverEffects() {
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(btn => {
            btn.addEventListener('mouseenter', this.handleButtonHover.bind(this));
            btn.addEventListener('mouseleave', this.handleButtonLeave.bind(this));
        });
    }

    handleButtonHover(e) {
        const btn = e.currentTarget;
        btn.style.transform = 'translateY(-2px)';
        btn.style.boxShadow = 'var(--shadow-lg)';
    }

    handleButtonLeave(e) {
        const btn = e.currentTarget;
        btn.style.transform = '';
        btn.style.boxShadow = '';
    }

    addTableHoverEffects() {
        const tableRows = document.querySelectorAll('tbody tr');
        tableRows.forEach(row => {
            row.addEventListener('mouseenter', this.handleRowHover.bind(this));
            row.addEventListener('mouseleave', this.handleRowLeave.bind(this));
        });
    }

    handleRowHover(e) {
        const row = e.currentTarget;
        row.style.backgroundColor = 'var(--primary-color)';
        row.style.color = 'var(--text-light)';
        row.style.transform = 'scale(1.01)';
    }

    handleRowLeave(e) {
        const row = e.currentTarget;
        row.style.backgroundColor = '';
        row.style.color = '';
        row.style.transform = '';
    }

    addNavHoverEffects() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('mouseenter', this.handleNavHover.bind(this));
            link.addEventListener('mouseleave', this.handleNavLeave.bind(this));
        });
    }

    handleNavHover(e) {
        const link = e.currentTarget;
        link.style.transform = 'translateY(-1px)';
        link.style.backgroundColor = 'rgba(102, 126, 234, 0.1)';
    }

    handleNavLeave(e) {
        const link = e.currentTarget;
        link.style.transform = '';
        link.style.backgroundColor = '';
    }

    addFormHoverEffects() {
        const formControls = document.querySelectorAll('.form-control, .form-select');
        formControls.forEach(control => {
            control.addEventListener('focus', this.handleFormFocus.bind(this));
            control.addEventListener('blur', this.handleFormBlur.bind(this));
        });
    }

    handleFormFocus(e) {
        const control = e.currentTarget;
        control.style.transform = 'scale(1.02)';
        control.style.boxShadow = '0 0 0 0.2rem rgba(102, 126, 234, 0.25)';
    }

    handleFormBlur(e) {
        const control = e.currentTarget;
        control.style.transform = '';
        control.style.boxShadow = '';
    }

    createRippleEffect(element, event) {
        const ripple = document.createElement('div');
        ripple.className = 'ripple-effect';
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
            z-index: 0;
        `;

        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';

        element.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
}

// ===== ANIMATION UTILITIES =====

class AnimationUtils {
    static addAnimationClass(element, className, duration = 1000) {
        element.classList.add(className);
        setTimeout(() => {
            element.classList.remove(className);
        }, duration);
    }

    static fadeIn(element, duration = 500) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const opacity = Math.min(progress / duration, 1);
            
            element.style.opacity = opacity;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    static slideIn(element, direction = 'left', duration = 500) {
        const startPosition = direction === 'left' ? '-100%' : '100%';
        element.style.transform = `translateX(${startPosition})`;
        element.style.display = 'block';
        
        let start = null;
        const animate = (timestamp) => {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            const translateX = Math.min(progress / duration, 1);
            
            element.style.transform = `translateX(${translateX * 100 - 100}%)`;
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
}

// ===== CSS ANIMATIONS =====

const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }

    .theme-transition {
        transition: all 0.3s ease;
    }

    .theme-toggle-btn {
        position: relative;
        overflow: hidden;
        border-radius: var(--radius-pill);
        padding: var(--spacing-sm) var(--spacing-md);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all var(--transition-normal);
    }

    .theme-toggle-btn:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }

    .theme-toggle-btn i {
        margin-right: var(--spacing-sm);
        transition: all var(--transition-normal);
    }

    .theme-toggle-btn:hover i {
        transform: rotate(180deg);
    }

    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }

    .slide-in-left {
        animation: slideInFromLeft 0.6s ease-out;
    }

    .slide-in-right {
        animation: slideInFromRight 0.6s ease-out;
    }

    .zoom-in {
        animation: zoomIn 0.5s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes slideInFromLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes slideInFromRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes zoomIn {
        from {
            opacity: 0;
            transform: scale(0.9);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
`;
document.head.appendChild(style);

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme switcher
    window.themeSwitcher = new ThemeSwitcher();
    
    // Initialize hover effects
    window.hoverEffects = new HoverEffects();
    
    // Add animation classes to elements on load
    const animatedElements = document.querySelectorAll('.card, .kpi-card, .prediction-card');
    animatedElements.forEach((element, index) => {
        setTimeout(() => {
            AnimationUtils.addAnimationClass(element, 'fade-in');
        }, index * 100);
    });
    
    console.log('🎨 Theme switcher and hover effects initialized!');
});

// ===== EXPORT FOR MODULE USAGE =====

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ThemeSwitcher, HoverEffects, AnimationUtils };
} 
// Global error handler for better error reporting
window.addEventListener('error', function(event) {
    console.error('Global error caught:', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
    });
    
    // Don't show error alerts to users in production
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('Development mode - errors logged above');
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault(); // Prevent the default browser behavior
});

// Override console.error to add more context
const originalConsoleError = console.error;
console.error = function(...args) {
    // Add timestamp and stack trace for better debugging
    const timestamp = new Date().toISOString();
    const stackTrace = new Error().stack;
    
    originalConsoleError.call(console, `[${timestamp}]`, ...args);
    if (args.length > 0 && typeof args[0] === 'string' && args[0].includes('Error')) {
        originalConsoleError.call(console, 'Stack trace:', stackTrace);
    }
};

console.log('Error handler initialized'); 
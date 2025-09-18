// js/config.js - Configuration management for Global Peds Reading Room
// Centralized configuration with environment detection and fallback to production settings

/**
 * Application configuration object
 * Automatically detects environment and provides appropriate URLs
 */
const APP_CONFIG = {
    // Environment detection
    environment: {
        isLocalDevelopment() {
            const hostname = window.location.hostname;
            return hostname === 'localhost' || hostname === '127.0.0.1';
        },
        
        getCurrentEnvironment() {
            return this.isLocalDevelopment() ? 'development' : 'production';
        }
    },
    
    // API Configuration
    api: {
        getBaseUrl() {
            if (APP_CONFIG.environment.isLocalDevelopment()) {
                return 'http://127.0.0.1:8000/api';
            }
            // Production/beta fallback - use relative path
            return '/api';
        }
    },
    
    // DICOM Viewer Configuration
    dicom: {
        getViewerUrl() {
            if (APP_CONFIG.environment.isLocalDevelopment()) {
                return 'http://localhost:8042/ohif/viewer';
            }
            // Production/beta fallback - use same hostname with port 8053
            return `${window.location.protocol}//${window.location.hostname}:8053/ohif/viewer`;
        }
    },
    
    // Placeholder for future configuration options
    // This structure makes it easy to add settings like DEBUG_MODE later
    features: {
        // Future feature flags can be added here
        // debugMode: APP_CONFIG.environment.isLocalDevelopment(),
        // enableAnalytics: !APP_CONFIG.environment.isLocalDevelopment()
    }
};

// Make configuration available globally
window.APP_CONFIG = APP_CONFIG;
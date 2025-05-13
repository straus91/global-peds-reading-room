// Create a component initialization system (in a new file like components.js)
const Components = {
    // Store initialized components to prevent duplicates
    initialized: new Set(),
    
    // Initialize component if not already done
    init(componentId, initFunction) {
        if (this.initialized.has(componentId)) {
            console.log(`Component ${componentId} already initialized`);
            return;
        }
        
        try {
            initFunction();
            this.initialized.add(componentId);
            console.log(`Component ${componentId} initialized`);
        } catch (error) {
            console.error(`Failed to initialize ${componentId}:`, error);
        }
    },
    
    // Reset a component to be initialized again
    reset(componentId) {
        this.initialized.delete(componentId);
    }
};

// Example usage in admin-users.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize user management only if on the correct page
    if (window.location.pathname.includes('manage-users.html')) {
        Components.init('manage-users', initManageUsersPage);
    }
});
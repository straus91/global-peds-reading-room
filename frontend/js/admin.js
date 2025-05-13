// frontend/js/admin.js - Admin panel core script

// This script assumes api.js is loaded first in admin HTML pages.

document.addEventListener('DOMContentLoaded', async () => {
    console.log("[AdminJS] DOMContentLoaded. Checking admin authentication...");
    // checkAdminAuth will handle redirection if not authenticated or not an admin.
    // It returns true if authentication is successful and user is an admin.
    const isAdminAuthenticated = await checkAdminAuth();

    if (isAdminAuthenticated) {
        // Only proceed if checkAdminAuth confirmed admin status and didn't redirect.
        console.log("[AdminJS] Admin authenticated. Initializing admin app...");
        initAdminApp(); // Initialize common admin UI elements (modals, logout, etc.)

        // Trigger page-specific initialization if the function exists.
        // Each admin page's JS file (e.g., admin-case-edit.js) should define this function.
        if (typeof window.initializeCurrentAdminPage === 'function') {
            console.log("[AdminJS] Calling page-specific initializer: window.initializeCurrentAdminPage()");
            try {
                await window.initializeCurrentAdminPage(); // Make it awaitable if page init is async
            } catch (pageInitError) {
                console.error("[AdminJS] Error during page-specific initialization:", pageInitError);
                showToast("Error initializing page components. Some features may not work.", "error");
            }
        } else {
            console.log("[AdminJS] No page-specific initializer (window.initializeCurrentAdminPage) found for this page.");
        }
    } else {
        console.log("[AdminJS] Admin authentication failed or user is not an admin. Redirection should have occurred.");
        // No further action needed here as checkAdminAuth handles redirection.
    }
});

/**
 * Checks if the user is authenticated AND is an admin.
 * 1. Checks for an access token.
 * 2. Verifies token by fetching user data from /users/me/.
 * 3. Checks the is_admin flag from the fetched user data.
 * 4. Redirects to login if not logged in, or to main site if not an admin.
 * @returns {Promise<boolean>} True if authenticated as admin, false otherwise (and redirection will occur).
 */async function checkAdminAuth() {
    const tokens = getAuthTokens();

    if (!tokens || !tokens.accessToken) {
        console.log("[AdminJS - checkAdminAuth] No access token found. Redirecting to login.");
        // Use consistent path resolution
        window.location.href = getLoginPath();
        return false;
    }

    try {
        const userData = await apiRequest('/users/me/');

        if (userData && userData.id) {
            if (userData.is_admin === true) {
                console.log("[AdminJS - checkAdminAuth] Admin user verified:", userData.username);
                sessionStorage.setItem('user', JSON.stringify({
                    id: userData.id,
                    name: `${userData.first_name || ''} ${userData.last_name || ''}`.trim() || userData.username,
                    email: userData.email,
                    role: userData.profile?.role || 'Admin',
                    isAdmin: true
                }));
                updateAdminUI();
                return true;
            } else {
                console.warn("[AdminJS - checkAdminAuth] User is authenticated but not an admin. Redirecting to main site.");
                showToast("Access Denied: You do not have administrator privileges.", "error");
                window.location.href = getMainPath();
                return false;
            }
        } else {
            console.error("[AdminJS - checkAdminAuth] Invalid user data received from API, or user ID missing.");
            throw new Error("Invalid user data from API.");
        }
    } catch (error) {
        console.error("[AdminJS - checkAdminAuth] Authentication check failed:", error.status, error.message, error.data);
        clearAuthTokens();
        sessionStorage.removeItem('user');
        showToast("Session expired or invalid. Please log in again.", "error");
        window.location.href = getLoginPath();
        return false;
    }
}
function getLoginPath() {
    // Check if we're in admin directory
    const currentPath = window.location.pathname;
    if (currentPath.includes('/admin/')) {
        return '../login.html';
    }
    return 'login.html';
}

function getMainPath() {
    // Check if we're in admin directory
    const currentPath = window.location.pathname;
    if (currentPath.includes('/admin/')) {
        return '../index.html';
    }
    return 'index.html';
}


async function adminLogout() {
    console.log("[AdminJS] Logging out admin...");
    clearAuthTokens(); // From api.js - clears localStorage
    sessionStorage.removeItem('user'); // Clear any session-stored user info
    sessionStorage.removeItem('adminWelcomeToastShown'); // Reset welcome toast flag
    showToast("You have been logged out.", "success");
    
    // Build absolute path to login page
    const origin = window.location.origin;
    const pathToFrontend = window.location.pathname.substring(0, window.location.pathname.indexOf('/frontend/') + '/frontend/'.length);
    window.location.href = origin + pathToFrontend + 'login.html';
}
/**
 * Initializes common admin application UI components like modals, tabs, etc.
 * Also sets up global handlers like logout.
 */
function initAdminApp() {
    // Global toast function (ensure it's robust)
    if (!window.showToast) {
        window.showToast = function(message, type = 'info', duration = 3000) {
            const toastContainer = document.getElementById('toastContainer');
            if (!toastContainer) {
                console.warn('Toast container #toastContainer not found in HTML. Using alert as fallback.');
                alert(`Toast (${type}): ${message}`);
                return;
            }
            const toast = document.createElement('div');
            toast.className = `toast ${type}`; // Assumes CSS for .toast and .toast.success, .toast.error etc.
            toast.textContent = message;
            toastContainer.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0'; // Start fade out
                setTimeout(() => toast.remove(), 500); // Remove after fade
            }, duration);
        };
    }
    // Global loading overlay function
     if (!window.showLoading) {
        window.showLoading = function(show, message = 'Loading...') {
            let loadingOverlay = document.getElementById('loadingOverlay');
            if (!loadingOverlay && show) { // Create if doesn't exist and needs to be shown
                loadingOverlay = document.createElement('div');
                loadingOverlay.id = 'loadingOverlay';
                loadingOverlay.style.cssText = 'display: flex; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.6); z-index: 2000; justify-content: center; align-items: center; color: white; font-size: 1.5em; text-align: center;';
                const msgDiv = document.createElement('div');
                msgDiv.className = 'loading-message';
                msgDiv.style.cssText = 'background: #2c3e50; padding: 25px 35px; border-radius: 8px; box-shadow: 0 0 15px rgba(0,0,0,0.5);';
                loadingOverlay.appendChild(msgDiv);
                document.body.appendChild(loadingOverlay);
            }
            if (loadingOverlay) {
                const msgDiv = loadingOverlay.querySelector('.loading-message');
                if (msgDiv) msgDiv.textContent = message;
                loadingOverlay.style.display = show ? 'flex' : 'none';
            }
        };
    }


    // Initialize common UI components if they exist on the page
    initModals();       // For any modals defined in admin HTML
    initTabs();         // For any tab structures
    initTableSelection(); // For tables with selectable rows

    // Display a welcome message once per session perhaps
    const userString = sessionStorage.getItem('user');
    if (userString && !sessionStorage.getItem('adminWelcomeToastShown')) {
        try {
            const user = JSON.parse(userString);
            showToast(`Welcome back to the admin panel, ${user.name || 'Admin'}!`, 'success');
            sessionStorage.setItem('adminWelcomeToastShown', 'true');
        } catch(e) { console.error("Error parsing user for welcome toast", e); }
    }
}

/**
 * Updates admin UI elements (e.g., username in header, logout link).
 */
function updateAdminUI() {
    const userString = sessionStorage.getItem('user');
    if (!userString) return;

    try {
        const user = JSON.parse(userString);
        const userNameElement = document.querySelector('.user-menu span');
        if (userNameElement) {
            userNameElement.textContent = user.name || 'Administrator';
        }

        const logoutLink = document.getElementById('logoutLink');
        if (logoutLink) {
            logoutLink.removeEventListener('click', handleAdminLogoutClick); // Prevent duplicate listeners
            logoutLink.addEventListener('click', handleAdminLogoutClick);
        }

        const profileLink = document.getElementById('profileLink');
        if (profileLink) {
            profileLink.removeEventListener('click', handleAdminProfileClick);
            profileLink.addEventListener('click', handleAdminProfileClick);
        }
    } catch (e) {
        console.error("Error updating admin UI with user data:", e);
    }
}

function handleAdminLogoutClick(e) {
    e.preventDefault();
    adminLogout();
}

function handleAdminProfileClick(e) {
    e.preventDefault();
    showToast('Admin profile page is not yet implemented.', 'info');
    // Example: window.location.href = 'profile.html';
}

async function adminLogout() {
    console.log("[AdminJS] Logging out admin...");
    // Optional: Call a backend logout endpoint if it exists and handles server-side session/token invalidation.
    // try {
    //     await apiRequest('/auth/logout/', { method: 'POST' }); // Example endpoint
    //     console.log("[AdminJS] Backend logout successful.");
    // } catch (error) {
    //     console.error("[AdminJS] Backend logout failed (token might already be invalid):", error);
    // } finally {
        clearAuthTokens(); // From api.js - clears localStorage
        sessionStorage.removeItem('user'); // Clear any session-stored user info
        sessionStorage.removeItem('adminWelcomeToastShown'); // Reset welcome toast flag
        showToast("You have been logged out.", "success");
        // Redirect to login page, ensuring correct relative path
        window.location.href = '../login.html'; // Assumes admin pages are in an 'admin' subdirectory
    // }
}

// --- Common UI Component Initializers ---
// These functions are called by initAdminApp if relevant components are on the page.

function initModals() {
    const modals = document.querySelectorAll('.modal');
    if (modals.length === 0) return;

    modals.forEach(modal => {
        // Close on clicking the close button (typically an 'x')
        const closeButtons = modal.querySelectorAll('.close-modal, [data-dismiss-modal]');
        closeButtons.forEach(closeBtn => {
            const targetModalId = closeBtn.dataset.dismissModal || modal.id;
            closeBtn.addEventListener('click', () => closeModal(targetModalId));
        });

        // Close on clicking the modal backdrop (outside the .modal-content)
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                closeModal(modal.id);
            }
        });
    });

    // Global ESC key to close any active modal
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active, .modal[style*="display: flex"], .modal[style*="display: block"]');
            if (activeModal) {
                closeModal(activeModal.id);
            }
        }
    });
    console.log("[AdminJS] Modal listeners initialized.");
}

// Global function to open a specific modal by ID
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        // Ensure no other modals are active first for cleaner UI
        // document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
        modal.style.display = 'flex'; // Or 'block', depending on your modal CSS for visibility
        modal.classList.add('active'); // If using class-based visibility
        console.log(`[AdminJS] Modal opened: #${modalId}`);
    } else {
        console.warn(`[AdminJS] Modal with ID "${modalId}" not found.`);
    }
}

// Global function to close a specific modal by ID
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
        console.log(`[AdminJS] Modal closed: #${modalId}`);
    } else {
        // console.warn(`[AdminJS] Attempted to close non-existent modal: #${modalId}`);
    }
}


function initTabs() {
    const tabContainers = document.querySelectorAll('.admin-tabs');
    if (tabContainers.length === 0) return;

    tabContainers.forEach(container => {
        const tabs = container.querySelectorAll('.tab');
        const tabContentContainer = container.nextElementSibling; // Assumes content is immediate sibling

        if (!tabContentContainer || !tabContentContainer.classList.contains('tab-content-container')) {
            // Fallback if direct sibling is not the container (e.g. for manage-templates.html structure)
            const pageContentArea = container.closest('.admin-content');
            if (!pageContentArea) return;
        }
        
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const targetTabContentId = this.dataset.tab; // e.g., "template-list" or "create-template"
                
                tabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                // Find all tab content sections related to THIS tab group and hide them
                let contentParent = this.closest('.admin-content'); // Find the parent that holds all tab contents
                if(contentParent){
                    contentParent.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
                    // Show the target content
                    const activeContent = contentParent.querySelector(`#${targetTabContentId}, .tab-content[data-tab-content="${targetTabContentId}"]`);
                    if (activeContent) {
                        activeContent.classList.add('active');
                    } else {
                        // Fallback for older structure in manage-templates.html where tab-content IDs match data-tab
                        const fallbackContent = document.getElementById(targetTabContentId + 'Container') || document.getElementById(targetTabContentId);
                        if(fallbackContent) fallbackContent.classList.add('active');
                    }
                }
                // Specific logic for manage-templates.html if needed
                if (window.location.pathname.includes('manage-templates.html') && typeof TemplateFormManager !== 'undefined') {
                    if (targetTabContentId === 'create-template' && !templatesState.currentEditTemplateId) {
                        TemplateFormManager.resetForm();
                    } else if (targetTabContentId === 'template-list') {
                        TemplateFormManager.resetForm(); // Reset form when switching away
                    }
                }


            });
        });
        // Activate the first tab by default if no tab is active
        if (tabs.length > 0 && !container.querySelector('.tab.active')) {
            tabs[0].click();
        }
    });
    console.log("[AdminJS] Tab listeners initialized.");
}


function initTableSelection() {
    // This function is a placeholder. Actual table selection logic (like "select all" checkboxes)
    // is often page-specific due to different table structures and data types.
    // Page-specific JS files (e.g., admin-users.js, admin-cases.js) should handle
    // their own table selection logic and call a global updateBulkActionsState if it exists.
    // Example:
    // const selectAllCheckbox = document.getElementById('selectAllCases');
    // if (selectAllCheckbox) { /* ... add listeners ... */ }
    console.log("[AdminJS] Table selection initialization (placeholder - page-specific JS should handle).");
}

// Global helper to get selected IDs from checkboxes with a specific class (if needed globally)
// function getSelectedIds(checkboxSelector) {
//     return Array.from(document.querySelectorAll(`${checkboxSelector}:checked`))
//                 .map(cb => cb.getAttribute('data-id'));
// }

// Global helper to update bulk action buttons (if a common pattern exists)
// function updateBulkActionsState(type, selectedCount) {
//     const bulkActionsDiv = document.querySelector(`.bulk-actions[data-type="${type}"]`); // Requires data-type on bulk-actions div
//     if (!bulkActionsDiv) return;
//     // ... logic to enable/disable buttons ...
// }

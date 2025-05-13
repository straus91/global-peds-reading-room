// js/admin-users.js - User management functionality for the admin panel

// Global variable to store fetched user data (for client-side filtering/searching)
let allUsersData = [];
let currentFilters = { role: '', status: '', search: '' };
let currentTab = 'all-users'; // To filter based on active tab

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize user management functions if on the correct page
    if (window.location.pathname.includes('manage-users.html')) {
        initManageUsersPage();
    }
});

// Check API connection before proceeding
async function checkApiConnection() {
    const apiUrl = `${API_CONFIG.getBaseUrl()}/users/me/`;
    try {
        console.log("Testing API connection to:", apiUrl);
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: { 
                'Accept': 'application/json',
                // Include auth token if available
                ...(getAuthTokens()?.accessToken ? 
                    {'Authorization': `Bearer ${getAuthTokens().accessToken}`} : {})
            }
        });
        
        console.log("API connection successful! Status:", response.status);
        if (!response.ok) {
            console.warn("API responded with non-OK status:", response.status);
        }
        return response.ok;
    } catch (error) {
        console.error("API connection failed:", error);
        showConnectionError(error);
        return false;
    }
}

// Show connection error in the UI
function showConnectionError(error) {
    const tableBody = document.getElementById('usersTable')?.querySelector('tbody');
    if (tableBody) {
        const errorMessage = error.message || "Unknown error";
        tableBody.innerHTML = `
            <tr>
                <td colspan="10" style="text-align:center; padding: 20px;">
                    <div style="color: #721c24; background-color: #f8d7da; padding: 15px; border-radius: 4px; text-align: left;">
                        <h3>Connection Error</h3>
                        <p>Could not connect to the API server: <code>${API_CONFIG.getBaseUrl()}</code></p>
                        <p>Error message: <code>${errorMessage}</code></p>
                        <p>Please check:</p>
                        <ul>
                            <li>Your backend server is running at the correct address</li>
                            <li>The API URL is correct (currently set to: <code>${API_CONFIG.getBaseUrl()}</code>)</li>
                            <li>Your network connection is working</li>
                            <li>CORS is properly configured on your backend</li>
                        </ul>
                        <button onclick="window.location.reload()" class="btn">Retry</button>
                    </div>
                </td>
            </tr>
        `;
    }
}

// Initialize Manage Users page
async function initManageUsersPage() {
    console.log("Initializing Manage Users Page...");
    
    // Check API connection before proceeding
    const isConnected = await checkApiConnection();
    if (!isConnected) {
        console.log("API connection check failed - stopping initialization");
        return;
    }
    
    // Setup Tabs
    setupTabs();
    
    // Setup filters and search
    setupFilters();
    
    // Setup bulk actions
    setupBulkActions();
    
    // Setup table selections
    setupTableSelections();
    
    // Fetch initial user data
    await fetchAndRenderUsers();
    
    // Setup pagination
    setupPagination();
}

// Setup tabs
function setupTabs() {
    const tabs = document.querySelectorAll('.admin-tabs .tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Visual tab selection
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Store the selected tab
            const previousTab = currentTab;
            currentTab = this.getAttribute('data-tab');
            console.log(`Tab changed from ${previousTab} to ${currentTab}`);
            
            // Show loading indicator
            showTabLoading();
            
            // Apply filters with slight delay to allow UI update
            setTimeout(() => {
                applyFiltersAndRender();
            }, 50);
        });
    });
    
    // Add spinner animation if needed
    if (!document.querySelector('style#spin-animation')) {
        const styleEl = document.createElement('style');
        styleEl.id = 'spin-animation';
        styleEl.textContent = `
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(styleEl);
    }
}

// Show loading indicator when changing tabs
function showTabLoading() {
    const tableBody = document.getElementById('usersTable')?.querySelector('tbody');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="10" style="text-align:center; padding: 20px;">
                    <div class="loading-indicator">
                        <div class="spinner" style="border: 3px solid rgba(0,0,0,0.1); border-radius: 50%; border-top-color: #4A86E8; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto 10px;"></div>
                        <p>Loading ${currentTab.replace('-', ' ')}...</p>
                    </div>
                </td>
            </tr>
        `;
    }
}

// Setup filters and search
function setupFilters() {
    const filterInputs = document.querySelectorAll('#roleFilter, #statusFilter');
    filterInputs.forEach(input => {
        input.addEventListener('change', () => {
            currentFilters[input.id.replace('Filter', '')] = input.value;
            console.log("Filter changed:", input.id, input.value);
            applyFiltersAndRender();
        });
    });
    
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('userSearch');
    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', () => {
            currentFilters.search = searchInput.value.trim().toLowerCase();
            applyFiltersAndRender();
        });
        searchInput.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                currentFilters.search = searchInput.value.trim().toLowerCase();
                applyFiltersAndRender();
            }
        });
    }
}

// Setup bulk action buttons
function setupBulkActions() {
    const bulkApproveBtn = document.getElementById('bulkApproveBtn');
    if (bulkApproveBtn) {
        bulkApproveBtn.removeEventListener('click', handleBulkApprove);
        bulkApproveBtn.addEventListener('click', handleBulkApprove);
    }

    const bulkDeactivateBtn = document.getElementById('bulkDeactivateBtn');
    if (bulkDeactivateBtn) {
        bulkDeactivateBtn.removeEventListener('click', handleBulkDeactivate);
        bulkDeactivateBtn.addEventListener('click', handleBulkDeactivate);
    }

    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.removeEventListener('click', handleBulkDelete);
        bulkDeleteBtn.addEventListener('click', handleBulkDelete);
    }

    // Setup confirm delete handler
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.removeEventListener('click', handleConfirmDelete);
        confirmDeleteBtn.addEventListener('click', handleConfirmDelete);
    }
}

// Setup table selections
function setupTableSelections() {
    // Set up select all checkbox
    const selectAllUsers = document.getElementById('selectAllUsers');
    if (selectAllUsers) {
        selectAllUsers.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.user-select');
            checkboxes.forEach(checkbox => checkbox.checked = this.checked);
            updateBulkActionsState(this.checked ? checkboxes.length : 0);
        });
    }

    // Handle individual checkbox changes using event delegation
    document.addEventListener('change', function(e) {
        if (e.target.matches('.user-select')) {
            const selectedCount = document.querySelectorAll('.user-select:checked').length;
            const totalCount = document.querySelectorAll('.user-select').length;
            
            // Update the "select all" checkbox
            const selectAllUsers = document.getElementById('selectAllUsers');
            if (selectAllUsers) {
                selectAllUsers.checked = selectedCount === totalCount && totalCount > 0;
            }
            
            updateBulkActionsState(selectedCount);
        }
    });
}

// Update bulk action buttons state
function updateBulkActionsState(selectedCount) {
    console.log(`Updating bulk actions state: ${selectedCount} users selected`);
    
    // Update the selected count text
    const countDisplay = document.querySelector('.selected-count');
    if (countDisplay) {
        countDisplay.textContent = `${selectedCount} user${selectedCount !== 1 ? 's' : ''} selected`;
    }
    
    // Enable/disable bulk action buttons
    const bulkApproveBtn = document.getElementById('bulkApproveBtn');
    const bulkDeactivateBtn = document.getElementById('bulkDeactivateBtn');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    
    if (bulkApproveBtn) bulkApproveBtn.disabled = selectedCount === 0;
    if (bulkDeactivateBtn) bulkDeactivateBtn.disabled = selectedCount === 0;
    if (bulkDeleteBtn) bulkDeleteBtn.disabled = selectedCount === 0;
}

// Setup pagination
function setupPagination() {
    document.querySelectorAll('.pagination-btn, .pagination-page').forEach(btn => {
        btn.removeEventListener('click', handlePaginationClick);
        btn.addEventListener('click', handlePaginationClick);
    });
}

// Fetch users from the API
async function fetchUsersFromAPI(apiUrl = '/admin/users/') {
    console.log("Fetching users from:", apiUrl);
    showLoadingIndicator(true);
    
    try {
        const data = await apiRequest(apiUrl);
        console.log("API Response:", data);
        
        if (data && Array.isArray(data.results)) {
            console.log(`Received ${data.results.length} users from API.`);
            allUsersData = data.results;
            updatePaginationControls(data.count, data.next, data.previous);
            return data.results;
        } else {
            console.error("Invalid API response structure:", data);
            showToast("Error: Could not parse user data from server.", "error");
            allUsersData = [];
            updatePaginationControls(0, null, null);
            return [];
        }
    } catch (error) {
        console.error("Failed to fetch users:", error);
        showToast(`Error fetching users: ${error.message}`, "error");
        allUsersData = [];
        updatePaginationControls(0, null, null);
        return [];
    } finally {
        showLoadingIndicator(false);
    }
}

// Show/Hide Loading Indicator
function showLoadingIndicator(show) {
    const tableBody = document.getElementById('usersTable')?.querySelector('tbody');
    if (!tableBody) return;
    
    if (show) {
        tableBody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 20px;">Loading users...</td></tr>';
    }
}

// Render the users table
function renderUsersTable(users) {
    const tableBody = document.getElementById('usersTable')?.querySelector('tbody');
    if (!tableBody) {
        console.error("Cannot render users: Table body not found.");
        return;
    }

    tableBody.innerHTML = '';

    if (!Array.isArray(users)) {
        console.error("Cannot render users: Input data is not an array.", users);
        tableBody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 20px;">Error displaying users.</td></tr>';
        return;
    }

    if (users.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 20px;">No users found matching criteria.</td></tr>';
        return;
    }

    users.forEach(user => {
        if (!user || typeof user !== 'object') {
            console.warn("Skipping invalid user data:", user);
            return;
        }
        
        const profile = user.profile || {};
        
        const row = document.createElement('tr');
        row.setAttribute('data-user-id', user.id);

        // Determine status class and text
        let statusClass = 'inactive';
        let statusText = 'Inactive';
        const approvalStatus = profile.approval_status;
        const isActive = user.is_active;

        if (approvalStatus === 'pending') {
            statusClass = 'pending';
            statusText = 'Pending';
        } else if (approvalStatus === 'active' && isActive === true) {
            statusClass = 'active';
            statusText = 'Active';
        }

        // Format joined date
        const joinedDate = user.date_joined ? new Date(user.date_joined).toLocaleDateString() : 'N/A';

        row.innerHTML = `
            <td><input type="checkbox" class="user-select" data-id="${user.id}"></td>
            <td>${user.id}</td>
            <td>${user.first_name || ''} ${user.last_name || ''}</td>
            <td>${user.email || 'N/A'}</td>
            <td>${profile.role || 'N/A'}</td>
            <td>${profile.institution || 'N/A'}</td>
            <td>${profile.country || 'N/A'}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>${joinedDate}</td>
            <td class="actions-cell">
                <button class="action-btn view-btn" data-id="${user.id}" title="View User"><span>👁️</span></button>
                ${approvalStatus === 'pending' ?
                    `<button class="action-btn approve-btn" data-id="${user.id}" title="Approve User"><span>✓</span></button>` :
                    `<button class="action-btn edit-btn" data-id="${user.id}" title="Edit User"><span>✏️</span></button>`
                }
                <button class="action-btn status-btn" data-id="${user.id}" data-current-status="${approvalStatus || 'inactive'}" title="${statusText === 'Active' ? 'Deactivate' : 'Activate'}">
                    <span>${statusText === 'Active' ? '🔒' : '🔓'}</span>
                </button>
                <button class="action-btn delete-btn" data-id="${user.id}" title="Delete User"><span>🗑️</span></button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });

    // Attach event listeners for action buttons
    attachActionListeners();
    
    // Update tab badge counts
    updateTabBadges();
}

// Helper function to update tab badge counts
function updateTabBadges() {
    if (!allUsersData || allUsersData.length === 0) return;
    
    try {
        // Count pending users
        const pendingCount = allUsersData.filter(user => 
            user && user.profile && user.profile.approval_status === 'pending'
        ).length;
        
        // Count admin users
        const adminCount = allUsersData.filter(user => 
            user && user.profile && user.profile.role && 
            (user.profile.role.toLowerCase() === 'admin' || 
             user.profile.role.toLowerCase() === 'administrator' ||
             user.profile.role.toLowerCase().includes('admin'))
        ).length;
        
        // Update badge texts
        const pendingBadge = document.querySelector('[data-tab="pending-approvals"] .badge');
        if (pendingBadge) pendingBadge.textContent = pendingCount;
        
        const adminBadge = document.querySelector('[data-tab="administrators"] .badge');
        if (adminBadge) adminBadge.textContent = adminCount;
        
        console.log(`Updated tab badges - Pending: ${pendingCount}, Admins: ${adminCount}`);
    } catch (error) {
        console.error("Error updating tab badges:", error);
    }
}

// Attach listeners to action buttons
function attachActionListeners() {
    console.log("Attaching action button listeners");
    
    // View buttons
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.removeEventListener('click', handleViewUser);
        btn.addEventListener('click', handleViewUser);
    });
    
    // Approve buttons
    document.querySelectorAll('.approve-btn').forEach(btn => {
        btn.removeEventListener('click', handleApproveUser);
        btn.addEventListener('click', handleApproveUser);
    });
    
    // Edit buttons
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.removeEventListener('click', handleEditUser);
        btn.addEventListener('click', handleEditUser);
    });
    
    // Status toggle buttons
    document.querySelectorAll('.status-btn').forEach(btn => {
        btn.removeEventListener('click', handleStatusToggle);
        btn.addEventListener('click', handleStatusToggle);
    });
    
    // Delete buttons
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.removeEventListener('click', handleDeleteUserClick);
        btn.addEventListener('click', handleDeleteUserClick);
    });
}

// Handle view user button click
function handleViewUser(event) {
    const userId = event.currentTarget.getAttribute('data-id');
    console.log("View user:", userId);
    
    const userData = allUsersData.find(u => u.id == userId);
    if (userData) {
        openUserDetailModal(userData);
    } else {
        showToast("Could not find user data to display.", "error");
    }
}

// Handle approve user button click
async function handleApproveUser(event) {
    const button = event.currentTarget;
    const userId = button.getAttribute('data-id');
    console.log("Approve user:", userId);
    
    if (!confirm(`Are you sure you want to approve user #${userId}?`)) {
        return;
    }

    button.disabled = true;

    try {
        console.log(`Calling API: /admin/users/${userId}/approve/`);
        const updatedUser = await apiRequest(`/admin/users/${userId}/approve/`, {
            method: 'PATCH'
        });
        
        console.log("API approve response:", updatedUser);
        showToast(`User #${userId} approved successfully!`, 'success');
        
        // Update the UI
        updateUserRowUI(userId, updatedUser);
        
        // Update the master data list
        const index = allUsersData.findIndex(u => u.id == userId);
        if (index !== -1) allUsersData[index] = updatedUser;
        
        // Update tab badge counts
        updateTabBadges();
    } catch (error) {
        console.error("Failed to approve user:", error);
        showToast(`Error approving user: ${error.message}`, 'error');
        button.disabled = false;
    }
}

// Handle edit user button click
function handleEditUser(event) {
    const userId = event.currentTarget.getAttribute('data-id');
    showToast(`Editing user #${userId} - Not Implemented Yet`, 'info');
}

// Handle status toggle button click
async function handleStatusToggle(event) {
    const button = event.currentTarget;
    const userId = button.getAttribute('data-id');
    const currentStatus = button.getAttribute('data-current-status');
    const newStatus = (currentStatus === 'active') ? 'inactive' : 'active';
    const actionText = (newStatus === 'active') ? 'activate' : 'deactivate';

    console.log(`Toggle status for user ${userId} from ${currentStatus} to ${newStatus}`);
    
    if (!confirm(`Are you sure you want to ${actionText} user #${userId}?`)) {
        return;
    }

    button.disabled = true;

    try {
        console.log(`Calling API: /admin/users/${userId}/set-status/ with status: ${newStatus}`);
        const updatedUser = await apiRequest(`/admin/users/${userId}/set-status/`, {
            method: 'PATCH',
            body: JSON.stringify({ status: newStatus })
        });
        
        console.log("API set-status response:", updatedUser);
        showToast(`User #${userId} ${actionText}d successfully!`, 'success');
        
        // Update the UI
        updateUserRowUI(userId, updatedUser);
        
        // Update the master data list
        const index = allUsersData.findIndex(u => u.id == userId);
        if (index !== -1) allUsersData[index] = updatedUser;
    } catch (error) {
        console.error(`Failed to ${actionText} user:`, error);
        showToast(`Error: ${error.message}`, 'error');
        button.disabled = false;
    }
}

// Handle delete user button click
function handleDeleteUserClick(event) {
    const button = event.currentTarget;
    const userId = button.getAttribute('data-id');
    console.log(`Requesting delete for user ID: ${userId}`);
    
    // Set data attributes on the confirmation button in the modal
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
        confirmBtn.setAttribute('data-delete-id', userId);
        confirmBtn.setAttribute('data-delete-type', 'user');
    } else {
        console.error("Confirm delete button not found in modal.");
    }
    
    // Open the modal
    openModal('deleteModal');
}

// Handle bulk approve action
async function handleBulkApprove() {
    const selectedIds = getSelectedIds('.user-select');
    if (selectedIds.length === 0) {
        showToast("No users selected.", "info");
        return;
    }
    
    if (!confirm(`Approve ${selectedIds.length} selected user(s)?`)) {
        return;
    }

    showToast(`Approving ${selectedIds.length} users...`, "info");
    let successCount = 0;
    let errorCount = 0;

    for (const userId of selectedIds) {
        try {
            const updatedUser = await apiRequest(`/admin/users/${userId}/approve/`, {
                method: 'PATCH'
            });
            
            // Update UI immediately
            updateUserRowUI(userId, updatedUser);
            
            // Update master data
            const index = allUsersData.findIndex(u => u.id == userId);
            if (index !== -1) allUsersData[index] = updatedUser;
            
            successCount++;
        } catch (error) {
            console.error(`Failed to approve user ${userId}:`, error);
            errorCount++;
        }
    }
    
    showToast(
        `Bulk Approval: ${successCount} succeeded, ${errorCount} failed.`, 
        errorCount > 0 ? "warning" : "success"
    );
    
    // Uncheck all checkboxes after operation
    uncheckAllCheckboxes();
    
    // Update tab badge counts
    updateTabBadges();
}

// Handle bulk deactivate action
async function handleBulkDeactivate() {
    const selectedIds = getSelectedIds('.user-select');
    if (selectedIds.length === 0) {
        showToast("No users selected.", "info");
        return;
    }
    
    if (!confirm(`Deactivate ${selectedIds.length} selected user(s)?`)) {
        return;
    }

    showToast(`Deactivating ${selectedIds.length} users...`, "info");
    let successCount = 0;
    let errorCount = 0;

    for (const userId of selectedIds) {
        try {
            const updatedUser = await apiRequest(`/admin/users/${userId}/set-status/`, {
                method: 'PATCH',
                body: JSON.stringify({ status: 'inactive' })
            });
            
            // Update UI immediately
            updateUserRowUI(userId, updatedUser);
            
            // Update master data
            const index = allUsersData.findIndex(u => u.id == userId);
            if (index !== -1) allUsersData[index] = updatedUser;
            
            successCount++;
        } catch (error) {
            console.error(`Failed to deactivate user ${userId}:`, error);
            errorCount++;
        }
    }
    
    showToast(
        `Bulk Deactivation: ${successCount} succeeded, ${errorCount} failed.`, 
        errorCount > 0 ? "warning" : "success"
    );
    
    // Uncheck all checkboxes after operation
    uncheckAllCheckboxes();
}

// Handle bulk delete action
function handleBulkDelete() {
    const selectedIds = getSelectedIds('.user-select');
    if (selectedIds.length === 0) {
        showToast("No users selected.", "info");
        return;
    }

    // Set context for the confirmation modal
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
        confirmBtn.setAttribute('data-delete-ids', JSON.stringify(selectedIds));
        confirmBtn.setAttribute('data-delete-type', 'user-bulk');
        
        // Update modal text if needed
        const modalTextElement = document.querySelector('#deleteModal .modal-body p');
        if (modalTextElement) {
            modalTextElement.textContent = `Are you sure you want to delete ${selectedIds.length} selected user(s)? This action cannot be undone.`;
        }
    }
    
    // Open the modal
    openModal('deleteModal');
}

// Handle delete confirmation
async function handleConfirmDelete() {
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (!confirmBtn) {
        console.error("Confirm delete button not found!");
        return;
    }
    
    const userId = confirmBtn.getAttribute('data-delete-id');
    const itemType = confirmBtn.getAttribute('data-delete-type');
    const userIdsString = confirmBtn.getAttribute('data-delete-ids');

    confirmBtn.disabled = true;

    if (itemType === 'user' && userId) {
        // Single User Delete
        console.log(`Confirming delete for user ID: ${userId}`);
        try {
            await apiRequest(`/admin/users/${userId}/`, { 
                method: 'DELETE' 
            });
            
            showToast(`User #${userId} deleted successfully.`, 'success');
            
            // Remove the row from the table
            document.querySelector(`tr[data-user-id="${userId}"]`)?.remove();
            
            // Update master data
            allUsersData = allUsersData.filter(u => u.id != userId);
            
            // Update tab badge counts
            updateTabBadges();
        } catch (error) {
            console.error("Failed to delete user:", error);
            showToast(`Error deleting user: ${error.message}`, 'error');
        }
    } else if (itemType === 'user-bulk' && userIdsString) {
        // Bulk User Delete
        let userIds = [];
        try {
            userIds = JSON.parse(userIdsString);
        } catch (parseError) {
            console.error("Failed to parse user IDs for bulk delete:", parseError);
            showToast("Error processing bulk delete request.", "error");
            confirmBtn.disabled = false;
            closeAllModals();
            return;
        }

        console.log(`Confirming bulk delete for user IDs: ${userIds}`);
        showToast(`Deleting ${userIds.length} users...`, "info");
        
        let successCount = 0;
        let errorCount = 0;
        
        for (const id of userIds) {
            try {
                await apiRequest(`/admin/users/${id}/`, { 
                    method: 'DELETE' 
                });
                
                // Remove the row from the table
                document.querySelector(`tr[data-user-id="${id}"]`)?.remove();
                
                successCount++;
            } catch (error) {
                console.error(`Failed to delete user ${id}:`, error);
                errorCount++;
            }
        }
        
        // Update master data
        allUsersData = allUsersData.filter(u => !userIds.map(String).includes(String(u.id)));
        
        showToast(
            `Bulk Delete: ${successCount} succeeded, ${errorCount} failed.`, 
            errorCount > 0 ? "warning" : "success"
        );
        
        // Uncheck all checkboxes after operation
        uncheckAllCheckboxes();
        
        // Update tab badge counts
        updateTabBadges();
    } else {
        console.log("Delete confirmation context unclear or missing.");
    }

    // Reset and close modal
    confirmBtn.disabled = false;
    confirmBtn.removeAttribute('data-delete-id');
    confirmBtn.removeAttribute('data-delete-ids');
    confirmBtn.removeAttribute('data-delete-type');
    
    // Reset modal text if changed
    const modalTextElement = document.querySelector('#deleteModal .modal-body p');
    if (modalTextElement) {
        modalTextElement.textContent = `Are you sure you want to delete the selected item(s)? This action cannot be undone.`;
    }
    
    closeAllModals();
}

// Fetch and render users
async function fetchAndRenderUsers() {
    await fetchUsersFromAPI();
    applyFiltersAndRender();
    updateBulkActionsState(0);
}

// Apply filters and render the filtered users
function applyFiltersAndRender() {
    console.log("Applying filters with current tab:", currentTab);
    console.log("Current filters:", currentFilters);
    
    if (!allUsersData || allUsersData.length === 0) {
        console.log("No users data available to filter");
        renderUsersTable([]);
        return;
    }
    
    // Start with all users
    let filtered = [...allUsersData];
    
    // Apply tab-based filtering
    if (currentTab === 'pending-approvals') {
        filtered = filtered.filter(user => 
            user && user.profile && user.profile.approval_status === 'pending'
        );
    } else if (currentTab === 'administrators') {
        filtered = filtered.filter(user => {
            if (!user || !user.profile || !user.profile.role) return false;
            
            const role = user.profile.role.toLowerCase();
            return role === 'admin' || 
                   role === 'administrator' ||
                   role.includes('admin');
        });
    }
    
    // Apply role filter
    if (currentFilters.role) {
        filtered = filtered.filter(user => 
            user && user.profile && 
            user.profile.role && 
            user.profile.role.toLowerCase() === currentFilters.role.toLowerCase()
        );
    }
    
    // Apply status filter
    // Apply status filter
    if (currentFilters.status) {
        filtered = filtered.filter(user => {
            if (!user || !user.profile) return false;
            
            if (currentFilters.status === 'active') {
                return user.profile.approval_status === 'active' && user.is_active === true;
            } else if (currentFilters.status === 'inactive') {
                return user.profile.approval_status === 'inactive' || user.is_active === false;
            } else if (currentFilters.status === 'pending') {
                return user.profile.approval_status === 'pending';
            }
            
            return false;
        });
    }
    
    // Apply search term
    if (currentFilters.search) {
        const searchTerm = currentFilters.search.toLowerCase();
        filtered = filtered.filter(user => {
            if (!user) return false;
            
            // Search in various user fields
            return (
                (user.first_name && user.first_name.toLowerCase().includes(searchTerm)) ||
                (user.last_name && user.last_name.toLowerCase().includes(searchTerm)) ||
                (user.email && user.email.toLowerCase().includes(searchTerm)) ||
                (user.profile?.role && user.profile.role.toLowerCase().includes(searchTerm)) ||
                (user.profile?.institution && user.profile.institution.toLowerCase().includes(searchTerm)) ||
                (user.profile?.country && user.profile.country.toLowerCase().includes(searchTerm))
            );
        });
    }
    
    console.log(`Filtered users: ${filtered.length} of ${allUsersData.length}`);
    renderUsersTable(filtered);
}

// Update a single row in the table after an action
function updateUserRowUI(userId, updatedUserData) {
    const row = document.querySelector(`tr[data-user-id="${userId}"]`);
    if (!row || !updatedUserData) return;

    console.log("Updating UI for user:", userId, updatedUserData);

    // Ensure profile exists, default to empty object if not
    const profile = updatedUserData.profile || {};
    
    // Determine status
    let statusClass = 'inactive';
    let statusText = 'Inactive';
    const approvalStatus = profile.approval_status;
    const isActive = updatedUserData.is_active;

    if (approvalStatus === 'pending') {
        statusClass = 'pending';
        statusText = 'Pending';
    } else if (approvalStatus === 'active' && isActive === true) {
        statusClass = 'active';
        statusText = 'Active';
    }

    // Update Status Badge
    const statusBadge = row.querySelector('.status-badge');
    if (statusBadge) {
        statusBadge.className = `status-badge ${statusClass}`;
        statusBadge.textContent = statusText;
    }

    // Update Action Buttons
    const actionsCell = row.querySelector('.actions-cell');
    if (actionsCell) {
        const approveBtn = actionsCell.querySelector('.approve-btn');
        const editBtn = actionsCell.querySelector('.edit-btn');
        const statusBtn = actionsCell.querySelector('.status-btn');
        
        // Remove approve button if user is no longer pending
        if (approveBtn && approvalStatus !== 'pending') {
            approveBtn.remove();
            
            // Add edit button if it doesn't exist
            if (!editBtn) {
                const newEditBtn = document.createElement('button');
                newEditBtn.className = 'action-btn edit-btn';
                newEditBtn.setAttribute('data-id', userId);
                newEditBtn.setAttribute('title', 'Edit User');
                newEditBtn.innerHTML = '<span>✏️</span>';
                newEditBtn.addEventListener('click', handleEditUser);
                
                // Insert before status button
                const statusBtn = actionsCell.querySelector('.status-btn');
                if (statusBtn) {
                    actionsCell.insertBefore(newEditBtn, statusBtn);
                } else {
                    actionsCell.appendChild(newEditBtn);
                }
            }
        }

        // Update status toggle button
        if (statusBtn) {
            statusBtn.setAttribute('data-current-status', approvalStatus || 'inactive');
            const isEffectivelyActive = statusText === 'Active';
            statusBtn.setAttribute('title', isEffectivelyActive ? 'Deactivate' : 'Activate');
            statusBtn.innerHTML = `<span>${isEffectivelyActive ? '🔒' : '🔓'}</span>`;
            statusBtn.disabled = false;
        }
    }
}

// Open user detail modal with specific user information
function openUserDetailModal(userData) {
    if (!userData) return;
    
    const profile = userData.profile || {};

    // Update modal fields
    const nameElement = document.getElementById('userDetailName');
    if (nameElement) {
        nameElement.textContent = `${userData.first_name || ''} ${userData.last_name || ''}`.trim() || userData.username || 'N/A';
    }
    
    const emailElement = document.getElementById('userDetailEmail');
    if (emailElement) {
        emailElement.textContent = userData.email || 'N/A';
    }

    const roleElement = document.getElementById('userDetailRole')?.querySelector('span');
    if (roleElement) {
        roleElement.textContent = profile.role || 'N/A';
    }

    const statusBadge = document.getElementById('userDetailStatus')?.querySelector('.status-badge');
    if (statusBadge) {
        let statusClass = 'inactive';
        let statusText = 'Inactive';
        const approvalStatus = profile.approval_status;
        const isActive = userData.is_active;
        
        if (approvalStatus === 'pending') {
            statusClass = 'pending';
            statusText = 'Pending';
        } else if (approvalStatus === 'active' && isActive === true) {
            statusClass = 'active';
            statusText = 'Active';
        }
        
        statusBadge.className = `status-badge ${statusClass}`;
        statusBadge.textContent = statusText;
    }

    const institutionElement = document.getElementById('userDetailInstitution');
    if (institutionElement) {
        institutionElement.textContent = profile.institution || 'N/A';
    }
    
    const countryElement = document.getElementById('userDetailCountry');
    if (countryElement) {
        countryElement.textContent = profile.country || 'N/A';
    }
    
    const joinedElement = document.getElementById('userDetailJoined');
    if (joinedElement) {
        joinedElement.textContent = userData.date_joined ? new Date(userData.date_joined).toLocaleDateString() : 'N/A';
    }

    // Placeholder data for fields not yet in API/model
    const reportsElement = document.getElementById('userDetailReports');
    if (reportsElement) {
        reportsElement.textContent = '0'; // TODO: Fetch actual count later
    }
    
    const lastActiveElement = document.getElementById('userDetailLastActive');
    if (lastActiveElement) {
        lastActiveElement.textContent = userData.last_login ? new Date(userData.last_login).toLocaleString() : 'Never';
    }

    // Open the modal
    openModal('userDetailModal');
}

// Update pagination controls
function updatePaginationControls(totalItems, nextUrl, previousUrl) {
    const paginationContainer = document.querySelector('.pagination');
    if (!paginationContainer) return;

    // Check if pagination is needed
    const pageSize = 10; // Assuming default page size
    const totalPages = Math.ceil(totalItems / pageSize);
    
    // Add/remove has-pages class to control visibility
    if (totalPages > 1) {
        paginationContainer.classList.add('has-pages');
    } else {
        paginationContainer.classList.remove('has-pages');
    }

    // Update Previous/Next buttons
    const prevBtn = paginationContainer.querySelector('.pagination-btn:first-child');
    const nextBtn = paginationContainer.querySelector('.pagination-btn:last-child');

    if (prevBtn) {
        prevBtn.disabled = !previousUrl;
        prevBtn.dataset.url = previousUrl || '';
    }
    
    if (nextBtn) {
        nextBtn.disabled = !nextUrl;
        nextBtn.dataset.url = nextUrl || '';
    }

    // Determine current page
    let currentPage = 1;
    
    try {
        if (previousUrl) {
            if (previousUrl.startsWith('http')) {
                const prevPage = parseInt(new URL(previousUrl).searchParams.get('page') || '0');
                currentPage = prevPage + 1;
            }
        } else if (nextUrl) {
            if (nextUrl.startsWith('http')) {
                const nextPage = parseInt(new URL(nextUrl).searchParams.get('page') || '2');
                currentPage = nextPage - 1;
            }
        }
    } catch (e) { 
        console.warn("Could not parse page number from URL", e); 
    }

    // Update page numbers and active state
    const pageButtons = paginationContainer.querySelectorAll('.pagination-page');
    pageButtons.forEach(btn => {
        const pageNum = parseInt(btn.textContent);
        if (pageNum === currentPage) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update page info text
    const pageInfo = paginationContainer.querySelector('.page-info');
    if (pageInfo) {
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    }
}

// Handle pagination clicks
async function handlePaginationClick(event) {
    const button = event.target.closest('.pagination-btn, .pagination-page');
    if (!button || button.disabled || button.classList.contains('active')) return;

    let apiUrl = button.dataset.url;

    // Handle page number clicks
    if (button.classList.contains('pagination-page')) {
        const pageNum = button.textContent;
        apiUrl = `/admin/users/?page=${pageNum}`;
    }

    if (apiUrl) {
        // Convert full URL to relative path if needed
        let relativeApiUrl = '';
        try {
            if (apiUrl.startsWith('http')) {
                relativeApiUrl = new URL(apiUrl).pathname + new URL(apiUrl).search;
            } else if (apiUrl.startsWith('/')) {
                relativeApiUrl = apiUrl;
            } else {
                console.error("Unrecognized pagination URL format:", apiUrl);
                showToast("Error navigating pagination.", "error");
                return;
            }
        } catch (e) {
            console.error("Error parsing pagination URL:", apiUrl, e);
            showToast("Error navigating pagination.", "error");
            return;
        }

        // Fetch data for the new page
        await fetchUsersFromAPI(relativeApiUrl);
        
        // Apply filters to the new data
        applyFiltersAndRender();
    }
}

// Helper function to get selected IDs
function getSelectedIds(selector) {
    return Array.from(document.querySelectorAll(`${selector}:checked`))
        .map(cb => cb.getAttribute('data-id'));
}

// Helper function to uncheck all checkboxes
function uncheckAllCheckboxes() {
    const selectAllCheckbox = document.getElementById('selectAllUsers');
    if (selectAllCheckbox) selectAllCheckbox.checked = false;
    
    document.querySelectorAll('.user-select').forEach(cb => cb.checked = false);
    
    updateBulkActionsState(0);
}

// Helper function for opening modals
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    } else {
        console.warn(`Modal with ID "${modalId}" not found.`);
    }
}

// Helper function for closing all modals
function closeAllModals() {
    document.querySelectorAll('.modal.active').forEach(modal => {
        modal.classList.remove('active');
    });
}

// Helper function for showing toast notifications
if (!window.showToast) {
    window.showToast = function(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return; // Guard clause to prevent errors
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    };
}
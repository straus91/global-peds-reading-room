// js/admin-cases.js - Admin manage cases functionalities

// Global state for cases (optional, but can be useful for caching/pagination)
let allFetchedCases = [];
let currentCasesPage = 1;
let totalCases = 0;
let casesNextUrl = null;
let casesPrevUrl = null;

document.addEventListener('DOMContentLoaded', () => {
    // Ensure this only runs on the manage-cases.html page
    if (window.location.pathname.includes('manage-cases.html')) {
        console.log("Manage Cases page loaded. Initializing...");
        initializeManageCasesPage();
    } else if (window.location.pathname.includes('add-case.html')) {
        // If you have common functions needed on add-case.html that were in an old admin-cases.js,
        // they should be moved to admin-case-edit.js or a shared utility file.
        // For now, we assume admin-cases.js is primarily for manage-cases.html
        console.log("Add Case page loaded. admin-cases.js is not initializing manage cases table here.");
    }
});

async function initializeManageCasesPage() {
    // Setup UI elements like filters, search, and action buttons
    setupCaseFiltersAndSearch();
    setupCaseTableEventListeners(); // For dynamic content like pagination or action buttons

    // Initial fetch of cases
    await fetchAndRenderCases();
}

function setupCaseFiltersAndSearch() {
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('caseSearch');
    const statusFilter = document.getElementById('statusFilter');
    const subspecialtyFilter = document.getElementById('subspecialtyFilter');
    const modalityFilter = document.getElementById('modalityFilter');

    searchBtn?.addEventListener('click', () => fetchAndRenderCases());
    searchInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') fetchAndRenderCases();
    });
    statusFilter?.addEventListener('change', () => fetchAndRenderCases());
    subspecialtyFilter?.addEventListener('change', () => fetchAndRenderCases());
    modalityFilter?.addEventListener('change', () => fetchAndRenderCases());

    console.log("Case filters and search listeners set up.");
}

function setupCaseTableEventListeners() {
    const tableBody = document.getElementById('adminCasesTableBody');
    if (!tableBody) {
        console.error("[SetupListeners] Table body 'adminCasesTableBody' not found.");
        return;
    }

    // To prevent adding multiple listeners if this function is called again,
    // we can either remove the old one or use a flag.
    // For simplicity, let's assume it's called once or that re-adding is harmless here.

    tableBody.addEventListener('click', (event) => {
        // Find the button, whether the click was on the button itself or its child span
        const editButton = event.target.closest('button.edit-case-btn');

        if (editButton) {
            event.preventDefault(); // Good practice for button clicks that navigate
            const caseId = editButton.dataset.id; // Use .dataset for data-* attributes
            if (caseId) {
                console.log(`[Action] Edit button clicked for case ID: ${caseId}. Redirecting to add-case.html?edit_id=${caseId}`);
                window.location.href = `add-case.html?edit_id=${caseId}`;
            } else {
                console.warn('[Action] Edit button clicked, but no case ID found on button.');
            }
            return; // Stop further processing if edit button was handled
        }

        // Example for other buttons if you add them directly here (like view or delete)
        // const deleteButton = event.target.closest('button.delete-btn');
        // if (deleteButton) {
        //     event.preventDefault();
        //     const caseId = deleteButton.dataset.id;
        //     if (caseId) {
        //         confirmDeleteCase(caseId); // Make sure confirmDeleteCase is defined
        //     }
        //     return;
        // }
    });
    console.log("[SetupListeners] Case table action event listener (delegated) is set up on adminCasesTableBody.");
}

async function fetchAndRenderCases(url = null) {
    const tableBody = document.getElementById('adminCasesTableBody');
    if (!tableBody) {
        console.error("Table body 'adminCasesTableBody' not found.");
        return;
    }

    // Show loading state
    tableBody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:20px;">Loading cases...</td></tr>';

    let queryParams = new URLSearchParams();
    if (!url) { // Only build query params if not using a direct pagination URL
        const searchTerm = document.getElementById('caseSearch')?.value || '';
        const status = document.getElementById('statusFilter')?.value || '';
        const subspecialty = document.getElementById('subspecialtyFilter')?.value || '';
        const modality = document.getElementById('modalityFilter')?.value || '';

        if (searchTerm) queryParams.append('search', searchTerm);
        if (status) queryParams.append('status', status);
        if (subspecialty) queryParams.append('subspecialty', subspecialty);
        if (modality) queryParams.append('modality', modality);
        // Default sorting (backend should handle this by default if not specified)
        // queryParams.append('ordering', '-created_at');
    }

    const endpoint = url || `/cases/admin/cases/?${queryParams.toString()}`;
    console.log(`Workspaceing cases from: ${endpoint}`);

    try {
        const response = await apiRequest(endpoint); // From api.js

        if (response && Array.isArray(response.results)) {
            allFetchedCases = response.results;
            totalCases = response.count;
            casesNextUrl = response.next;
            casesPrevUrl = response.previous;

            renderCasesTable(allFetchedCases);
            renderPaginationControls(totalCases, casesNextUrl, casesPrevUrl);
        } else {
            console.error("Invalid response structure for cases:", response);
            tableBody.innerHTML = '<tr><td colspan="9" style="text-align:center; color:red;">Error: Could not parse case data.</td></tr>';
        }
    } catch (error) {
        console.error("Failed to fetch cases:", error);
        const errorMsg = error.data?.detail || error.message || "An unknown error occurred";
        tableBody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:red;">Failed to load cases: ${errorMsg}</td></tr>`;
    }
}

function renderCasesTable(cases) {
    const tableBody = document.getElementById('adminCasesTableBody');
    if (!tableBody) return;

    tableBody.innerHTML = ''; // Clear previous content or loading message

    if (cases.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" style="text-align:center;">No cases found matching your criteria.</td></tr>';
        return;
    }

    cases.forEach(caseItem => {
        const row = tableBody.insertRow();
        const createdDate = caseItem.created_at ? new Date(caseItem.created_at).toLocaleDateString() : 'N/A';
        const statusDisplay = caseItem.status ? caseItem.status.charAt(0).toUpperCase() + caseItem.status.slice(1) : 'N/A';

        row.innerHTML = `
            <td><input type="checkbox" class="case-select" data-id="${caseItem.id}"></td>
            <td>${caseItem.id}</td>
            <td>${caseItem.title || 'N/A'}</td>
            <td>${caseItem.subspecialty_display || caseItem.subspecialty || 'N/A'}</td>
            <td>${caseItem.modality_display || caseItem.modality || 'N/A'}</td>
            <td>${caseItem.difficulty_display || caseItem.difficulty || 'N/A'}</td>
            <td><span class="status-badge ${caseItem.status || 'default'}">${statusDisplay}</span></td>
            <td>${createdDate}</td>
            <td class="actions-cell">
                <button class="action-btn edit-case-btn" data-id="${caseItem.id}" title="Edit Case"><span>✏️</span></button>
                <button class="action-btn view-btn" data-id="${caseItem.id}" title="View Case (Frontend)" onclick="alert('View on frontend not implemented yet for case ID ${caseItem.id}')"><span>👁️</span></button>
                <button class="action-btn delete-btn" data-id="${caseItem.id}" title="Delete Case" onclick="confirmDeleteCase(${caseItem.id})"><span>🗑️</span></button>
            </td>
        `;
    });
     // Re-initialize table selection checkboxes if they were cleared
    if (typeof initTableSelection === 'function') {
        // You might need to ensure initTableSelection can be called multiple times safely
        // or specifically target the newly added checkboxes if it doesn't use event delegation.
        // For now, let's assume it's safe or uses delegation.
        initTableSelection();
    }
}

function renderPaginationControls(count, next, previous) {
    const paginationContainer = document.querySelector('.pagination');
    if (!paginationContainer) return;

    const itemsPerPage = 10; // This should match your Django REST Framework pagination settings
    const totalPages = Math.ceil(count / itemsPerPage);

    paginationContainer.innerHTML = ''; // Clear existing

    if (totalPages <= 1) {
        paginationContainer.style.display = 'none';
        return;
    }
    paginationContainer.style.display = 'flex';


    let currentPage = 1;
    if (previous) {
        const prevPageMatch = previous.match(/page=(\d+)/);
        currentPage = prevPageMatch ? parseInt(prevPageMatch[1]) + 1 : (next ? 1 : totalPages);
    } else if (next) {
        const nextPageMatch = next.match(/page=(\d+)/);
        currentPage = nextPageMatch ? parseInt(nextPageMatch[1]) - 1 : 1;
    } else if (count > 0) { // Only one page
        currentPage = 1;
    }


    // Previous Button
    const prevButton = document.createElement('button');
    prevButton.className = 'pagination-btn';
    prevButton.textContent = 'Previous';
    prevButton.disabled = !previous;
    if (previous) prevButton.dataset.url = previous;
    prevButton.addEventListener('click', () => fetchAndRenderCases(casesPrevUrl));
    paginationContainer.appendChild(prevButton);

    // Page Numbers (simplified for now, can be expanded)
    const pagesDiv = document.createElement('div');
    pagesDiv.className = 'pagination-pages';
     // Show current page and total pages
    pagesDiv.innerHTML = `<span class="page-info">Page ${currentPage} of ${totalPages}</span>`;
    // For more complex pagination (first, last, numbered pages):
    // You would loop from 1 to totalPages, create spans, add event listeners
    // and implement logic to show a limited number of page links (e.g., with ellipses).
    paginationContainer.appendChild(pagesDiv);


    // Next Button
    const nextButton = document.createElement('button');
    nextButton.className = 'pagination-btn';
    nextButton.textContent = 'Next';
    nextButton.disabled = !next;
    if (next) nextButton.dataset.url = next; // Store full URL for simplicity
    nextButton.addEventListener('click', () => fetchAndRenderCases(casesNextUrl));
    paginationContainer.appendChild(nextButton);
}


// Placeholder for confirm delete
function confirmDeleteCase(caseId) {
    if (confirm(`Are you sure you want to delete case ID ${caseId}?`)) {
        deleteCase(caseId);
    }
}

async function deleteCase(caseId) {
    console.log(`Attempting to delete case ID ${caseId}`);
    try {
        await apiRequest(`/cases/admin/cases/${caseId}/`, { method: 'DELETE' });
        showToast(`Case ID ${caseId} deleted successfully.`, 'success');
        fetchAndRenderCases(); // Refresh the list
    } catch (error) {
        console.error(`Failed to delete case ${caseId}:`, error);
        const errorMsg = error.data?.detail || error.message || "An unknown error occurred";
        showToast(`Error deleting case: ${errorMsg}`, 'error');
    }
}

// Fallback for showToast if not globally defined (from admin.js usually)
if (typeof showToast !== 'function') {
    console.warn('[admin-cases.js] showToast function not found, using console log fallback.');
    window.showToast = function(message, type = 'info') {
        console.log(`Toast (${type}): ${message}`);
    };
}
// js/main.js - Main application logic

console.log("--- main.js script started ---"); // <<< Check if script runs at all

// Assume api.js is loaded first
// Assume other functions like loadWelcome, loadMyReports, submitReport etc. exist

document.addEventListener('DOMContentLoaded', function() {
    console.log("--- DOMContentLoaded event fired ---"); // <<< Check if this runs

    // Initial setup: Check login status, load default view etc.
    checkLoginStatusAndInit();

    // Setup Navigation Links
    const casesLinkElement = document.getElementById('casesLink');
    console.log("Found #casesLink element:", casesLinkElement); // <<< Check if element is found
    casesLinkElement?.addEventListener('click', (e) => {
        console.log("--- Cases link clicked! ---"); // <<< Check if listener fires
        e.preventDefault();
        loadCaseList(); // Load cases when nav link is clicked
    });

    const myReportsLinkElement = document.getElementById('myReportsLink');
    console.log("Found #myReportsLink element:", myReportsLinkElement); // <<< Check if element is found
    myReportsLinkElement?.addEventListener('click', (e) => {
        console.log("--- My Reports link clicked! ---"); // <<< Check if listener fires
        e.preventDefault();
        loadMyReports();
    });

    // Add listeners for profile, logout etc.
    const profileLinkElement = document.getElementById('profileLink');
     console.log("Found #profileLink element:", profileLinkElement); // <<< Check if element is found
    profileLinkElement?.addEventListener('click', (e) => {
         console.log("--- Profile link clicked! ---"); // <<< Check if listener fires
         e.preventDefault();
         // TODO: Implement profile view/modal
         showToast("Profile feature not yet implemented.", "info");
    });

    const logoutLinkElement = document.getElementById('logoutLink');
     console.log("Found #logoutLink element:", logoutLinkElement); // <<< Check if element is found
    logoutLinkElement?.addEventListener('click', (e) => { // Changed ID to match index.html
         console.log("--- Logout link clicked! ---"); // <<< Check if listener fires
         e.preventDefault();
         handleLogout();
    });

});

// Check login status and initialize the main view
async function checkLoginStatusAndInit() {
    console.log("--- checkLoginStatusAndInit called ---");
    const tokens = getAuthTokens(); // from api.js
    if (!tokens) {
        console.log("No auth tokens found, redirecting to login.");
        // Not logged in, redirect to login page
        window.location.href = 'login.html';
        return;
    }

    try {
        // Verify token / fetch user details
        const user = await fetchUserDetails();
        if (user) {
            console.log("User details fetched/found:", user);
            updateUserMenu(user); // Update header with user info
            loadWelcome(user); // Load initial welcome message or dashboard
            // Show admin link if user is admin
            if (user.isAdmin) {
                const adminLink = document.getElementById('adminLink');
                if(adminLink) {
                    console.log("User is admin, showing admin link.");
                    adminLink.style.display = 'inline'; // Or 'block' depending on layout
                }
            }
        } else {
            throw new Error("User data not found.");
        }
    } catch (error) {
        console.error("Authentication check failed:", error);
        clearAuthTokens(); // Clear invalid tokens
        window.location.href = 'login.html'; // Redirect to login
    }
}

// Fetch user details (Example implementation)
async function fetchUserDetails() {
     console.log("--- fetchUserDetails called ---");
     // Check sessionStorage first if storing user details there after login
     const storedUser = sessionStorage.getItem('user');
     if (storedUser) {
         try {
             console.log("Found user details in sessionStorage.");
             // Periodically re-validate with API? For now, trust sessionStorage
             return JSON.parse(storedUser);
         } catch (e) {
             console.error("Failed to parse stored user data", e);
             sessionStorage.removeItem('user'); // Clear invalid data
         }
     }
     // If not in session storage, fetch from API
     console.log("Fetching user details from API...");
    try {
        const userData = await apiRequest('/users/me/'); // Uses api.js
        if (userData) {
             console.log("Successfully fetched user details from API:", userData);
             // Store essential details for later use
             const userDetails = {
                 id: userData.id,
                 // Use first/last name if available, otherwise username
                 name: `${userData.first_name || ''} ${userData.last_name || ''}`.trim() || userData.username,
                 email: userData.email,
                 // Ensure is_admin comes from the API response (check UserSerializer)
                 isAdmin: userData.is_admin === true
             };
             sessionStorage.setItem('user', JSON.stringify(userDetails));
             return userDetails;
        }
        console.warn("API returned no user data from /users/me/");
        return null;
    } catch (error) {
        console.error("Failed to fetch user details from API:", error);
        // Handle specific errors like 401 if needed
        if (error.status === 401) {
             console.log("API returned 401 for /users/me/, clearing tokens.");
             clearAuthTokens();
             window.location.href = 'login.html';
        }
        return null;
    }
}


// Update user menu in the header (Example)
function updateUserMenu(user) {
    console.log("--- updateUserMenu called ---");
    const userMenuContainer = document.querySelector('.user-menu');
    if (!userMenuContainer) {
        console.warn("User menu container not found.");
        return;
    }

    const userNameSpan = userMenuContainer.querySelector('span');
    // const userImg = userMenuContainer.querySelector('img'); // If you want to update avatar

    if (userNameSpan) {
        userNameSpan.textContent = user.name || user.email;
    } else {
         console.warn("User name span not found in user menu.");
    }
    // Potentially update profile link href if needed
}

// Load Welcome Message (Example)
function loadWelcome(user) {
    console.log("--- loadWelcome called ---");
    const mainContent = document.getElementById('mainContent');
    if (mainContent) {
        mainContent.innerHTML = `<h2>Welcome, ${user.name || 'User'}!</h2><p>Select "Cases" from the navigation to begin.</p>`;
    } else {
         console.error("Main content area not found for welcome message.");
    }
}

// --- Load Case List View ---
async function loadCaseList(url = '/cases/cases/') { // Accept URL for pagination
    console.log(`--- loadCaseList called with url: ${url} ---`); // <<< Check if function runs
    const mainContent = document.getElementById('mainContent');
    if (!mainContent) {
        console.error("Main content area not found.");
        return;
    }

    // --- HTML Structure & CSS for Case List ---
    mainContent.innerHTML = `
        <style>
            /* Style for the side-by-side container */
            .case-list-split-view {
                display: flex;
                flex-wrap: wrap; /* Allow wrapping on smaller screens */
                gap: 20px; /* Space between grid and table */
                margin-top: 20px;
            }
            /* Style for the grid panel */
            .case-grid-panel {
                flex: 1 1 400px; /* Flex grow, shrink, basis */
                min-width: 300px; /* Minimum width before wrapping */
            }
             /* Style for the table panel */
            .case-table-panel {
                flex: 2 1 500px; /* Let table take more space */
                min-width: 400px;
                overflow-x: auto; /* Add horizontal scroll for table if needed */
            }
            /* Ensure grid itself displays cards correctly */
            #caseGrid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 15px;
            }
            /* Basic table styling */
            #caseTable {
                width: 100%;
                border-collapse: collapse;
            }
            #caseTable th, #caseTable td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            #caseTable th {
                background-color: #f2f2f2;
            }
            /* Add styles for viewed/reported rows if needed */
             #caseTable tr.viewed td { background-color: #e8f5e9; }
             #caseTable tr.reported td { background-color: #dcedc8; font-weight: bold; }

            /* Responsive: Stack on smaller screens */
            @media (max-width: 768px) {
                .case-list-split-view {
                    flex-direction: column;
                }
                .case-grid-panel, .case-table-panel {
                     flex-basis: auto; /* Reset basis */
                }
            }
        </style>

        <div class="case-list-header">
            <h2>Radiology Cases</h2>
            <div class="filters">
                <select id="filterSubspecialty" disabled><option value="">All Subspecialties</option></select>
                <select id="filterModality" disabled><option value="">All Modalities</option></select>
                <select id="filterDifficulty" disabled><option value="">All Difficulties</option></select>
                <button id="applyFiltersBtn" disabled>Apply Filters</button>
                <small>(Filters not implemented yet)</small>
            </div>
        </div>

        <div class="loading-indicator">Loading cases...</div>

        <div class="case-list-split-view">
            <div class="case-grid-panel">
                 <h3>Case Grid View</h3>
                 <div class="case-grid" id="caseGrid">
                     </div>
            </div>
            <div class="case-table-panel">
                <h3>Case List View</h3>
                <div class="case-table-container">
                    <table id="caseTable">
                        <thead>
                            <tr>
                                <th>Title</th>
                                <th>Subspecialty</th>
                                <th>Modality</th>
                                <th>Status</th>
                                <th>Date Added</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="pagination" id="casePagination">
            </div>
    `;
    // --- END HTML & CSS for Case List ---

    const gridContainer = document.getElementById('caseGrid');
    const tableBody = document.getElementById('caseTable')?.querySelector('tbody');
    const loadingIndicator = mainContent.querySelector('.loading-indicator');
    const paginationContainer = document.getElementById('casePagination');

    if (!gridContainer || !tableBody || !loadingIndicator || !paginationContainer) {
         console.error("Required elements for case list not found in loaded HTML.");
         loadingIndicator.textContent = 'Error loading case list view structure.';
         return;
    }

    try {
        // Fetch published cases from the backend API endpoint
        console.log(`Fetching cases from ${url}`);
        const response = await apiRequest(url); // Uses api.js

        loadingIndicator.style.display = 'none'; // Hide loading indicator

        if (response && Array.isArray(response.results)) {
            const cases = response.results;
            console.log(`Received ${cases.length} cases.`);

            if (cases.length === 0 && !response.previous) { // Only show if first page is empty
                gridContainer.innerHTML = '<p>No published cases found.</p>';
                tableBody.innerHTML = '<tr><td colspan="6">No published cases found.</td></tr>';
            } else {
                renderCaseGrid(gridContainer, cases);
                renderCaseTable(tableBody, cases);
            }
            // Handle pagination controls
            renderPagination(paginationContainer, response.count, response.next, response.previous);

        } else {
            console.error("Invalid response structure received from API:", response);
            gridContainer.innerHTML = '<p>Error loading cases. Invalid data received.</p>';
            tableBody.innerHTML = '<tr><td colspan="6">Error loading cases.</td></tr>';
        }

    } catch (error) {
        console.error("Failed to fetch or render cases:", error);
        loadingIndicator.style.display = 'none';
        gridContainer.innerHTML = `<p>Error loading cases: ${error.message}</p>`;
        tableBody.innerHTML = `<tr><td colspan="6">Error loading cases: ${error.message}</td></tr>`;
    }
}

// Render cases into the grid view
    function renderCaseGrid(container, cases) {
        // Clear any previous content from the container
        container.innerHTML = '';

        // If there are no cases, display a message
        if (!cases || cases.length === 0) {
            container.innerHTML = '<p>No published cases found at the moment.</p>';
            return; // Exit the function early
        }

        // Loop through each case provided in the 'cases' array
        cases.forEach(caseData => {
            // Create a new 'div' element for each case card
            const card = document.createElement('div');
            card.className = 'case-card'; // Assign a class for styling

            // Apply additional styling if the user has reported or viewed this case
            if (caseData.is_reported_by_user) {
                card.classList.add('reported');
            } else if (caseData.is_viewed_by_user) {
                card.classList.add('viewed');
            }

            // Define a placeholder image URL.
            // The text on the placeholder can use the modality from caseData.
            // ** USING: caseData.modality **
            const thumbnailUrl = `https://placehold.co/300x200/eee/666?text=${caseData.modality || 'Case'}`;

            // Set the inner HTML of the card with case details
            // ** USING: caseData.modality, caseData.subspecialty, caseData.difficulty **
            card.innerHTML = `
                <img src="${thumbnailUrl}" alt="Case thumbnail for ${caseData.title || 'Untitled Case'}" onerror="this.src='https://placehold.co/300x200/eee/ccc?text=No+Image'; this.alt='Image load error';">
                <h4>${caseData.title || 'Untitled Case'}</h4>
                <p>
                    Modality: ${caseData.modality || 'N/A'}<br>
                    Subspecialty: ${caseData.subspecialty || 'N/A'}
                </p>
                <div class="tags">
                    <span class="tag difficulty-${(caseData.difficulty || 'unknown').toLowerCase().replace(/\s+/g, '-')}">
                        ${caseData.difficulty || 'Unknown Difficulty'}
                    </span>
                    ${caseData.is_reported_by_user ? '<span class="tag status-reported">Reported</span>' : ''}
                    ${!caseData.is_reported_by_user && caseData.is_viewed_by_user ? '<span class="tag status-viewed">Viewed</span>' : ''}
                </div>
                <button class="view-case-btn" data-case-id="${caseData.id}">View Case</button>
            `;

            // Find the "View Case" button within the newly created card
            const viewButton = card.querySelector('.view-case-btn');
            if (viewButton) {
                // Add an event listener to the button. When clicked, it will call the 'viewCase' function,
                // passing the ID of the current case.
                viewButton.addEventListener('click', () => viewCase(caseData.id));
            }

            // Add the newly created and populated card to the main container
            container.appendChild(card);
        });
    }


// Render cases into the table view
// Render cases into the table view
    function renderCaseTable(tableBody, cases) {
        // Clear any previous content from the table body
        tableBody.innerHTML = '';

        // If there are no cases, display a message in a single row
        if (!cases || cases.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No published cases found at the moment.</td></tr>';
            return; // Exit the function early
        }

        // Loop through each case provided in the 'cases' array
        cases.forEach(caseData => {
            // Insert a new row into the table
            const row = tableBody.insertRow();
            let rowClass = '';

            // Apply a class to the row if the user has reported or viewed this case
            if (caseData.is_reported_by_user) {
                rowClass = 'reported';
            } else if (caseData.is_viewed_by_user) {
                rowClass = 'viewed';
            }
            if (rowClass) {
                row.className = rowClass;
            }

            // Determine the status text based on user interaction
            const statusText = caseData.is_reported_by_user ? 'Reported' : (caseData.is_viewed_by_user ? 'Viewed' : 'New');
            // Format the publication date
            const addedDate = caseData.published_at ? new Date(caseData.published_at).toLocaleDateString() : 'N/A';

            // Creating cells and populating them with case data
            // ** USING: caseData.title **
            const titleCell = row.insertCell();
            titleCell.textContent = caseData.title || 'Untitled Case';

            // ** USING: caseData.subspecialty **
            const subspecialtyCell = row.insertCell();
            subspecialtyCell.textContent = caseData.subspecialty || 'N/A';

            // ** USING: caseData.modality **
            const modalityCell = row.insertCell();
            modalityCell.textContent = caseData.modality || 'N/A';

            const statusCell = row.insertCell();
            statusCell.textContent = statusText;

            const dateCell = row.insertCell();
            dateCell.textContent = addedDate;

            // Create and add the "View" button for each case
            const actionsCell = row.insertCell();
            const viewButton = document.createElement('button');
            viewButton.className = 'view-case-btn'; // Use a consistent class for styling
            viewButton.textContent = 'View';
            viewButton.setAttribute('data-case-id', caseData.id); // Store case ID for the event listener
            viewButton.addEventListener('click', () => viewCase(caseData.id)); // Call viewCase on click
            actionsCell.appendChild(viewButton);
        });
    }
    
// Render basic pagination controls (Example)
function renderPagination(container, totalItems, nextUrl, previousUrl) {
    // ... (renderPagination function remains the same as previous version) ...
    container.innerHTML = ''; // Clear previous
    if (!totalItems || totalItems <= 10) return; // Don't show if only one page (assuming page size 10 from backend)

    const prevDisabled = !previousUrl ? 'disabled' : '';
    const nextDisabled = !nextUrl ? 'disabled' : '';

    container.innerHTML = `
        <button class="pagination-btn prev-btn" data-url="${previousUrl || ''}" ${prevDisabled}>Previous</button>
        <span class="page-info"></span>
        <button class="pagination-btn next-btn" data-url="${nextUrl || ''}" ${nextDisabled}>Next</button>
    `;

    // Add event listeners for pagination buttons
    container.querySelectorAll('.pagination-btn').forEach(btn => {
        btn.addEventListener('click', handleCasePaginationClick);
    });

    // Update page info text
    const pageInfo = container.querySelector('.page-info');
    if (pageInfo) {
        const pageSize = 10; // Assuming page size 10 from backend
        let currentPage = 1;
        try {
            // Determine current page based on which link (prev/next) is available
            if (previousUrl && previousUrl.includes('page=')) {
                currentPage = parseInt(new URL(previousUrl).searchParams.get('page') || '0') + 1;
            } else if (nextUrl && nextUrl.includes('page=')) {
                 currentPage = parseInt(new URL(nextUrl).searchParams.get('page') || '2') - 1;
            } else if (!previousUrl && nextUrl) { // Only next exists -> page 1
                 currentPage = 1;
            } else if (previousUrl && !nextUrl) { // Only prev exists -> last page
                 currentPage = Math.ceil(totalItems / pageSize);
            }
        } catch (e) { console.warn("Could not parse page number from URL", e); }
        const totalPages = Math.ceil(totalItems / pageSize);
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    }
}

// Handle clicks on pagination buttons for the case list
async function handleCasePaginationClick(event) {
    // ... (handleCasePaginationClick function remains the same as previous version) ...
    console.log("--- handleCasePaginationClick called ---");
    const button = event.target;
    const apiUrl = button.dataset.url; // Get the full URL from the button

    if (!apiUrl || button.disabled) return;

    // Convert full URL back to relative path for apiRequest
    let relativeApiUrl = '';
    try {
        if (apiUrl.startsWith('http')) {
             relativeApiUrl = new URL(apiUrl).pathname + new URL(apiUrl).search;
             // Remove the base API part if apiRequest prepends it
             relativeApiUrl = relativeApiUrl.replace('/api', ''); // Adjust if needed
        } else {
             console.error("Pagination URL is not absolute:", apiUrl);
             throw new Error("Invalid pagination URL format.");
        }
        // Call loadCaseList with the relative path for the next/previous page
        loadCaseList(relativeApiUrl);
    } catch (error) {
        console.error("Failed to handle pagination click:", error);
        showToast("Error loading next page.", "error");
    }
}


// --- Load My Reports View ---

async function loadMyReports() {
    console.log("--- loadMyReports called ---");
    const mainContent = document.getElementById('mainContent');
    if (!mainContent) {
        console.error("Main content area #mainContent not found for My Reports.");
        return;
    }

    mainContent.innerHTML = `<h2>My Submitted Reports</h2><div class="loading-indicator">Fetching your reports...</div>`;
    const loadingIndicator = mainContent.querySelector('.loading-indicator');

    try {
        // Fetch reports from the backend API endpoint
        const response = await apiRequest('/cases/my-reports/'); // Uses api.js

        if (loadingIndicator) {
            loadingIndicator.style.display = 'none'; // Hide loading indicator
        }

        // Handle both paginated and direct array responses
        let reports = [];
        if (response && Array.isArray(response.results)) {
            // Paginated response
            reports = response.results;
        } else if (response && Array.isArray(response)) {
            // Direct array response
            reports = response;
        } else {
            console.error("Invalid response structure for reports:", response);
            mainContent.innerHTML += '<p>Could not load your reports. Invalid response format.</p>';
            return;
        }

        if (reports.length === 0) {
            mainContent.innerHTML += '<p>You have not submitted any reports yet.</p>';
        } else {
            let reportListHTML = '<ul class="report-list">'; // Add a class for styling
            reports.forEach(report => {
                reportListHTML += `
                    <li>
                        <a href="#" class="view-case-link" data-case-id="${report.case}">
                            ${report.case_title || `Case ID ${report.case}`}
                        </a>
                        - Submitted on ${new Date(report.submitted_at).toLocaleDateString()}
                    </li>`;
            });
            reportListHTML += '</ul>';
            mainContent.innerHTML += reportListHTML;

            // Add event listeners to the newly created links
            mainContent.querySelectorAll('.view-case-link').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const caseId = e.target.getAttribute('data-case-id');
                    if (caseId) {
                        viewCase(caseId);
                    } else {
                        console.error("View case link clicked, but no case ID found.");
                        showToast("Could not load case: ID missing.", "error");
                    }
                });
            });
        }
    } catch (error) {
        console.error("Failed to load reports:", error);
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        mainContent.innerHTML += `<p>Error loading reports: ${error.message || 'Unknown error'}</p>`;
    }
}

function getBodyPartFromSubspecialty(subspecialty) {
    switch (subspecialty) {
        case 'neuro':
            return 'brain';
        case 'head-neck':
            return 'head-neck';
        case 'chest':
            return 'chest';
        case 'abdomen':
            return 'abdomen';
        case 'msk':
            return 'msk';
        default:
            return 'general';
    }
}
 // --- View Case Detail ---

// In frontend/js/main.js

// --- View Case Detail ---
async function viewCase(caseId) {
    console.log(`--- viewCase called for caseId: ${caseId} ---`);
    const mainContent = document.getElementById('mainContent');
    if (!mainContent) {
        console.error("Main content area #mainContent not found for displaying case detail.");
        return;
    }

    mainContent.innerHTML = `<div class="loading-indicator" style="padding: 20px;">Loading case details for Case ID ${caseId}...</div>`;

    try {
        const caseData = await apiRequest(`/cases/cases/${caseId}/`);

        if (!caseData || typeof caseData.id === 'undefined') {
            console.error("Case data not found or invalid structure from API for ID:", caseId, caseData);
            showToast(`Case ID ${caseId} not found or error loading details.`, 'error');
            mainContent.innerHTML = `<p>Error: Could not load details for Case ID ${caseId}.</p>
                                     <button id="backToCasesBtnListError" class="btn btn-secondary">Back to Cases</button>`;
            document.getElementById('backToCasesBtnListError')?.addEventListener('click', () => loadCaseList());
            return;
        }

        // Mark case as viewed
        try {
            await apiRequest(`/cases/cases/${caseId}/viewed/`, { method: 'POST' });
            console.log(`Case ${caseId} marked as viewed.`);
        } catch (viewError) {
            console.warn(`Could not mark case ${caseId} as viewed:`, viewError);
            // Non-critical, so we continue
        }

        const caseDetailHTML = `
            <style>
                #caseDetailContainer {
                    display: flex;
                    flex-direction: row;
                    gap: 20px;
                    padding-top: 15px;
                }
                #caseImagingColumn {
                    flex: 1;
                    min-width: 300px;
                    height: calc(100vh - 150px);
                    overflow-y: auto;
                    padding-right: 15px;
                    border-right: 1px solid #eee;
                    display: flex;
                    flex-direction: column;
                    /* align-items: center; */ /* Let content align naturally */
                    justify-content: flex-start;
                }
                #caseInfoColumn {
                    flex: 0 0 480px;
                    max-width: 480px;
                    height: calc(100vh - 150px);
                    overflow-y: auto;
                    padding-left: 15px;
                }
                .case-detail-header-main {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #ddd;
                }
                .case-section-title {
                    margin-top: 20px;
                    margin-bottom: 10px;
                    color: #333;
                    font-size: 1.1em;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 5px;
                }
                /* Styles for user submitted report section, copied from previous response */
                .user-submitted-report-content {
                    margin-top: 20px;
                    padding: 20px;
                    background-color: #eef5ff;
                    border: 1px solid #cce7ff;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }
                .user-submitted-report-content .case-section-title {
                    color: #0056b3;
                    margin-bottom: 10px;
                }
                .user-submitted-report-content ul {
                    list-style: none;
                    padding-left: 0;
                }
                .user-submitted-report-content li {
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 1px dotted #bedcf5;
                }
                 .user-submitted-report-content li:last-child {
                    border-bottom: none;
                }
                .user-submitted-report-content strong {
                    display: block;
                    margin-bottom: 5px;
                    font-size: 1.05em;
                }
                .user-submitted-report-content div { /* For the content text */
                     padding-left: 10px;
                     white-space: pre-wrap;
                     word-wrap: break-word;
                }
                @media (max-width: 860px) {
                    #caseDetailContainer {
                        flex-direction: column-reverse;
                    }
                    #caseInfoColumn, #caseImagingColumn {
                        flex-basis: auto;
                        max-width: none;
                        height: auto;
                        overflow-y: visible;
                        border-right: none;
                        padding-right: 0;
                        padding-left: 0;
                        margin-bottom: 20px;
                    }
                    #caseImagingColumn {
                         border-top: 1px solid #eee;
                         padding-top: 20px;
                         margin-bottom: 0;
                    }
                }
            </style>

            <div id="caseDetailView">
                <div class="case-detail-header-main">
                    <div>
                        <h2 class="case-detail-title" style="margin-bottom: 5px;">${caseData.title || 'Untitled Case'}</h2>
                        <div class="case-detail-meta">
                            Subspecialty: <span>${caseData.subspecialty_display || caseData.subspecialty || 'N/A'}</span> |
                            Modality: <span>${caseData.modality_display || caseData.modality || 'N/A'}</span> |
                            Difficulty: <span>${caseData.difficulty_display || caseData.difficulty || 'N/A'}</span>
                        </div>
                        <div class="tags" style="margin-top: 5px;">
                            <span class="tag">${caseData.subspecialty_display || caseData.subspecialty || 'N/A'}</span>
                            <span class="tag">${caseData.modality_display || caseData.modality || 'N/A'}</span>
                            <span class="tag difficulty-${(caseData.difficulty_display || caseData.difficulty || 'unknown').toLowerCase().replace(/\s+/g, '-')}">
                                ${caseData.difficulty_display || caseData.difficulty || 'Unknown'}
                            </span>
                        </div>
                    </div>
                    <div>
                        <button class="btn btn-secondary" id="backToCasesBtn">Back to Cases</button>
                    </div>
                </div>

                <div id="caseDetailContainer">
                    <div id="caseImagingColumn">
                        <h3 class="case-section-title">Imaging</h3>
                        <div id="dicomViewerContainer" style="width:100%; height:600px; min-height:500px; border:1px solid #ccc; background-color: #f0f0f0; display:flex; align-items:center; justify-content:center;">
                            <iframe id="dicomViewerFrame" style="width:100%; height:100%; border:none;" title="DICOM Study Viewer">
                                <p>Your browser does not support iframes, or an error occurred loading the DICOM viewer.</p>
                            </iframe>
                        </div>
                        <p id="dicomLoadingMessage" style="text-align:center; margin-top:10px; display:none;">Loading DICOM images...</p>
                        <p id="dicomErrorMessage" style="color:red; text-align:center; margin-top:10px; display:none;">Could not load DICOM images.</p>
                    </div>

                    <div id="caseInfoColumn">
                        <div class="case-clinical-info">
                            <h3 class="case-section-title">Clinical Information</h3>
                            <p><strong>Patient Age:</strong> ${caseData.patient_age_display || caseData.patient_age || 'N/A'}</p>
                            <p>${caseData.clinical_history || 'No clinical history provided.'}</p>
                        </div>

                        <div id="reportSubmissionSection" class="case-report-template">
                            <h3 class="case-section-title">Your Report</h3>
                            <form id="reportForm" data-case-id="${caseData.id}">
                                <div id="dynamicReportSectionsContainer">
                                    <p>Loading report template...</p>
                                </div>
                                <div class="form-actions" style="margin-top:15px;">
                                    <button type="submit" class="btn">Submit Report</button>
                                </div>
                            </form>
                        </div>

                        <div id="userSubmittedReportSection" class="user-submitted-report-content" style="display: none;">
                            <h3 class="case-section-title" style="color: #0056b3;">Your Submitted Report</h3>
                            <p>Loading your report...</p>
                        </div>

                        <div id="expertDiscussionSection" class="expert-analysis-content" style="display: none;">
                            <h3 class="case-section-title">Expert Analysis</h3>
                            <div id="expertLanguageSelector" style="margin-bottom:10px;"></div>
                            <div id="expertTemplateContentContainer">
                                <p>Select a language to view expert analysis.</p>
                            </div>
                            <p><strong>Key Findings (Expert):</strong> ${caseData.key_findings || 'Not available.'}</p>
                            <p><strong>Diagnosis (Expert):</strong> ${caseData.diagnosis || 'Not available.'}</p>
                            <p><strong>Discussion (Expert):</strong> ${caseData.discussion || 'Not available.'}</p>
                            ${caseData.references ? `<p><strong>References:</strong> ${caseData.references}</p>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;

        mainContent.innerHTML = caseDetailHTML; // Render the base HTML

        // Setup event listeners and dynamic content loading
        document.getElementById('backToCasesBtn')?.addEventListener('click', () => loadCaseList());

        const reportForm = document.getElementById('reportForm');
        if (reportForm) {
            reportForm.addEventListener('submit', handleReportSubmit);
        }

        if (caseData.master_template_details) {
            renderMasterTemplateForReporting(caseData.master_template_details, 'dynamicReportSectionsContainer');
        } else {
            console.warn("Case does not have master_template_details. Cannot render report form sections.");
            const reportContainer = document.getElementById('dynamicReportSectionsContainer');
            if (reportContainer) {
                reportContainer.innerHTML = "<p><em>No report template is associated with this case, or template details are missing. Cannot submit a report.</em></p>";
            }
            reportForm?.querySelector('button[type="submit"]')?.remove();
        }

        // ***** START NEW JS LOGIC FOR IFRAME *****
        const dicomViewerFrame = document.getElementById('dicomViewerFrame');
        const dicomViewerContainer = document.getElementById('dicomViewerContainer');
        const dicomLoadingMessage = document.getElementById('dicomLoadingMessage');
        const dicomErrorMessage = document.getElementById('dicomErrorMessage');

        if (caseData.orthanc_study_uid && dicomViewerFrame && dicomViewerContainer) {
            if (dicomLoadingMessage) dicomLoadingMessage.style.display = 'block';
            if (dicomErrorMessage) dicomErrorMessage.style.display = 'none';
            dicomViewerFrame.style.display = 'block';

            const orthancOhifViewerBaseUrl = "http://localhost:8042/ohif/viewer"; // Ensure this is your correct Orthanc OHIF base URL
            const dicomSrcUrl = `${orthancOhifViewerBaseUrl}?StudyInstanceUIDs=${caseData.orthanc_study_uid}`;

            console.log("Attempting to load DICOM study in iframe from URL:", dicomSrcUrl);
            dicomViewerFrame.src = dicomSrcUrl;

            dicomViewerFrame.onload = function() {
                console.log("DICOM iframe content loaded (or attempted to load).");
                if (dicomLoadingMessage) dicomLoadingMessage.style.display = 'none';
            };
            dicomViewerFrame.onerror = function() {
                console.error("Error loading DICOM iframe content.");
                if (dicomLoadingMessage) dicomLoadingMessage.style.display = 'none';
                if (dicomErrorMessage) dicomErrorMessage.style.display = 'block';
                dicomViewerFrame.style.display = 'none';
            };

        } else if (dicomViewerContainer) {
            console.warn("No orthanc_study_uid for this case, or DICOM viewer elements not found.");
            if (dicomViewerFrame) dicomViewerFrame.style.display = 'none';
            if (dicomLoadingMessage) dicomLoadingMessage.style.display = 'none';
            if (dicomErrorMessage) dicomErrorMessage.style.display = 'none';
            dicomViewerContainer.innerHTML = '<p style="text-align:center; padding:20px; color:#777;">No DICOM images are associated with this case.</p>';
        }
        // ***** END NEW JS LOGIC FOR IFRAME *****

        // Conditional display logic for report form, user's report, and expert analysis
        if (caseData.is_reported_by_user) {
            const reportSubmissionSection = document.getElementById('reportSubmissionSection');
            if (reportSubmissionSection) reportSubmissionSection.style.display = 'none';

            const discussionSection = document.getElementById('expertDiscussionSection');
            if (discussionSection) discussionSection.style.display = 'block';
            populateExpertLanguageSelector(caseData.id, caseData.applied_templates || []);

            await displayUserSubmittedReport(caseData.id); // Display user's existing report
        } else {
            // User has not reported, show submission form
            const reportSubmissionSection = document.getElementById('reportSubmissionSection');
            if (reportSubmissionSection) reportSubmissionSection.style.display = 'block';

            // Hide user report and expert analysis sections if they haven't submitted
            const userReportDisplay = document.getElementById('userSubmittedReportSection');
            if(userReportDisplay) userReportDisplay.style.display = 'none';
            const discussionSection = document.getElementById('expertDiscussionSection');
            if (discussionSection) discussionSection.style.display = 'none';
        }

    } catch (error) {
        console.error(`Failed to fetch or display case ID ${caseId}:`, error);
        mainContent.innerHTML = `<p>Error loading case: ${error.message || 'Unknown error'}. Please try again.</p>
                                 <button id="backToCasesBtnError" class="btn btn-secondary">Back to Cases</button>`;
        document.getElementById('backToCasesBtnError')?.addEventListener('click', () => loadCaseList());
        showToast(`Error loading case: ${error.message || 'Unknown error'}`, 'error');
    }
}


    async function populateExpertLanguageSelector(caseId, appliedTemplates) {
        const selectorContainer = document.getElementById('expertLanguageSelector');
        const contentContainer = document.getElementById('expertTemplateContentContainer');
        if (!selectorContainer || !contentContainer) return;

        selectorContainer.innerHTML = '<strong>View Expert Report In:</strong> ';

        if (!appliedTemplates || appliedTemplates.length === 0) {
            selectorContainer.innerHTML += ' <span>No expert versions available.</span>';
            contentContainer.innerHTML = '';
            return;
        }

        appliedTemplates.forEach((template, index) => {
            const langButton = document.createElement('button');
            langButton.className = 'btn btn-sm btn-outline-secondary expert-lang-btn';
            langButton.style.marginLeft = '5px';
            langButton.textContent = template.language_name || template.language_code;
            langButton.dataset.languageCode = template.language_code;
            langButton.dataset.caseTemplateId = template.id; // Store the CaseTemplate ID

            langButton.onclick = async () => {
                document.querySelectorAll('.expert-lang-btn').forEach(btn => btn.classList.remove('active'));
                langButton.classList.add('active');
                contentContainer.innerHTML = `<p>Loading ${template.language_name} expert report...</p>`;
                try {
                    // Fetch the specific expert template content using its CaseTemplate ID
                    // The project doc mentions GET /api/cases/cases/<case_pk>/expert-templates/<language_code>/
                    // OR, if we have the CaseTemplate ID, we might have a direct endpoint like /api/cases/admin/case-templates/<casetemplate_pk>/
                    // Let's use the user-facing one for now.
                    const expertContent = await apiRequest(`/cases/cases/${caseId}/expert-templates/${template.language_code}/`);
                    
                    if (expertContent && expertContent.section_contents) {
                        let html = '<ul>';
                        expertContent.section_contents.forEach(section => {
                            html += `<li><strong>${section.master_section_name}:</strong><p>${section.content || '<em>No content provided.</em>'}</p></li>`;
                        });
                        html += '</ul>';
                        contentContainer.innerHTML = html;
                    } else {
                        contentContainer.innerHTML = '<p>Could not load expert report content.</p>';
                    }
                } catch (err) {
                    console.error("Error fetching expert template content:", err);
                    contentContainer.innerHTML = `<p>Error loading expert report: ${err.message}</p>`;
                }
            };
            selectorContainer.appendChild(langButton);

            // Automatically click the first language button
            if (index === 0) {
                langButton.click();
            }
        });
    }

// js/main.js

// Renders the MasterTemplate sections as form fields for report submission.
// This version dynamically creates input fields for each section in the masterTemplateData.
function renderMasterTemplateForReporting(masterTemplateData, containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with ID '${containerId}' not found for rendering master template.`);
        return;
    }

    const reportForm = document.getElementById('reportForm'); // Get the form element

    // Ensure the submit button is present if we are rendering a form
    // This is important if the container was previously emptied due to an error.
    if (reportForm) {
        let submitButton = reportForm.querySelector('button[type="submit"]');
        if (!submitButton) {
            const actionsDiv = reportForm.querySelector('.form-actions') || document.createElement('div');
            if (!actionsDiv.classList.contains('form-actions')) {
                actionsDiv.className = 'form-actions';
                actionsDiv.style.marginTop = '15px'; // Ensure consistent styling
                // Insert actionsDiv before other content if it was created, or append if form was empty
                if (reportForm.firstChild && actionsDiv !== reportForm.querySelector('.form-actions')) {
                     reportForm.insertBefore(actionsDiv, reportForm.firstChild.nextSibling); // Try to place it reasonably
                } else if (actionsDiv !== reportForm.querySelector('.form-actions')) {
                    reportForm.appendChild(actionsDiv);
                }
            }
            submitButton = document.createElement('button');
            submitButton.type = 'submit';
            submitButton.className = 'btn';
            submitButton.textContent = 'Submit Report';
            actionsDiv.appendChild(submitButton);
        }
    }


    if (!masterTemplateData || !masterTemplateData.sections || !Array.isArray(masterTemplateData.sections)) {
        container.innerHTML = '<p>Could not load report template structure: Invalid master template data provided.</p>';
        console.warn("Invalid or missing masterTemplateData or sections:", masterTemplateData);
        reportForm?.querySelector('button[type="submit"]')?.remove(); // Remove submit if no template
        return;
    }
    
    if (masterTemplateData.sections.length === 0) {
        container.innerHTML = '<p>This case uses a master template that currently has no defined sections. Cannot create a report.</p>';
        reportForm?.querySelector('button[type="submit"]')?.remove(); // Remove submit if no sections
        return;
    }

    let formHTML = '';
    // Ensure sections are sorted by their 'order' property
    const sortedSections = [...masterTemplateData.sections].sort((a, b) => (a.order || 0) - (b.order || 0));

    sortedSections.forEach(section => {
        // Each textarea needs a unique 'name' attribute for form submission.
        // We also add data attributes to easily retrieve section ID and name for submission.
        const initialContent = section.placeholder_text || ''; // Use placeholder as initial editable value
        // Basic sanitization for content directly injected into textarea value
        const escapedInitialContent = initialContent.replace(/</g, "&lt;").replace(/>/g, "&gt;");

        formHTML += `
            <div class="report-section" style="margin-bottom: 15px;">
                <label for="report_section_${section.id}" style="display:block; font-weight:bold; margin-bottom:5px;">
                    ${section.name || 'Unnamed Section'} ${section.is_required ? '<span style="color:red;">*</span>' : ''}
                </label>
                <textarea id="report_section_${section.id}" 
                          name="section_content_for_master_section_${section.id}" /* Unique name for FormData if used, though JS reads directly */
                          class="form-control report-section-textarea" /* Added class for easier selection */
                          rows="4" 
                          data-section-name="${section.name || 'Unnamed Section'}" 
                          data-section-id="${section.id}" /* Store MasterTemplateSection ID */
                          ${section.is_required ? 'required' : ''}>${escapedInitialContent}</textarea>
            </div>
        `;
    });
    container.innerHTML = formHTML;
    console.log("Fully dynamic report form rendered based on Master Template sections.");
}

async function displayUserSubmittedReport(caseId) {
    const userReportContainer = document.getElementById('userSubmittedReportSection');
    if (!userReportContainer) {
        console.warn("User report container 'userSubmittedReportSection' not found in the DOM.");
        return;
    }

    userReportContainer.innerHTML = `
        <h3 class="case-section-title" style="color: #0056b3; margin-bottom: 10px;">Your Submitted Report</h3>
        <p>Loading your submitted report...</p>`;
    userReportContainer.style.display = 'block';

    try {
        const myReportsResponse = await apiRequest('/cases/my-reports/');
        let reports = [];
        if (myReportsResponse && Array.isArray(myReportsResponse.results)) {
            reports = myReportsResponse.results;
        } else if (myReportsResponse && Array.isArray(myReportsResponse)) {
            reports = myReportsResponse;
        } else {
            console.warn("Unexpected response format for /cases/my-reports/ endpoint:", myReportsResponse);
        }

        const reportForThisCase = reports.find(report =>
            (report.case && String(report.case) === String(caseId)) ||
            (report.case && typeof report.case === 'object' && String(report.case.id) === String(caseId)) ||
            (report.case_id && String(report.case_id) === String(caseId))
        );

        if (reportForThisCase && reportForThisCase.structured_content && Array.isArray(reportForThisCase.structured_content)) {
            let html = `<h3 class="case-section-title" style="color: #0056b3; margin-bottom: 10px;">Your Submitted Report</h3>`;
            if (reportForThisCase.submitted_at) {
                html += `<p style="font-size: 0.9em; color: #555; margin-bottom: 15px;">Submitted on: ${new Date(reportForThisCase.submitted_at).toLocaleString()}</p>`;
            }
            html += '<ul style="list-style: none; padding-left: 0;">';
            reportForThisCase.structured_content.forEach(section => {
                const sectionName = section.section_name || `Section ID ${section.master_template_section_id || 'N/A'}`;
                const sectionContent = section.content || '<em>No content submitted for this section.</em>';
                html += `
                    <li style="margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px dotted #ddd;">
                        <strong style="display: block; margin-bottom: 5px; font-size: 1.05em;">${sectionName}:</strong>
                        <div style="padding-left: 10px; white-space: pre-wrap; word-wrap: break-word;">${sectionContent}</div>
                    </li>`;
            });
            html += '</ul>';

            // ***** START: ADD AI FEEDBACK BUTTON & CONTAINER *****
            html += `
                <div style="text-align: right; margin-top: 20px; padding-top:15px; border-top: 1px solid #ddd_feedback;">
                    <button class="btn btn-secondary btn-sm get-ai-feedback-btn" data-report-id="${reportForThisCase.id}">Get AI Feedback</button>
                </div>
                <div id="aiFeedbackContainerForReport_${reportForThisCase.id}" class="ai-feedback-container" style="margin-top: 15px; padding: 15px; background-color: #fff9e6; border: 1px solid #ffecb3; border-radius: 6px; display:none; white-space: pre-wrap; word-wrap: break-word;">
                    <h4 style="color: #b08c00; margin-top:0; margin-bottom:10px;">AI Feedback:</h4>
                    <p class="ai-feedback-loading-message">Loading feedback...</p>
                    <div class="ai-feedback-content"></div>
                </div>
            `;
            // ***** END: ADD AI FEEDBACK BUTTON & CONTAINER *****

            userReportContainer.innerHTML = html;

            // ***** ADD EVENT LISTENER FOR THE NEW BUTTON *****
            const aiFeedbackBtn = userReportContainer.querySelector(`.get-ai-feedback-btn[data-report-id="${reportForThisCase.id}"]`);
            if (aiFeedbackBtn) {
                aiFeedbackBtn.addEventListener('click', async () => {
                    const reportId = aiFeedbackBtn.dataset.reportId;
                    const feedbackDisplayDiv = document.querySelector(`#aiFeedbackContainerForReport_${reportId} .ai-feedback-content`);
                    const feedbackContainer = document.getElementById(`aiFeedbackContainerForReport_${reportId}`);
                    const loadingMessageP = feedbackContainer.querySelector('.ai-feedback-loading-message');


                    if (feedbackContainer && feedbackDisplayDiv && loadingMessageP) {
                        feedbackContainer.style.display = 'block';
                        loadingMessageP.style.display = 'block';
                        feedbackDisplayDiv.innerHTML = ''; // Clear previous feedback
                        aiFeedbackBtn.disabled = true;
                        aiFeedbackBtn.textContent = "Getting Feedback...";

                        try {
                            console.log(`Requesting AI feedback for report ID: ${reportId}`);
                            const feedbackResponse = await apiRequest(`/cases/reports/${reportId}/ai-feedback/`); // GET request
                            
                            if (feedbackResponse && feedbackResponse.feedback) {
                                console.log("AI Feedback received:", feedbackResponse.feedback);
                                feedbackDisplayDiv.textContent = feedbackResponse.feedback; // Using textContent to preserve formatting from LLM
                            } else {
                                console.warn("Could not retrieve valid AI feedback from response:", feedbackResponse);
                                feedbackDisplayDiv.innerHTML = '<p style="color:red;">Could not retrieve AI feedback at this time.</p>';
                            }
                        } catch (error) {
                            console.error("Error fetching AI feedback:", error);
                            feedbackDisplayDiv.innerHTML = `<p style="color:red;">Error fetching AI feedback: ${error.message || 'Unknown error'}</p>`;
                        } finally {
                            loadingMessageP.style.display = 'none';
                            aiFeedbackBtn.disabled = false;
                            aiFeedbackBtn.textContent = "Get AI Feedback";
                        }
                    } else {
                        console.error("Could not find elements for displaying AI feedback for report " + reportId);
                    }
                });
            }
            // ***** END OF EVENT LISTENER *****

        } else {
            userReportContainer.innerHTML = `
                <h3 class="case-section-title" style="color: #0056b3; margin-bottom: 10px;">Your Submitted Report</h3>
                <p>You have not submitted a report for this case, or your report could not be loaded.</p>`;
        }
    } catch (error) {
        console.error("Error fetching or displaying user's submitted report:", error);
        userReportContainer.innerHTML = `
            <h3 class="case-section-title" style="color: #0056b3; margin-bottom: 10px;">Your Submitted Report</h3>
            <p style="color:red;">Error loading your report: ${error.message || 'Unknown error'}</p>`;
    }
}
// Handle Report Submission
async function handleReportSubmit(event) {
    console.log("--- handleReportSubmit called (dynamic sections version) ---");
    event.preventDefault();
    const form = event.target;
    const caseId = form.getAttribute('data-case-id');
    const submitButton = form.querySelector('button[type="submit"]');

    if (!submitButton) {
        console.error("Submit button not found inside report form.");
        showToast("Error: Submit button missing.", "error");
        return;
    }

    const reportSectionsContainer = document.getElementById('dynamicReportSectionsContainer');
    if (!reportSectionsContainer) {
        console.error("Dynamic report sections container not found.");
        showToast("Error: Report form structure is missing.", "error");
        return;
    }

    const sectionTextareas = reportSectionsContainer.querySelectorAll('textarea');
    const reportContents = [];
    let allRequiredFilled = true;

    sectionTextareas.forEach(textarea => {
        const sectionId = textarea.dataset.sectionId; // Assuming data-section-id holds the MasterTemplateSection ID
        const sectionName = textarea.dataset.sectionName || 'Unnamed Section'; // For error messages
        const content = textarea.value.trim();
        const isRequired = textarea.hasAttribute('required');

        if (isRequired && !content) {
            allRequiredFilled = false;
            showToast(`Please fill in the required section: "${sectionName}"`, 'error');
            textarea.classList.add('error'); // Add some visual feedback
            // Consider focusing the first empty required field:
            if (allRequiredFilled) { // only focus the first one
                 textarea.focus();
            }
        } else {
            textarea.classList.remove('error');
        }

        reportContents.push({
            master_template_section_id: parseInt(sectionId), // Send the ID of the MasterTemplateSection
            content: content
        });
    });

    if (!allRequiredFilled) {
        return; // Stop submission if a required field is empty
    }

    if (reportContents.length === 0) {
        showToast("Cannot submit an empty report. Please fill in the sections.", "warning");
        return;
    }

    submitButton.disabled = true;
    submitButton.textContent = 'Submitting...';

    try {
        const reportPayload = {
            case_id: parseInt(caseId),
            // The backend will now expect 'structured_content' or similar,
            // instead of 'findings' and 'impression'.
            // Let's name it 'section_details' for now.
            section_details: reportContents
        };
        console.log("Submitting structured report data:", reportPayload);

        // IMPORTANT: The backend endpoint '/api/cases/reports/' and its serializer
        // will need to be updated to accept this 'section_details' structure.
        const response = await apiRequest('/cases/reports/', {
            method: 'POST',
            body: JSON.stringify(reportPayload)
        });

        console.log("Report submission response:", response);
        showToast("Report submitted successfully!", 'success');

        // UI updates after successful submission:
        // Disable form fields
        sectionTextareas.forEach(textarea => {
            textarea.disabled = true;
        });
        submitButton.remove(); // Remove submit button

        // Show the expert discussion section
        const discussionSection = document.getElementById('expertDiscussionSection');
        if (discussionSection) {
            discussionSection.style.display = 'block';
        }
        
        // Refresh case data to get updated is_reported_by_user status for the main caseData object
        // This is useful if the user stays on the page.
        try {
            const updatedCaseData = await apiRequest(`/cases/cases/${caseId}/`);
            if (updatedCaseData && typeof updatedCaseData.id !== 'undefined') {
                // If you store the main caseData globally in viewCase scope, update it.
                // For now, just log. The expert section population will use its own fetch or passed data.
                console.log("Refreshed case data after report submission:", updatedCaseData);
                // Re-populate expert language selector if needed, or ensure it uses fresh data
                populateExpertLanguageSelector(updatedCaseData.id, updatedCaseData.applied_templates || []);
            }
        } catch (refreshError) {
            console.warn("Could not refresh case data after report submission:", refreshError);
        }


    } catch (error) {
        console.error("Failed to submit report:", error);
        const errorMessage = error.data?.detail || (error.data && typeof error.data === 'object' ? JSON.stringify(error.data) : error.message) || "Failed to submit report.";
        showToast(`Error: ${errorMessage}`, 'error');
        submitButton.disabled = false;
        submitButton.textContent = 'Submit Report';
    }
}
// Handle Logout (Example)
function handleLogout() {
    // ... (handleLogout function remains the same as previous version) ...
    console.log("--- handleLogout called ---");
    clearAuthTokens(); // From api.js
    sessionStorage.removeItem('user'); // Clear stored user data
    showToast("You have been logged out.", "success");
    // Redirect to login page after a short delay
    setTimeout(() => { window.location.href = 'login.html'; }, 1000);
}

// Add showToast function if not already globally available (e.g., from auth.js)
if (!window.showToast) {
    // ... (showToast function remains the same as previous version) ...
    console.log("Defining window.showToast function.");
    window.showToast = function(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer'); // Assumes container exists in index.html
        if (!toastContainer) { console.warn('Toast container not found.'); return; }
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => { toast.remove(); }, 3000);
    };
}

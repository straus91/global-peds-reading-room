// js/main.js - Main application logic for Global Peds Reading Room

// Assume api.js is loaded first (provides apiRequest, getAuthTokens, clearAuthTokens)

document.addEventListener('DOMContentLoaded', function() {
    console.log("--- DOMContentLoaded event fired ---");

    // Initial setup: Check login status, load default view etc.
    checkLoginStatusAndInit();

    // Setup Navigation Links
    setupNavigationListeners();
});

// Setup all navigation link event listeners
function setupNavigationListeners() {
    // Cases tab
    const casesLinkElement = document.getElementById('casesLink');
    casesLinkElement?.addEventListener('click', (e) => {
        console.log("--- Cases link clicked! ---");
        e.preventDefault();
        document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
        casesLinkElement.classList.add('active');
        loadCaseList(); // Load cases when nav link is clicked
    });

    // My Reports tab
    const myReportsLinkElement = document.getElementById('myReportsLink');
    myReportsLinkElement?.addEventListener('click', (e) => {
        console.log("--- My Reports link clicked! ---");
        e.preventDefault();
        document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
        myReportsLinkElement.classList.add('active');
        loadMyReports();
    });

    // Profile link in user menu dropdown
    const profileLinkElement = document.getElementById('profileLink');
    profileLinkElement?.addEventListener('click', (e) => {
        console.log("--- Profile link clicked! ---");
        e.preventDefault();
        showToast("Profile feature not yet implemented.", "info");
    });

    // Logout link in user menu dropdown
    const logoutLinkElement = document.getElementById('logoutLink');
    logoutLinkElement?.addEventListener('click', (e) => {
        console.log("--- Logout link clicked! ---");
        e.preventDefault();
        handleLogout();
    });
}

// Check login status and initialize the main view
async function checkLoginStatusAndInit() {
    console.log("--- checkLoginStatusAndInit called ---");
    const tokens = getAuthTokens(); // from api.js
    if (!tokens) {
        console.log("No auth tokens found, redirecting to login.");
        window.location.href = 'login.html';
        return;
    }

    try {
        // Verify token / fetch user details
        const user = await fetchUserDetails();
        if (user) {
            console.log("User details fetched/found:", user);
            updateUserMenu(user); // Update header with user info
            
            // Show admin link if user is admin
            if (user.isAdmin) {
                const adminLink = document.getElementById('adminLink');
                if(adminLink) {
                    console.log("User is admin, showing admin link.");
                    adminLink.style.display = 'inline'; // Or 'block' depending on layout
                }
            }
            
            // Check URL hash for direct case viewing
            const hash = window.location.hash;
            if (hash && hash.startsWith('#case/')) {
                const caseId = hash.split('/')[1];
                if (caseId) {
                    console.log(`Direct case viewing via URL hash: ${caseId}`);
                    viewCase(caseId);
                    return;
                }
            }
            
            // Show cases tab by default if no specific route
            loadCaseList();
            document.getElementById('casesLink')?.classList.add('active');
        } else {
            throw new Error("User data not found.");
        }
    } catch (error) {
        console.error("Authentication check failed:", error);
        clearAuthTokens(); // Clear invalid tokens
        window.location.href = 'login.html'; // Redirect to login
    }
}

// Fetch user details
async function fetchUserDetails() {
    console.log("--- fetchUserDetails called ---");
    // Check sessionStorage first if storing user details there after login
    const storedUser = sessionStorage.getItem('user');
    if (storedUser) {
        try {
            console.log("Found user details in sessionStorage.");
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
                // Ensure is_admin comes from the API response
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

// Update user menu in the header
function updateUserMenu(user) {
    console.log("--- updateUserMenu called ---");
    const userMenuContainer = document.querySelector('.user-menu');
    if (!userMenuContainer) {
        console.warn("User menu container not found.");
        return;
    }

    const userNameSpan = userMenuContainer.querySelector('span');
    if (userNameSpan) {
        userNameSpan.textContent = user.name || user.email;
    } else {
        console.warn("User name span not found in user menu.");
    }
}

// Handle Logout
function handleLogout() {
    console.log("--- handleLogout called ---");
    clearAuthTokens(); // From api.js
    sessionStorage.removeItem('user'); // Clear stored user data
    showToast("You have been logged out.", "success");
    // Redirect to login page after a short delay
    setTimeout(() => { window.location.href = 'login.html'; }, 1000);
}
// --- Load Case List View ---
async function loadCaseList(url = '/cases/cases/') {
    console.log(`--- loadCaseList called with url: ${url} ---`);
    const mainContent = document.getElementById('mainContent');
    if (!mainContent) {
        console.error("Main content area not found.");
        return;
    }

    // Set HTML structure for case list
    mainContent.innerHTML = `
        <div class="case-list-header">
            <h2>Radiology Cases</h2>
            <div class="filters">
                <select id="filterSubspecialty"><option value="">All Subspecialties</option></select>
                <select id="filterModality"><option value="">All Modalities</option></select>
                <select id="filterDifficulty"><option value="">All Difficulties</option></select>
                <button id="applyFiltersBtn">Apply Filters</button>
            </div>
        </div>

        <div class="loading-indicator">Loading cases...</div>

        <div class="case-list-split-view">
            <div class="case-grid-panel">
                 <h3>Case Grid View</h3>
                 <div class="case-grid" id="caseGrid"></div>
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
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="pagination" id="casePagination"></div>
    `;

    const gridContainer = document.getElementById('caseGrid');
    const tableBody = document.getElementById('caseTable')?.querySelector('tbody');
    const loadingIndicator = mainContent.querySelector('.loading-indicator');
    const paginationContainer = document.getElementById('casePagination');

    if (!gridContainer || !tableBody || !loadingIndicator || !paginationContainer) {
        console.error("Required elements for case list not found in loaded HTML.");
        return;
    }

    // Setup filter dropdowns (placeholder functionality for now)
    setupFilters();

    try {
        // Fetch published cases from the backend API endpoint
        console.log(`Fetching cases from ${url}`);
        const response = await apiRequest(url);

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

// Setup placeholder filters (implementation to be expanded later)
function setupFilters() {
    // Just setup basic click handler for now
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', () => {
            showToast("Filtering functionality will be implemented in the next update.", "info");
        });
    }
}

// Render cases into the grid view
function renderCaseGrid(container, cases) {
    container.innerHTML = '';
    if (!cases || cases.length === 0) {
        container.innerHTML = '<p>No published cases found at the moment.</p>';
        return;
    }

    cases.forEach(caseData => {
        const card = document.createElement('div');
        card.className = 'case-card';
        
        if (caseData.is_reported_by_user) {
            card.classList.add('reported');
        } else if (caseData.is_viewed_by_user) {
            card.classList.add('viewed');
        }

        const thumbnailUrl = `https://placehold.co/300x200/eee/666?text=${caseData.modality || 'Case'}`;

        card.innerHTML = `
            <img src="${thumbnailUrl}" alt="Case thumbnail" onerror="this.src='https://placehold.co/300x200/eee/ccc?text=No+Image';">
            <h4>${caseData.title || 'Untitled Case'}</h4>
            <p>
                Modality: ${caseData.modality || 'N/A'}<br>
                Subspecialty: ${caseData.subspecialty || 'N/A'}
            </p>
            <div class="tags">
                <span class="tag difficulty-${(caseData.difficulty || 'unknown').toLowerCase().replace(/\\s+/g, '-')}">
                    ${caseData.difficulty || 'Unknown Difficulty'}
                </span>
                ${caseData.is_reported_by_user ? '<span class="tag status-reported">Reported</span>' : ''}
                ${!caseData.is_reported_by_user && caseData.is_viewed_by_user ? '<span class="tag status-viewed">Viewed</span>' : ''}
            </div>
            <button class="view-case-btn" data-case-id="${caseData.id}">View Case</button>
        `;

        const viewButton = card.querySelector('.view-case-btn');
        viewButton?.addEventListener('click', () => viewCase(caseData.id));
        container.appendChild(card);
    });
}

// Render cases into the table view
function renderCaseTable(tableBody, cases) {
    tableBody.innerHTML = '';
    if (!cases || cases.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No published cases found at the moment.</td></tr>';
        return;
    }

    cases.forEach(caseData => {
        const row = tableBody.insertRow();
        if (caseData.is_reported_by_user) {
            row.className = 'reported';
        } else if (caseData.is_viewed_by_user) {
            row.className = 'viewed';
        }

        const statusText = caseData.is_reported_by_user ? 'Reported' : (caseData.is_viewed_by_user ? 'Viewed' : 'New');
        const addedDate = caseData.published_at ? new Date(caseData.published_at).toLocaleDateString() : 'N/A';

        // Creating cells with content
        const titleCell = row.insertCell();
        titleCell.textContent = caseData.title || 'Untitled Case';

        const subspecialtyCell = row.insertCell();
        subspecialtyCell.textContent = caseData.subspecialty || 'N/A';

        const modalityCell = row.insertCell();
        modalityCell.textContent = caseData.modality || 'N/A';

        const statusCell = row.insertCell();
        statusCell.textContent = statusText;

        const dateCell = row.insertCell();
        dateCell.textContent = addedDate;

        // Add view button
        const actionsCell = row.insertCell();
        const viewButton = document.createElement('button');
        viewButton.className = 'view-case-btn';
        viewButton.textContent = 'View';
        viewButton.dataset.caseId = caseData.id;
        viewButton.addEventListener('click', () => viewCase(caseData.id));
        actionsCell.appendChild(viewButton);
    });
}

// Render pagination controls
function renderPagination(container, totalItems, nextUrl, previousUrl) {
    container.innerHTML = '';
    if (!totalItems || totalItems <= 10) return;

    const prevDisabled = !previousUrl ? 'disabled' : '';
    const nextDisabled = !nextUrl ? 'disabled' : '';

    container.innerHTML = `
        <button class="pagination-btn prev-btn" data-url="${previousUrl || ''}" ${prevDisabled}>Previous</button>
        <span class="page-info"></span>
        <button class="pagination-btn next-btn" data-url="${nextUrl || ''}" ${nextDisabled}>Next</button>
    `;

    container.querySelectorAll('.pagination-btn').forEach(btn => {
        btn.addEventListener('click', handlePaginationClick);
    });

    // Calculate current page
    const pageInfo = container.querySelector('.page-info');
    if (pageInfo) {
        const pageSize = 10;
        let currentPage = 1, totalPages = Math.ceil(totalItems / pageSize);
        
        try {
            if (previousUrl && previousUrl.includes('page=')) {
                currentPage = parseInt(new URL(previousUrl).searchParams.get('page') || '0') + 1;
            } else if (nextUrl && nextUrl.includes('page=')) {
                currentPage = parseInt(new URL(nextUrl).searchParams.get('page') || '2') - 1;
            }
        } catch (e) { console.warn("Could not parse page number from URL", e); }
        
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    }
}

// Handle pagination clicks
async function handlePaginationClick(event) {
    const button = event.target;
    const apiUrl = button.dataset.url;

    if (!apiUrl || button.disabled) return;

    try {
        let relativeApiUrl = '';
        if (apiUrl.startsWith('http')) {
            relativeApiUrl = new URL(apiUrl).pathname + new URL(apiUrl).search;
            relativeApiUrl = relativeApiUrl.replace('/api', ''); // Adjust if needed
        }
        loadCaseList(relativeApiUrl);
    } catch (error) {
        console.error("Failed to handle pagination click:", error);
        showToast("Error loading next page.", "error");
    }
}

// --- View Case Detail Function ---
async function viewCase(caseId) {
    console.log(`--- viewCase called for caseId: ${caseId} ---`);
    const mainContent = document.getElementById('mainContent');
    if (!mainContent) {
        console.error("Main content area not found for displaying case detail.");
        return;
    }

    // Update URL hash for direct linking to case
    window.location.hash = `case/${caseId}`;
    
    mainContent.innerHTML = `<div class="loading-indicator" style="padding: 20px;">Loading case details for Case ID ${caseId}...</div>`;

    try {
        const caseData = await apiRequest(`/cases/cases/${caseId}/`);

        if (!caseData || typeof caseData.id === 'undefined') {
            console.error("Case data not found or invalid structure from API for ID:", caseId);
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

        // Generate and insert HTML for case detail
        renderCaseDetail(caseData);
        
        // Setup DICOM viewer if available
        setupDicomViewer(caseData);
        
        // Setup report submission form or load existing report
        if (caseData.is_reported_by_user) {
            // User has already reported on this case - hide form, show their report
            const reportFormSection = document.getElementById('reportSubmissionSection');
            if (reportFormSection) reportFormSection.style.display = 'none';
            
            // Show expert discussion section
            const expertDiscussionSection = document.getElementById('expertDiscussionSection');
            if (expertDiscussionSection) expertDiscussionSection.style.display = 'block';
            
            // Load expert language selector if templates are available
            populateExpertLanguageSelector(caseData.id, caseData.applied_templates || []);
            
            // Display user's submitted report
            await displayUserSubmittedReport(caseData.id);
        } else {
            // Show report form, hide expert discussion
            const reportFormSection = document.getElementById('reportSubmissionSection');
            if (reportFormSection) reportFormSection.style.display = 'block';
            
            // Hide user report and expert sections if they haven't submitted
            const userReportDisplay = document.getElementById('userSubmittedReportSection');
            if (userReportDisplay) userReportDisplay.style.display = 'none';
            
            const expertDiscussionSection = document.getElementById('expertDiscussionSection');
            if (expertDiscussionSection) expertDiscussionSection.style.display = 'none';
            
            // Render the template form if available
            if (caseData.master_template_details) {
                renderMasterTemplateForReporting(caseData.master_template_details, 'dynamicReportSectionsContainer');
            } else {
                console.warn("Case doesn't have master_template_details. Cannot render report form.");
                const reportContainer = document.getElementById('dynamicReportSectionsContainer');
                if (reportContainer) {
                    reportContainer.innerHTML = "<p><em>No report template is associated with this case.</em></p>";
                }
                const submitBtn = reportFormSection?.querySelector('button[type="submit"]');
                if (submitBtn) submitBtn.style.display = 'none';
            }
        }

    } catch (error) {
        console.error(`Failed to fetch or display case ID ${caseId}:`, error);
        mainContent.innerHTML = `<p>Error loading case: ${error.message || 'Unknown error'}. Please try again.</p>
                                <button id="backToCasesBtnError" class="btn btn-secondary">Back to Cases</button>`;
        document.getElementById('backToCasesBtnError')?.addEventListener('click', () => loadCaseList());
        showToast(`Error loading case: ${error.message || 'Unknown error'}`, 'error');
    }
}

 // Setup DICOM viewer with improved error handling
function setupDicomViewer(caseData) {
    const dicomViewerFrame = document.getElementById('dicomViewerFrame');
    const dicomViewerContainer = document.getElementById('dicomViewerContainer');
    const dicomLoadingMessage = document.getElementById('dicomLoadingMessage');
    const dicomErrorMessage = document.getElementById('dicomErrorMessage');

    if (!dicomViewerContainer) return;

    if (!caseData.orthanc_study_uid) {
        // No DICOM study linked to this case
        if (dicomViewerFrame) dicomViewerFrame.style.display = 'none';
        if (dicomLoadingMessage) dicomLoadingMessage.style.display = 'none';
        if (dicomErrorMessage) dicomErrorMessage.style.display = 'none';
        dicomViewerContainer.innerHTML = '<p style="text-align:center; padding:20px; color:#777;">No DICOM images are associated with this case.</p>';
        return;
    }

    // Case has DICOM study UID - setup viewer
    if (dicomLoadingMessage) dicomLoadingMessage.style.display = 'block';
    if (dicomErrorMessage) dicomErrorMessage.style.display = 'none';
    if (dicomViewerFrame) {
        dicomViewerFrame.style.display = 'block';
        
        const orthancOhifViewerBaseUrl = "http://localhost:8042/ohif/viewer"; // Update with your Orthanc OHIF URL
        const dicomSrcUrl = `${orthancOhifViewerBaseUrl}?StudyInstanceUIDs=${caseData.orthanc_study_uid}`;

        console.log("Loading DICOM study in iframe from URL:", dicomSrcUrl);
        
        // Setup iframe event listeners for load/error
        dicomViewerFrame.onload = function() {
            console.log("DICOM iframe successfully loaded");
            if (dicomLoadingMessage) dicomLoadingMessage.style.display = 'none';
        };
        
        dicomViewerFrame.onerror = function() {
            console.error("Error loading DICOM iframe content");
            if (dicomLoadingMessage) dicomLoadingMessage.style.display = 'none';
            if (dicomErrorMessage) dicomErrorMessage.style.display = 'block';
            dicomViewerFrame.style.display = 'none';
        };
        
        // Set src after setting up listeners
        dicomViewerFrame.src = dicomSrcUrl;
        
        // Additional safety timer to detect loading issues
        setTimeout(() => {
            if (dicomLoadingMessage && dicomLoadingMessage.style.display !== 'none') {
                console.warn("DICOM viewer may be taking too long to load - check if it's accessible");
                dicomLoadingMessage.style.display = 'none';
                dicomErrorMessage.style.display = 'block';
                dicomErrorMessage.textContent = "DICOM viewer is taking too long to load. Please check if your Orthanc server is running and accessible.";
            }
        }, 15000); // 15 second timeout
    }
}

// Render the base HTML for case detail view
function renderCaseDetail(caseData) {
    const mainContent = document.getElementById('mainContent');
    if (!mainContent) return;
    
    mainContent.innerHTML = `
        <div id="caseDetailView">
            <div class="case-detail-header-main">
                <div>
                    <h2 class="case-detail-title">${caseData.title || 'Untitled Case'}</h2>
                    <div class="case-detail-meta">
                        Subspecialty: <span>${caseData.subspecialty_display || caseData.subspecialty || 'N/A'}</span> |
                        Modality: <span>${caseData.modality_display || caseData.modality || 'N/A'}</span> |
                        Difficulty: <span>${caseData.difficulty_display || caseData.difficulty || 'N/A'}</span>
                    </div>
                </div>
                <div>
                    <button class="btn btn-secondary" id="backToCasesBtn">Back to Cases</button>
                </div>
            </div>

            <div id="caseDetailContainer">
                <div id="caseImagingColumn">
                    <h3 class="case-section-title">Imaging</h3>
                    <div id="dicomViewerContainer" style="width:100%; height:600px; border:1px solid #ccc; background-color: #f0f0f0;">
                        <iframe id="dicomViewerFrame" style="width:100%; height:100%; border:none;" title="DICOM Study Viewer"></iframe>
                    </div>
                    <p id="dicomLoadingMessage" style="text-align:center; margin-top:10px; display:none;">Loading DICOM images...</p>
                    <p id="dicomErrorMessage" style="color:red; text-align:center; margin-top:10px; display:none;">Could not load DICOM images.</p>
                </div>

                <div id="caseInfoColumn">
                    <div class="case-clinical-info">
                        <h3 class="case-section-title">Clinical Information</h3>
                        <p><strong>Patient Age:</strong> ${caseData.patient_age || 'N/A'}</p>
                        <p><strong>Patient Sex:</strong> ${caseData.patient_sex || 'N/A'}</p>
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
                        <h3 class="case-section-title">Your Submitted Report</h3>
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
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add event listener for back button
    document.getElementById('backToCasesBtn')?.addEventListener('click', () => {
        // Clear URL hash when going back to case list
        window.location.hash = '';
        loadCaseList();
    });
    
    // Add form submit event handler
    const reportForm = document.getElementById('reportForm');
    if (reportForm) {
        reportForm.addEventListener('submit', handleReportSubmit);
    }
}

// Display user's submitted report with AI feedback integration
async function displayUserSubmittedReport(caseId) {
    const userReportContainer = document.getElementById('userSubmittedReportSection');
    if (!userReportContainer) return;

    userReportContainer.innerHTML = `
        <h3 class="case-section-title" style="color: #0056b3;">Your Submitted Report</h3>
        <p>Loading your submitted report...</p>`;
    userReportContainer.style.display = 'block';

    try {
        const myReportsResponse = await apiRequest('/cases/my-reports/');
        let reports = [];
        
        if (myReportsResponse && Array.isArray(myReportsResponse.results)) {
            reports = myReportsResponse.results;
        } else if (myReportsResponse && Array.isArray(myReportsResponse)) {
            reports = myReportsResponse;
        }

        const reportForThisCase = reports.find(report => 
            String(report.case) === String(caseId) || 
            (report.case && typeof report.case === 'object' && String(report.case.id) === String(caseId)) ||
            (report.case_id && String(report.case_id) === String(caseId))
        );

        if (reportForThisCase && reportForThisCase.structured_content && Array.isArray(reportForThisCase.structured_content)) {
            let html = `<h3 class="case-section-title" style="color: #0056b3;">Your Submitted Report</h3>`;
            
            if (reportForThisCase.submitted_at) {
                html += `<p style="font-size: 0.9em; color: #555; margin-bottom: 15px;">
                    Submitted on: ${new Date(reportForThisCase.submitted_at).toLocaleString()}</p>`;
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

            // Add AI Feedback button and container
            html += `
                <div style="text-align: right; margin-top: 20px; padding-top:15px; border-top: 1px solid #ddd;">
                    <button class="btn btn-secondary btn-sm get-ai-feedback-btn" data-report-id="${reportForThisCase.id}">
                        Get AI Feedback
                    </button>
                </div>
                <div id="aiFeedbackContainerForReport_${reportForThisCase.id}" class="ai-feedback-container" 
                     style="margin-top: 15px; padding: 15px; background-color: #fff9e6; border: 1px solid #ffecb3; 
                            border-radius: 6px; display:none;">
                    <h4 style="color: #b08c00; margin-top:0; margin-bottom:10px;">AI Feedback:</h4>
                    <p class="ai-feedback-loading-message">Loading feedback...</p>
                    <div class="ai-feedback-content"></div>
                </div>
            `;

            userReportContainer.innerHTML = html;

            // Add event listener for AI feedback button
            const aiFeedbackBtn = userReportContainer.querySelector(`.get-ai-feedback-btn[data-report-id="${reportForThisCase.id}"]`);
            if (aiFeedbackBtn) {
                aiFeedbackBtn.addEventListener('click', () => requestAIFeedback(reportForThisCase.id));
            }

        } else {
            userReportContainer.innerHTML = `
                <h3 class="case-section-title" style="color: #0056b3;">Your Submitted Report</h3>
                <p>You have not submitted a report for this case, or your report could not be loaded.</p>`;
        }
    } catch (error) {
        console.error("Error fetching or displaying user's submitted report:", error);
        userReportContainer.innerHTML = `
            <h3 class="case-section-title" style="color: #0056b3;">Your Submitted Report</h3>
            <p style="color:red;">Error loading your report: ${error.message || 'Unknown error'}</p>`;
    }
}

// Function to request AI feedback for a report
async function requestAIFeedback(reportId) {
    const feedbackContainer = document.getElementById(`aiFeedbackContainerForReport_${reportId}`);
    const loadingMessage = feedbackContainer?.querySelector('.ai-feedback-loading-message');
    const feedbackContent = feedbackContainer?.querySelector('.ai-feedback-content');
    const feedbackBtn = document.querySelector(`.get-ai-feedback-btn[data-report-id="${reportId}"]`);
    
    if (!feedbackContainer || !loadingMessage || !feedbackContent || !feedbackBtn) {
        console.error("Required elements for AI feedback not found");
        showToast("Error: Could not display AI feedback", "error");
        return;
    }
    
    // Display the container and loading message
    feedbackContainer.style.display = 'block';
    loadingMessage.style.display = 'block';
    feedbackContent.innerHTML = '';
    feedbackBtn.disabled = true;
    feedbackBtn.textContent = "Getting Feedback...";
    
    try {
        console.log(`Requesting AI feedback for report ID: ${reportId}`);
        const response = await apiRequest(`/cases/reports/${reportId}/ai-feedback/`);
        
        if (response) {
            console.log("AI feedback response:", response);
            
            // Check for different possible response formats
            let feedbackText = '';
            
            if (response.raw_llm_feedback) {
                feedbackText = response.raw_llm_feedback;
            } else if (response.structured_feedback) {
                // Handle structured feedback with sections
                const structured = response.structured_feedback;
                
                if (structured.overall_impression_alignment) {
                    feedbackText += `Overall Impression Alignment:\n${structured.overall_impression_alignment}\n\n`;
                }
                
                if (structured.section_feedback && structured.section_feedback.length > 0) {
                    feedbackText += "Section-by-Section Analysis:\n";
                    structured.section_feedback.forEach(sf => {
                        if (sf.severity_level_from_llm === "Consistent") {
                            feedbackText += `${sf.section_name}: ${sf.discrepancy_summary_from_llm}\n`;
                        } else {
                            feedbackText += `${sf.section_name}: (${sf.severity_level_from_llm}) ${sf.discrepancy_summary_from_llm}\n`;
                        }
                    });
                    feedbackText += "\n";
                }
                
                if (structured.key_learning_points && structured.key_learning_points.length > 0) {
                    feedbackText += "Key Learning Points:\n";
                    structured.key_learning_points.forEach((lp, index) => {
                        feedbackText += `${index+1}. ${lp.point}\n   Advice: ${lp.advice}\n`;
                        if (lp.topics_for_study) {
                            feedbackText += `   Further Study: ${lp.topics_for_study}\n`;
                        }
                    });
                }
            } else {
                // Fallback for any other response format containing feedback
                feedbackText = response.feedback || JSON.stringify(response, null, 2);
            }
            
            // Display the feedback
            if (feedbackText) {
                feedbackContent.innerText = feedbackText; // Use innerText to preserve formatting
            } else {
                feedbackContent.innerHTML = '<p>No feedback was provided by the AI.</p>';
            }
        } else {
            feedbackContent.innerHTML = '<p>Received an empty response from the AI feedback service.</p>';
        }
    } catch (error) {
        console.error("Error fetching AI feedback:", error);
        feedbackContent.innerHTML = `<p style="color:red;">Error fetching AI feedback: ${error.message || 'Unknown error'}</p>`;
    } finally {
        loadingMessage.style.display = 'none';
        feedbackBtn.disabled = false;
        feedbackBtn.textContent = "Get AI Feedback";
    }
}

// Populate expert language selector
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
        langButton.dataset.caseTemplateId = template.id;

        langButton.onclick = async () => {
            document.querySelectorAll('.expert-lang-btn').forEach(btn => btn.classList.remove('active'));
            langButton.classList.add('active');
            contentContainer.innerHTML = `<p>Loading ${template.language_name} expert report...</p>`;
            
            try {
                const expertContent = await apiRequest(`/cases/cases/${caseId}/expert-templates/${template.language_code}/`);
                
                if (expertContent && expertContent.section_contents) {
                    let html = '<ul>';
                    expertContent.section_contents.forEach(section => {
                        html += `
                            <li>
                                <strong>${section.master_section_name}:</strong>
                                <p>${section.content || '<em>No content provided.</em>'}</p>
                            </li>`;
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

// Renders the MasterTemplate sections as form fields for report submission
function renderMasterTemplateForReporting(masterTemplateData, containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container '${containerId}' not found for rendering template.`);
        return;
    }

    const reportForm = document.getElementById('reportForm');

    // Ensure the submit button is present
    if (reportForm) {
        let submitButton = reportForm.querySelector('button[type="submit"]');
        if (!submitButton) {
            const actionsDiv = reportForm.querySelector('.form-actions') || document.createElement('div');
            if (!actionsDiv.classList.contains('form-actions')) {
                actionsDiv.className = 'form-actions';
                actionsDiv.style.marginTop = '15px';
                
                if (reportForm.firstChild) {
                    reportForm.insertBefore(actionsDiv, reportForm.firstChild.nextSibling);
                } else {
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

    // Validate master template data
    if (!masterTemplateData || !masterTemplateData.sections || !Array.isArray(masterTemplateData.sections)) {
        container.innerHTML = '<p>Could not load report template structure: Invalid master template data.</p>';
        console.warn("Invalid template data:", masterTemplateData);
        reportForm?.querySelector('button[type="submit"]')?.remove();
        return;
    }
    
    if (masterTemplateData.sections.length === 0) {
        container.innerHTML = '<p>This template has no defined sections. Cannot create report.</p>';
        reportForm?.querySelector('button[type="submit"]')?.remove();
        return;
    }

    // Sort sections by order property
    const sortedSections = [...masterTemplateData.sections].sort((a, b) => (a.order || 0) - (b.order || 0));

    // Build the form HTML
    let formHTML = '';
    sortedSections.forEach(section => {
        const initialContent = section.placeholder_text || '';
        const escapedInitialContent = initialContent.replace(/</g, "&lt;").replace(/>/g, "&gt;");

        formHTML += `
            <div class="report-section" style="margin-bottom: 15px;">
                <label for="report_section_${section.id}" style="display:block; font-weight:bold; margin-bottom:5px;">
                    ${section.name || 'Unnamed Section'} ${section.is_required ? '<span style="color:red;">*</span>' : ''}
                </label>
                <textarea id="report_section_${section.id}" 
                          name="section_content_for_master_section_${section.id}"
                          class="form-control report-section-textarea"
                          rows="4" 
                          data-section-name="${section.name || 'Unnamed Section'}" 
                          data-section-id="${section.id}"
                          ${section.is_required ? 'required' : ''}>${escapedInitialContent}</textarea>
            </div>
        `;
    });
    
    container.innerHTML = formHTML;
    console.log("Report form rendered with Master Template sections.");
}

// Handle report form submission
async function handleReportSubmit(event) {
    console.log("--- handleReportSubmit called ---");
    event.preventDefault();
    const form = event.target;
    const caseId = form.getAttribute('data-case-id');
    const submitButton = form.querySelector('button[type="submit"]');

    if (!submitButton) {
        console.error("Submit button not found in report form.");
        showToast("Error: Submit button missing.", "error");
        return;
    }

    const reportSectionsContainer = document.getElementById('dynamicReportSectionsContainer');
    if (!reportSectionsContainer) {
        console.error("Report sections container not found.");
        showToast("Error: Report form structure is missing.", "error");
        return;
    }

    const sectionTextareas = reportSectionsContainer.querySelectorAll('textarea');
    const reportContents = [];
    let allRequiredFilled = true;

    // Validate form inputs
    sectionTextareas.forEach(textarea => {
        const sectionId = textarea.dataset.sectionId;
        const sectionName = textarea.dataset.sectionName || 'Unnamed Section';
        const content = textarea.value.trim();
        const isRequired = textarea.hasAttribute('required');

        if (isRequired && !content) {
            allRequiredFilled = false;
            showToast(`Please fill in the required section: "${sectionName}"`, 'error');
            textarea.classList.add('error');
            
            // Focus the first empty required field
            if (allRequiredFilled) {
                textarea.focus();
            }
        } else {
            textarea.classList.remove('error');
        }

        reportContents.push({
            master_template_section_id: parseInt(sectionId),
            content: content
        });
    });

    if (!allRequiredFilled) {
        return; // Stop submission if required fields are empty
    }

    if (reportContents.length === 0) {
        showToast("Cannot submit an empty report. Please fill in the sections.", "warning");
        return;
    }

    // Disable submit button during API call
    submitButton.disabled = true;
    submitButton.textContent = 'Submitting...';

    try {
        const reportPayload = {
            case_id: parseInt(caseId),
            section_details: reportContents
        };
        
        console.log("Submitting structured report data:", reportPayload);
        const response = await apiRequest('/cases/reports/', {
            method: 'POST',
            body: JSON.stringify(reportPayload)
        });

        console.log("Report submission response:", response);
        showToast("Report submitted successfully!", 'success');

        // UI updates after successful submission
        sectionTextareas.forEach(textarea => {
            textarea.disabled = true;
        });
        submitButton.remove();

        // Show expert discussion section
        const expertDiscussionSection = document.getElementById('expertDiscussionSection');
        if (expertDiscussionSection) {
            expertDiscussionSection.style.display = 'block';
        }
        
        // Refresh case data to get updated status
        try {
            const updatedCaseData = await apiRequest(`/cases/cases/${caseId}/`);
            if (updatedCaseData && typeof updatedCaseData.id !== 'undefined') {
                console.log("Refreshed case data after report submission:", updatedCaseData);
                
                // Show expert language selector with updated data
                populateExpertLanguageSelector(caseId, updatedCaseData.applied_templates || []);
                
                // Display the user's submitted report
                await displayUserSubmittedReport(caseId);
            }
        } catch (refreshError) {
            console.warn("Could not refresh case data after report:", refreshError);
        }

    } catch (error) {
        console.error("Failed to submit report:", error);
        const errorMessage = error.data?.detail || 
                             (error.data && typeof error.data === 'object' ? JSON.stringify(error.data) : error.message) || 
                             "Failed to submit report.";
        showToast(`Error: ${errorMessage}`, 'error');
        submitButton.disabled = false;
        submitButton.textContent = 'Submit Report';
    }
}

// Helper function for showing toast notifications
function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, duration);
}

// --- Load My Reports View ---
async function loadMyReports() {
    console.log("--- loadMyReports called ---");
    const mainContent = document.getElementById('mainContent');
    if (!mainContent) {
        console.error("Main content area not found for My Reports.");
        return;
    }

    mainContent.innerHTML = `<h2>My Submitted Reports</h2><div class="loading-indicator">Fetching your reports...</div>`;
    const loadingIndicator = mainContent.querySelector('.loading-indicator');

    try {
        // Fetch reports from the backend API endpoint
        const response = await apiRequest('/cases/my-reports/');

        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }

        // Handle both paginated and direct array responses
        let reports = [];
        if (response && Array.isArray(response.results)) {
            reports = response.results;
        } else if (response && Array.isArray(response)) {
            reports = response;
        } else {
            console.error("Invalid response structure for reports:", response);
            mainContent.innerHTML += '<p>Could not load your reports. Invalid response format.</p>';
            return;
        }

        if (reports.length === 0) {
            mainContent.innerHTML += '<p>You have not submitted any reports yet.</p>';
        } else {
            let reportListHTML = '<ul class="report-list">';
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

            // Add event listeners to case links
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
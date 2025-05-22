// js/main.js - Main application logic for Global Peds Reading Room

// Assume api.js is loaded first (provides apiRequest, getAuthTokens, clearAuthTokens)

// Helper functions (MOVED TO TOP LEVEL for global accessibility)
const getDisplayValue = (value, fallback = 'N/A') => value || fallback;
const getSubspecialtyDisplay = (data) => getDisplayValue(data.subspecialty_display || data.subspecialty);
const getModalityDisplay = (data) => getDisplayValue(data.modality_display || data.modality);
const getDifficultyDisplay = (data) => getDisplayValue(data.difficulty_display || data.difficulty);

// NEW: Global variable for the current user's report data, used for re-rendering after AI feedback
let currentUserReportData = null;

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

    // Re-introduce case-list-split-view for side-by-side layout
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

    // Setup filter dropdowns
    setupFilters();

    try {
        // Fetch published cases
        console.log(`Workspaceing cases from ${url}`);
        const response = await apiRequest(url);

        loadingIndicator.style.display = 'none';

        if (response && Array.isArray(response.results)) {
            const cases = response.results;
            console.log(`Received ${cases.length} cases.`);

            if (cases.length === 0 && !response.previous) {
                gridContainer.innerHTML = '<p>No published cases found.</p>';
                tableBody.innerHTML = '<tr><td colspan="6">No published cases found.</td></tr>';
            } else {
                renderCaseGrid(gridContainer, cases);
                renderCaseTable(tableBody, cases);
            }
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
                <span class="tag difficulty-${(caseData.difficulty || 'unknown').toLowerCase().replace(/\s+/g, '-')}">
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


async function viewCase(caseId) {
    console.log(`--- viewCase called for caseId: ${caseId} ---`);
    const mainContent = document.getElementById('mainContent');
    if (!mainContent) {
        console.error("Main content area not found for displaying case detail.");
        return;
    }

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

        try {
            await apiRequest(`/cases/cases/${caseId}/viewed/`, { method: 'POST' });
            console.log(`Case ${caseId} marked as viewed.`);
        } catch (viewError) {
            console.warn(`Could not mark case ${caseId} as viewed:`, viewError);
        }

        renderCaseDetail(caseData); // This now includes the tab structure
        setupDicomViewer(caseData);
        
        const reportSubmissionSection = document.getElementById('reportSubmissionSection');
        const caseReviewTabsContainer = document.getElementById('caseReviewTabsContainer');
        const userSubmittedReportContentDiv = document.getElementById('userSubmittedReportSectionContent');
        const aiFeedbackTabContent = document.getElementById('aiFeedbackTabContent'); // To reset AI feedback tab
        const expertReportTabContent = document.getElementById('expertReportTabContent'); // To reset Expert report tab

        let userReportForCase = null; // Declare a variable to hold the user's report data

        if (caseData.is_reported_by_user) {
            if (reportSubmissionSection) reportSubmissionSection.style.display = 'none';
            if (caseReviewTabsContainer) caseReviewTabsContainer.style.display = 'block';

            // Fetch user's reports once
            const myReportsResponse = await apiRequest('/cases/my-reports/');
            let allUserReports = [];
            if (myReportsResponse && Array.isArray(myReportsResponse.results)) {
                allUserReports = myReportsResponse.results;
            } else if (myReportsResponse && Array.isArray(myReportsResponse)) {
                allUserReports = myReportsResponse;
            }

            userReportForCase = allUserReports.find(report => 
                String(report.case) === String(caseData.id) || 
                (report.case && typeof report.case === 'object' && String(report.case.id) === String(caseData.id)) ||
                (report.case_id && String(report.case_id) === String(caseData.id))
            );

            // Store the fetched user report in the global variable
            currentUserReportData = userReportForCase;

            if (userSubmittedReportContentDiv && currentUserReportData) {
                 displayUserSubmittedReport(currentUserReportData, userSubmittedReportContentDiv); // Pass the global report object
            } else if (userSubmittedReportContentDiv) {
                userSubmittedReportContentDiv.innerHTML = `<h4 class="tab-content-title" style="color: #0056b3;">Your Submitted Report</h4><p>Could not load your submitted report for this case.</p>`;
            }

            // Reset AI Feedback and Expert tabs to initial states
            if (aiFeedbackTabContent) aiFeedbackTabContent.innerHTML = `
                <h4 class="tab-content-title">AI Feedback Analysis</h4>
                <div id="aiFeedbackDisplayArea">
                    <p>Request AI feedback to see analysis.</p>
                </div>
                <div id="aiFeedbackRatingSection" style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee; display:none;">
                    <h4>Rate this AI Feedback:</h4>
                    <div class="stars">
                        <span>☆</span><span>☆</span><span>☆</span><span>☆</span><span>☆</span>
                    </div>
                    <textarea placeholder="Optional comments..." style="width:100%; min-height:60px; margin-top:5px;"></textarea>
                    <button class="btn btn-sm btn-secondary" style="margin-top:5px;">Submit Rating</button>
                </div>`;
            if (expertReportTabContent) expertReportTabContent.innerHTML = `
                <h4 class="tab-content-title">Expert Report</h4>
                <div id="expertLanguageSelector" style="margin-bottom:10px;"></div>
                <div id="expertTemplateContentContainer">
                    <p>Select a language to view expert analysis.</p>
                </div>
                <p><strong>Key Findings (Expert):</strong> ${getDisplayValue(caseData.key_findings)}</p>`;


            populateExpertLanguageSelector(caseData.id, caseData.applied_templates || [], currentUserReportData); // Pass currentUserReportData here
             
            // NEW: Immediately request AI feedback for existing reports
            if (currentUserReportData && currentUserReportData.id) {
                requestAIFeedback(currentUserReportData.id);
            }

            // Activate the "Your Submitted Report" tab by default
            document.querySelector('.info-tab-button[data-tab-target="#userSubmittedReportSectionContent"]')?.click();
        } else {
            if (reportSubmissionSection) reportSubmissionSection.style.display = 'block';
            if (caseReviewTabsContainer) caseReviewTabsContainer.style.display = 'none';
            
            if (caseData.master_template_details) {
                renderMasterTemplateForReporting(caseData.master_template_details, 'dynamicReportSectionsContainer');
            } else {
                console.warn("Case doesn't have master_template_details. Cannot render report form.");
                const reportContainer = document.getElementById('dynamicReportSectionsContainer');
                if (reportContainer) {
                    reportContainer.innerHTML = "<p><em>No report template is associated with this case.</em></p>";
                }
                const submitBtn = reportSubmissionSection?.querySelector('button[type="submit"]');
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
    if (!mainContent) {
        console.error("renderCaseDetail: Main content area not found.");
        return;
    }

    mainContent.innerHTML = `
        <div id="caseDetailView">
            <div class="case-detail-header-main">
                <div>
                    <h2 class="case-detail-title">${getDisplayValue(caseData.case_identifier || caseData.title, 'Untitled Case')}</h2>
                    <div class="case-detail-meta">
                        Subspecialty: <span>${getSubspecialtyDisplay(caseData)}</span> |
                        Modality: <span>${getModalityDisplay(caseData)}</span> |
                        Difficulty: <span>${getDifficultyDisplay(caseData)}</span>
                    </div>
                </div>
                <div>
                    <button class="btn btn-secondary" id="backToCasesBtn">Back to Cases</button>
                </div>
            </div>

            <div id="caseDetailContainer">
                <div id="caseImagingColumn">
                    <h3 class="case-section-title">Imaging</h3>
                    <div id="dicomViewerContainer">
                        <iframe id="dicomViewerFrame" title="DICOM Study Viewer"></iframe>
                    </div>
                    <p id="dicomLoadingMessage" style="text-align:center; margin-top:10px; display:none;">Loading DICOM images...</p>
                    <p id="dicomErrorMessage" style="color:red; text-align:center; margin-top:10px; display:none;">Could not load DICOM images.</p>
                </div>

                <div id="caseInfoColumn">
                    <div class="case-info-top-strip">
                        <h3 class="case-section-title">Case Information</h3>
                        <p><strong>Case ID:</strong> ${getDisplayValue(caseData.case_identifier)}</p>
                        <p><strong>Patient Age:</strong> ${getDisplayValue(caseData.patient_age)}</p>
                        <p><strong>Patient Sex:</strong> ${getDisplayValue(caseData.patient_sex)}</p>
                        <p><strong>Clinical History:</strong></p>
                        <p class="clinical-history-text">${getDisplayValue(caseData.clinical_history, 'No clinical history provided.')}</p>
                        <div class="expert-diagnosis-highlight">
                            <strong>Expert Diagnosis:</strong> 
                            <span>${getDisplayValue(caseData.diagnosis)}</span>
                        </div>
                    </div>

                    <div id="reportSubmissionSection" class="case-report-template" style="display: block;">
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
                    
                    <div id="caseReviewTabsContainer" style="display: none;">
                        <div class="info-tabs">
                            <button class="info-tab-button active" data-tab-target="#userSubmittedReportSectionContent">Your Submitted Report</button>
                            <button class="info-tab-button" data-tab-target="#aiFeedbackTabContent">AI Feedback</button>
                            <button class="info-tab-button" data-tab-target="#expertReportTabContent">Expert Report</button>
                        </div>

                        <div id="tabContentContainer">
                            <div id="userSubmittedReportSectionContent" class="info-tab-content active">
                                <p>Loading your report...</p>
                            </div>

                            <div id="aiFeedbackTabContent" class="info-tab-content">
                                <h4 class="tab-content-title">AI Feedback Analysis</h4>
                                <div id="aiFeedbackDisplayArea">
                                    <p>Request AI feedback to see analysis.</p>
                                </div>
                                <div id="aiFeedbackRatingSection" style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee; display:none;">
                                    <h4>Rate this AI Feedback:</h4>
                                    <div class="stars">
                                        <span>☆</span><span>☆</span><span>☆</span><span>☆</span><span>☆</span>
                                    </div>
                                    <textarea placeholder="Optional comments..." style="width:100%; min-height:60px; margin-top:5px;"></textarea>
                                    <button class="btn btn-sm btn-secondary" style="margin-top:5px;">Submit Rating</button>
                                </div>
                            </div>

                            <div id="expertReportTabContent" class="info-tab-content">
                                <h4 class="tab-content-title">Expert Report</h4>
                                <div id="expertLanguageSelector" style="margin-bottom:10px;"></div>
                                <div id="expertTemplateContentContainer">
                                    <p>Select a language to view expert analysis.</p>
                                </div>
                                <p><strong>Key Findings (Expert):</strong> ${getDisplayValue(caseData.key_findings)}</p>
                            </div>
                        </div>
                    </div>

                    <div class="case-info-bottom-strip">
                        <h3 class="case-section-title">References</h3>
                        <p>${getDisplayValue(caseData.references, 'No references provided.')}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('backToCasesBtn')?.addEventListener('click', () => {
        window.location.hash = '';
        loadCaseList();
    });
    
    const reportForm = document.getElementById('reportForm');
    if (reportForm) {
        reportForm.addEventListener('submit', handleReportSubmit);
    }

    setupInfoTabs();
}


// Function to handle tab switching for the info column
function setupInfoTabs() {
    const tabContainer = document.getElementById('caseReviewTabsContainer');
    if (!tabContainer) {
        console.warn("setupInfoTabs: Tab container '#caseReviewTabsContainer' not found. Tabs cannot be initialized.");
        return;
    }

    const tabButtons = tabContainer.querySelectorAll('.info-tab-button');
    const tabContents = tabContainer.querySelectorAll('.info-tab-content');

    if (tabButtons.length === 0) {
        console.warn("setupInfoTabs: No tab buttons found with class '.info-tab-button' inside '#caseReviewTabsContainer'.");
        return;
    }
    if (tabContents.length === 0) {
        console.warn("setupInfoTabs: No tab content areas found with class '.info-tab-content' inside '#caseReviewTabsContainer'.");
        return;
    }
    console.log(`setupInfoTabs: Found ${tabButtons.length} buttons and ${tabContents.length} content areas. Attaching listeners...`);

    tabButtons.forEach(button => {
        // Prevent attaching multiple listeners if this function is somehow called more than once
        if (button.dataset.listenerAttached === 'true') {
            // console.log("Listener already attached to button:", button.textContent.trim());
            return;
        }
        button.dataset.listenerAttached = 'true'; // Mark as listener attached

        button.addEventListener('click', () => {
            const targetTabSelector = button.dataset.tabTarget; // Should be like "#someId"
            console.log("Tab button clicked. Button text:", button.textContent.trim(), "Target selector:", targetTabSelector);

            if (!targetTabSelector || !targetTabSelector.startsWith('#')) {
                console.error("Button is missing a valid data-tab-target attribute (must start with #):", button);
                return;
            }

            const targetContentId = targetTabSelector.substring(1); // Remove '#'

            // Deactivate all buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            // Activate the clicked button
            button.classList.add('active');
            console.log("Activated button:", button.textContent.trim());

            let targetFound = false;
            // Hide all content areas, then show the target one
            tabContents.forEach(content => {
                if (content.id === targetContentId) {
                    content.classList.add('active'); // Assumes CSS handles display:block for .active
                    targetFound = true;
                    console.log("Showing content for:", content.id);
                } else {
                    content.classList.remove('active');
                }
            });

            if (!targetFound) {
                console.warn("No content area found for target ID:", targetContentId);
            }
        });
        console.log("Listener attached to button:", button.textContent.trim());
    });
}
// Function to display user's submitted report with AI feedback integration
// Renamed parameter to userReportData (the full report object)
async function displayUserSubmittedReport(userReportData, targetContainerElement) { 
    if (!targetContainerElement) {
        console.error("Target container for user's submitted report not provided.");
        return;
    }

    targetContainerElement.innerHTML = `
        <h4 class="tab-content-title">Your Submitted Report</h4>
        <p>Loading your submitted report...</p>`;

    if (userReportData && userReportData.structured_content && Array.isArray(userReportData.structured_content)) {
        let html = `<h4 class="tab-content-title" style="color: #0056b3;">Your Submitted Report</h4>`;
        
        if (userReportData.submitted_at) {
            html += `<p style="font-size: 0.9em; color: #555; margin-bottom: 15px;">
                Submitted on: ${new Date(userReportData.submitted_at).toLocaleString()}</p>`;
        }
        
        // NEW: Add a class for the UL for consistency
        html += '<ul class="user-report-sections-list">'; 

        // Create a map for quick lookup of AI feedback by section name
        const aiSectionFeedbackMap = new Map();
        if (userReportData.ai_feedback_content && userReportData.ai_feedback_content.structured_feedback) {
            console.log("AI Feedback Content:", userReportData.ai_feedback_content);
            
            // Check if section_feedback exists and has items
            const sectionFeedback = userReportData.ai_feedback_content.structured_feedback.section_feedback || [];
            console.log("Section Feedback Array:", sectionFeedback);
            
            if (sectionFeedback.length > 0) {
                // Process normal section feedback
                sectionFeedback.forEach(sf => {
                    console.log("Processing section feedback:", sf);
                    aiSectionFeedbackMap.set(sf.section_name, sf);
                });
            } else {
                // If no section feedback is available, we'll just use Consistent (green) for all sections
                console.log("Section feedback array is empty - using Consistent for all sections");
                // We won't create any default feedback - sections will default to 'Consistent'
            }
        }
        
        userReportData.structured_content.forEach(section => {
            const sectionName = section.section_name || `Section ID ${section.master_template_section_id || 'N/A'}`;
            const sectionContent = section.content || '<em>No content submitted for this section.</em>';

            // Default values
            let sectionClasses = 'ai-feedback-consistent'; // Default to consistent (green) if no feedback
            let aiComment = 'Generally consistent with expert assessment';
            let aiSeverity = 'Consistent';

            // Check for AI feedback for this specific section
            const aiFeedbackForSection = aiSectionFeedbackMap.get(sectionName);
            if (aiFeedbackForSection) {
                aiComment = aiFeedbackForSection.discrepancy_summary_from_llm || aiComment;
                aiSeverity = aiFeedbackForSection.severity_level_from_llm || aiSeverity;
                
                console.log(`Section: ${sectionName}, Severity: ${aiSeverity}, Raw value:`, aiFeedbackForSection.severity_level_from_llm);

                // Normalize severity value for consistent matching
                const normalizedSeverity = (aiSeverity || '').trim();
                
                // Apply classes based on severity - handle different formats from the LLM
                if (normalizedSeverity.toLowerCase().includes('critical') || normalizedSeverity.toLowerCase() === 'severe') {
                    sectionClasses = 'ai-feedback-critical';
                    console.log(`${sectionName}: Applied critical class`);
                } else if (normalizedSeverity.toLowerCase().includes('moderate') || normalizedSeverity.toLowerCase() === 'medium') {
                    sectionClasses = 'ai-feedback-moderate';
                    console.log(`${sectionName}: Applied moderate class`);
                } else {
                    // Default to consistent for everything else
                    sectionClasses = 'ai-feedback-consistent';
                    console.log(`${sectionName}: Applied consistent class (default)`);
                }
                
                console.log(`${sectionName}: Final class applied: ${sectionClasses}`);
            }

            const dataAttributes = `
                data-ai-comment="${aiComment}"
                data-ai-severity="${aiSeverity}"
                data-section-name="${sectionName}"
            `;

            // MODIFIED HTML STRUCTURE AND CLASSES HERE
            html += `
                <li class="report-section-display-item ${sectionClasses}" ${dataAttributes}>
                    <strong class="report-section-title-display">${sectionName}:</strong>
                    <div class="report-section-content-display">
                        <p>${sectionContent}</p>
                    </div>
                </li>`;
        });
        html += '</ul>';

        html += `
            <div style="text-align: right; margin-top: 20px; padding-top:15px; border-top: 1px solid #ddd;" class="report-action-buttons">
                <button class="btn btn-secondary btn-sm reset-case-btn" data-case-id="${userReportData.case || userReportData.case_id}">
                    <i class="fa fa-undo"></i> Reset Case
                </button>
                <button class="btn btn-primary btn-sm get-ai-feedback-btn" data-report-id="${userReportData.id}">
                    <i class="fa fa-refresh"></i> Get AI Feedback
                </button>
            </div>`;

        targetContainerElement.innerHTML = html;

        // Add event listener for AI Feedback button
        const aiFeedbackBtn = targetContainerElement.querySelector(`.get-ai-feedback-btn[data-report-id="${userReportData.id}"]`);
        if (aiFeedbackBtn) {
            aiFeedbackBtn.addEventListener('click', () => {
                requestAIFeedback(userReportData.id);
                document.querySelector('.info-tab-button[data-tab-target="#aiFeedbackTabContent"]')?.click();
            });
        }
        
        // Add event listener for Reset Case button
        const resetCaseBtn = targetContainerElement.querySelector(`.reset-case-btn[data-case-id]`);
        if (resetCaseBtn) {
            resetCaseBtn.addEventListener('click', async () => {
                const caseId = resetCaseBtn.dataset.caseId;
                if (!caseId) return;
                
                // Confirm the reset action
                if (confirm("Are you sure you want to reset this case? This will allow you to submit a new report for this case, but your current report will still be accessible in your history.")) {
                    try {
                        // Save existing report data to sessionStorage for future reference
                        const existingReportKey = `previous_report_case_${caseId}`;
                        sessionStorage.setItem(existingReportKey, JSON.stringify(userReportData));
                        
                        // Call API to reset case status for this user
                        await apiRequest(`/cases/cases/${caseId}/reset/`, { method: 'POST' });
                        
                        // Show success message
                        showToast("Case reset successfully. You can now submit a new report.", "success");
                        
                        // Reload the case to show the reporting form
                        viewCase(caseId);
                    } catch (error) {
                        console.error("Error resetting case:", error);
                        showToast(`Error resetting case: ${error.message || "Unknown error"}`, "error");
                    }
                }
            });
        }
        // NEW: Initialize tooltips for the newly rendered sections
        setupReportSectionTooltips(targetContainerElement);

    } else {
        targetContainerElement.innerHTML = `
            <h4 class="tab-content-title" style="color: #0056b3;">Your Submitted Report</h4>
            <p>You have not submitted a report for this case, or your report could not be loaded.</p>`;
    }
}

// Function to request AI feedback for a report
async function requestAIFeedback(reportId) {
    // Correctly identify the target elements based on renderCaseDetail HTML structure
    const aiFeedbackTabContent = document.getElementById('aiFeedbackTabContent');
    const aiFeedbackDisplayArea = document.getElementById('aiFeedbackDisplayArea');
    const feedbackBtn = document.querySelector(`.get-ai-feedback-btn[data-report-id="${reportId}"]`);
    
    // Check if all required elements are found
    if (!aiFeedbackTabContent || !aiFeedbackDisplayArea || !feedbackBtn) {
        console.error("Required elements for AI feedback not found in the DOM (aiFeedbackTabContent or aiFeedbackDisplayArea or feedbackBtn).");
        showToast("Error: Could not display AI feedback due to missing UI elements.", "error");
        return;
    }

    // Attempt to retrieve saved AI feedback first (using GET request)
    try {
        aiFeedbackDisplayArea.innerHTML = '<p class="ai-feedback-loading-message" style="text-align:center; padding:20px;">Checking for saved AI feedback...</p>';
        feedbackBtn.disabled = true;
        feedbackBtn.textContent = "Checking...";

        const savedResponse = await apiRequest(`/cases/reports/${reportId}/ai-feedback/`, { method: 'GET' });
        
        console.log("Saved AI feedback retrieved:", savedResponse);
        if (savedResponse) {
            displayAIResponseBody(savedResponse, aiFeedbackDisplayArea);
            showToast("Saved AI feedback loaded successfully!", "success");
            document.getElementById('aiFeedbackRatingSection').style.display = 'block'; // Show rating section

            // ***************************************************************
            // FIX: Re-fetch the full user report to update the color-coding on "Your Submitted Report" tab
            const updatedReportData = await apiRequest(`/cases/my-reports/?report_id=${reportId}`); 
            let fullReportToReRender = null;
            if (updatedReportData && Array.isArray(updatedReportData.results) && updatedReportData.results.length > 0) {
                fullReportToReRender = updatedReportData.results[0];
            } else if (updatedReportData && !Array.isArray(updatedReportData) && updatedReportData.id) { 
                fullReportToReRender = updatedReportData;
            }

            if (fullReportToReRender) {
                const userSubmittedReportContentDiv = document.getElementById('userSubmittedReportSectionContent');
                if (userSubmittedReportContentDiv) {
                    displayUserSubmittedReport(fullReportToReRender, userSubmittedReportContentDiv);
                } else {
                    console.warn("User submitted report content div not found for re-rendering.");
                }
            } else {
                console.warn("Could not re-fetch full user report for color-coding after AI feedback loaded.");
            }
            // ***************************************************************

        } else {
            aiFeedbackDisplayArea.innerHTML = '<p>No saved AI feedback found. Click "Get/Refresh AI Feedback" to generate new feedback.</p>';
            document.getElementById('aiFeedbackRatingSection').style.display = 'none'; // Hide rating section
            feedbackBtn.textContent = "Get/Refresh AI Feedback"; // Reset button text
            feedbackBtn.removeEventListener('click', generateNewAIReportFeedback); // Remove old listener if exists
            feedbackBtn.addEventListener('click', () => generateNewAIReportFeedback(reportId)); // Attach listener for generating
        }

    } catch (error) {
        console.warn("No saved AI feedback found or error retrieving:", error);
        if (error.status === 404 || (error.data && error.data.error && error.data.error.includes("not yet generated"))) {
            aiFeedbackDisplayArea.innerHTML = '<p>No saved AI feedback found. Click "Get/Refresh AI Feedback" to generate new feedback.</p>';
            document.getElementById('aiFeedbackRatingSection').style.display = 'none'; // Hide rating section
            feedbackBtn.textContent = "Get/Refresh AI Feedback"; // Reset button text
            feedbackBtn.removeEventListener('click', generateNewAIReportFeedback); // Remove old listener
            feedbackBtn.addEventListener('click', () => generateNewAIReportFeedback(reportId)); // Attach listener for generating
        } else {
            console.error("Error retrieving saved AI feedback:", error);
            aiFeedbackDisplayArea.innerHTML = `<p style="color:red;">Error loading saved AI feedback: ${error.message || 'Unknown error'}</p>`;
            document.getElementById('aiFeedbackRatingSection').style.display = 'none'; // Hide rating section
        }
    } finally {
        feedbackBtn.disabled = false;
        if (feedbackBtn.textContent === 'Checking...') {
            feedbackBtn.textContent = "Get/Refresh AI Feedback";
        }
    }
}

// New function to handle generating new AI feedback (POST request)
async function generateNewAIReportFeedback(reportId) {
    const aiFeedbackTabContent = document.getElementById('aiFeedbackTabContent');
    const aiFeedbackDisplayArea = document.getElementById('aiFeedbackDisplayArea');
    const feedbackBtn = document.querySelector(`.get-ai-feedback-btn[data-report-id="${reportId}"]`);

    if (!aiFeedbackTabContent || !aiFeedbackDisplayArea || !feedbackBtn) {
        console.error("Required elements for AI feedback not found for generation (aiFeedbackTabContent or aiFeedbackDisplayArea or feedbackBtn).");
        showToast("Error: Could not display AI feedback due to missing UI elements.", "error");
        return;
    }

    aiFeedbackDisplayArea.innerHTML = '<p class="ai-feedback-loading-message" style="text-align:center; padding:20px;">Generating new AI feedback, this may take a moment...</p>';
    feedbackBtn.disabled = true;
    feedbackBtn.textContent = "Generating...";

    try {
        console.log(`Generating new AI feedback for report ID: ${reportId}`);
        const response = await apiRequest(`/cases/reports/${reportId}/ai-feedback/`, { method: 'POST' });
        
        if (response) {
            console.log("New AI feedback generated and saved:", response);
            displayAIResponseBody(response, aiFeedbackDisplayArea);
            showToast("AI feedback generated and saved successfully!", "success");
            document.getElementById('aiFeedbackRatingSection').style.display = 'block'; // Show rating section

            // ***************************************************************
            // FIX: Re-fetch the full user report to update the color-coding on "Your Submitted Report" tab
            const updatedReportData = await apiRequest(`/cases/my-reports/?report_id=${reportId}`);
            let fullReportToReRender = null;
            if (updatedReportData && Array.isArray(updatedReportData.results) && updatedReportData.results.length > 0) {
                fullReportToReRender = updatedReportData.results[0];
            } else if (updatedReportData && !Array.isArray(updatedReportData) && updatedReportData.id) {
                fullReportToReRender = updatedReportData;
            }

            if (fullReportToReRender) {
                const userSubmittedReportContentDiv = document.getElementById('userSubmittedReportSectionContent');
                if (userSubmittedReportContentDiv) {
                    displayUserSubmittedReport(fullReportToReRender, userSubmittedReportContentDiv);
                } else {
                    console.warn("User submitted report content div not found for re-rendering after generation.");
                }
            } else {
                console.warn("Could not re-fetch full user report for color-coding after new AI feedback generated.");
            }
            // ***************************************************************

        } else {
            aiFeedbackDisplayArea.innerHTML = '<p>Received an empty response when generating AI feedback.</p>';
            document.getElementById('aiFeedbackRatingSection').style.display = 'none'; // Hide rating section
        }

    } catch (error) {
        console.error("Error generating new AI feedback:", error);
        aiFeedbackDisplayArea.innerHTML = `<p style="color:red;">Error generating new AI feedback: ${error.message || 'Unknown error'}</p>`;
        document.getElementById('aiFeedbackRatingSection').style.display = 'none'; // Hide rating section
    } finally {
        feedbackBtn.disabled = false;
        feedbackBtn.textContent = "Get/Refresh AI Feedback";
    }
}


// Helper to display AI response content into the AI Feedback tab
function displayAIResponseBody(response, targetElement) {
    let feedbackHtml = '';
    
    // Extract raw feedback and format for clean display
    if (response.raw_llm_feedback) {
        const rawFeedback = response.raw_llm_feedback;
        
        // Look for the sections we want to display
        const criticalPattern = /1\.\s*CRITICAL\s+DISCREPANCIES:(.*?)(?=2\.\s*NON-CRITICAL|SECTION SEVERITY ASSESSMENT:|$)/is;
        const nonCriticalPattern = /2\.\s*NON-CRITICAL\s+DISCREPANCIES:(.*?)(?=SECTION SEVERITY ASSESSMENT:|$)/is;
        
        // Find the sections
        const criticalMatch = rawFeedback.match(criticalPattern);
        const nonCriticalMatch = rawFeedback.match(nonCriticalPattern);
        
        // Create a clean formatted display
        feedbackHtml += `<div class="feedback-container">`;
        
        // Add critical discrepancies if found
        if (criticalMatch && criticalMatch[1].trim() && !criticalMatch[1].trim().includes("None identified")) {
            const criticalContent = criticalMatch[1].trim();
            feedbackHtml += `
                <div class="feedback-section critical-section">
                    <h3>Critical Discrepancies</h3>
                    <div class="content">${formatDiscrepancyContent(criticalContent)}</div>
                </div>`;
        }
        
        // Add non-critical discrepancies if found
        if (nonCriticalMatch && nonCriticalMatch[1].trim() && !nonCriticalMatch[1].trim().includes("None identified")) {
            const nonCriticalContent = nonCriticalMatch[1].trim();
            feedbackHtml += `
                <div class="feedback-section moderate-section">
                    <h3>Non-Critical Discrepancies</h3>
                    <div class="content">${formatDiscrepancyContent(nonCriticalContent)}</div>
                </div>`;
        }
        
        // If no discrepancies were found in either section
        if ((!criticalMatch || criticalMatch[1].trim().includes("None identified")) && 
            (!nonCriticalMatch || nonCriticalMatch[1].trim().includes("None identified"))) {
            feedbackHtml += `
                <div class="feedback-section consistent-section">
                    <h3>AI Feedback</h3>
                    <p>No discrepancies identified. Your report is consistent with the expert assessment.</p>
                </div>`;
        }
        
        feedbackHtml += `</div>`;
    } else {
        // No raw feedback available
        feedbackHtml = `<p>No detailed feedback was provided by the AI.</p>`;
    }
    
    // Apply the HTML to the target element
    targetElement.innerHTML = feedbackHtml;
    
    // Add some styling
    const style = document.createElement('style');
    style.textContent = `
        .feedback-container {
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 8px;
        }
        .feedback-section {
            margin-bottom: 20px;
            padding: 12px;
            border-radius: 6px;
        }
        .critical-section {
            background-color: #feebeb;
            border-left: 4px solid #dc3545;
        }
        .moderate-section {
            background-color: #fff8e6;
            border-left: 4px solid #ffc107;
        }
        .consistent-section {
            background-color: #e6f9ed;
            border-left: 4px solid #28a745;
        }
        .feedback-section h3 {
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 16px;
            font-weight: 600;
        }
        .feedback-section ul {
            margin-top: 8px;
            padding-left: 20px;
        }
        .feedback-section li {
            margin-bottom: 8px;
        }
    `;
    targetElement.appendChild(style);
}

// Helper function to format discrepancy content
function formatDiscrepancyContent(content) {
    // Replace bullet points with proper HTML list items
    let formatted = content.replace(/\s*-\s*You\s+/g, "<li>You ");
    
    // If we have list items, wrap them in a ul
    if (formatted.includes("<li>")) {
        formatted = "<ul>" + formatted + "</ul>";
    } else {
        // Otherwise just wrap in paragraphs
        formatted = "<p>" + formatted.replace(/\n\n/g, "</p><p>") + "</p>";
    }
    
    return formatted;
}


// Populate expert language selector
async function populateExpertLanguageSelector(caseId, appliedTemplates, userReportData) { 
    const selectorContainer = document.getElementById('expertLanguageSelector');
    const contentContainer = document.getElementById('expertTemplateContentContainer');
    if (!selectorContainer || !contentContainer) return;

    selectorContainer.innerHTML = '<strong>View Expert Report In:</strong> ';

    if (!appliedTemplates || appliedTemplates.length === 0) {
        selectorContainer.innerHTML += ' <span>No expert versions available.</span>';
        contentContainer.innerHTML = '<p>No expert templates are available for this case.</p>';
        return;
    }

    // This map is no longer used for rendering in this function, as per the new requirement,
    // but kept as a placeholder if future logic needs it.
    const userReportSectionsMap = {}; 
    if (userReportData && userReportData.structured_content) {
        userReportData.structured_content.forEach(section => {
            userReportSectionsMap[section.master_template_section_id] = section;
        });
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
                    // NEW: Consistent UL class
                    let html = '<ul class="expert-report-sections-list">'; 
                    expertContent.section_contents.forEach(expertSection => {
                        const expertSectionContent = expertSection.content || '<em>No content provided.</em>';

                        // MODIFIED HTML STRUCTURE AND CLASSES HERE for consistency
                        html += `
                            <li class="report-section-display-item">
                                <strong class="report-section-title-display">${expertSection.master_section_name}:</strong>
                                <div class="report-section-content-display">
                                    <p>${expertSectionContent}</p>
                                </div>
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
                
                // Fetch the newly submitted report to get its AI feedback content
                const myReportsResponse = await apiRequest('/cases/my-reports/');
                let allUserReports = [];
                if (myReportsResponse && Array.isArray(myReportsResponse.results)) {
                    allUserReports = myReportsResponse.results;
                } else if (myReportsResponse && Array.isArray(myReportsResponse)) {
                    allUserReports = myReportsResponse;
                }
                const newUserReportForCase = allUserReports.find(report => 
                    String(report.case) === String(caseId) || 
                    (report.case && typeof report.case === 'object' && String(report.case.id) === String(caseId)) ||
                    (report.case_id && String(report.case_id) === String(caseId))
                );

                if(newUserReportForCase){
                    const reportSubmissionSection = document.getElementById('reportSubmissionSection');
                    const caseReviewTabsContainer = document.getElementById('caseReviewTabsContainer');
                    const userSubmittedReportContentDiv = document.getElementById('userSubmittedReportSectionContent');
                    
                    if (reportSubmissionSection) reportSubmissionSection.style.display = 'none';
                    if (caseReviewTabsContainer) caseReviewTabsContainer.style.display = 'block';
                    
                    // NEW: Store the newly submitted report globally
                    currentUserReportData = newUserReportForCase;

                    // Display user's report (which now might have AI feedback)
                    displayUserSubmittedReport(newUserReportForCase, userSubmittedReportContentDiv);
                    // Populate expert language selector
                    populateExpertLanguageSelector(caseId, updatedCaseData.applied_templates || [], newUserReportForCase);
                    
                    // IMPORTANT: Immediately request AI feedback here for the newly submitted report
                    // This ensures it generates and saves, and then displays.
                    requestAIFeedback(newUserReportForCase.id); 

                    // Activate the "Your Submitted Report" tab by default
                    document.querySelector('.info-tab-button[data-tab-target="#userSubmittedReportSectionContent"]')?.click();
                }

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


// Enhanced tooltip function with expert content comparison
function setupReportSectionTooltips(containerElement) {
    const reportSections = containerElement.querySelectorAll('.report-section-display-item');
    let currentTooltip = null;
    
    // Try to find the expert content for comparison
    let expertSectionContents = {};
    const expertTemplateContentContainer = document.getElementById('expertTemplateContentContainer');
    
    // Cache any expert template content that's currently loaded
    if (expertTemplateContentContainer) {
        const expertSections = expertTemplateContentContainer.querySelectorAll('.report-section-display-item');
        expertSections.forEach(expertSection => {
            const sectionNameElement = expertSection.querySelector('.report-section-title-display');
            const contentElement = expertSection.querySelector('.report-section-content-display p');
            
            if (sectionNameElement && contentElement) {
                const name = sectionNameElement.textContent.replace(':', '').trim();
                const content = contentElement.textContent.trim();
                expertSectionContents[name] = content;
                console.log(`Cached expert content for section "${name}"`);
            }
        });
    }
    
    // Style for the expert content
    const expertStyleCSS = `
        .expert-comparison {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px dashed #ccc;
            font-size: 0.9em;
        }
        .expert-comparison h4 {
            margin: 0 0 5px 0;
            font-size: 0.9em;
            color: #444;
        }
        .expert-comparison p {
            margin: 0;
            padding: 5px;
            background-color: #f5f5f5;
            border-left: 3px solid #28a745;
            font-style: italic;
        }
    `;

    reportSections.forEach(section => {
        const aiComment = section.dataset.aiComment;
        const aiSeverity = section.dataset.aiSeverity;
        const sectionName = section.dataset.sectionName;
        
        // Always add tooltip, even without AI comment
        section.addEventListener('mouseenter', (e) => {
            // Remove any existing tooltip
            if (currentTooltip) {
                currentTooltip.remove();
            }

            currentTooltip = document.createElement('div');
            currentTooltip.className = 'ai-feedback-tooltip enhanced';
            
            // Add a style tag for the expert section styling
            const styleEl = document.createElement('style');
            styleEl.textContent = expertStyleCSS;
            currentTooltip.appendChild(styleEl);
            
            // Start with AI feedback if available
            let tooltipContent = '';
            if (aiComment && aiSeverity) {
                tooltipContent += `
                    <div class="ai-feedback-content">
                        <h3>${sectionName} <span class="severity-badge ${aiSeverity.toLowerCase()}">${aiSeverity}</span></h3>
                        <p>${aiComment}</p>
                    </div>
                `;
            } else {
                tooltipContent += `
                    <div class="ai-feedback-content">
                        <h3>${sectionName}</h3>
                        <p class="no-feedback">No specific feedback for this section</p>
                    </div>
                `;
            }
            
            // Add expert content comparison if available
            if (expertSectionContents[sectionName]) {
                tooltipContent += `
                    <div class="expert-comparison">
                        <h4>Expert's Content:</h4>
                        <p>${expertSectionContents[sectionName]}</p>
                    </div>
                `;
            }
            
            currentTooltip.innerHTML += tooltipContent;
            document.body.appendChild(currentTooltip);

            // Position the tooltip
            const rect = section.getBoundingClientRect();
            currentTooltip.style.left = `${rect.left + window.scrollX + rect.width / 2 - currentTooltip.offsetWidth / 2}px`;
            currentTooltip.style.top = `${rect.top + window.scrollY - currentTooltip.offsetHeight - 10}px`;

            // Ensure it doesn't go off-screen
            if (parseFloat(currentTooltip.style.left) < 0) {
                currentTooltip.style.left = '5px';
            }
            if (parseFloat(currentTooltip.style.left) + currentTooltip.offsetWidth > window.innerWidth) {
                currentTooltip.style.left = `${window.innerWidth - currentTooltip.offsetWidth - 5}px`;
            }

            // Animation
            setTimeout(() => currentTooltip.classList.add('show'), 10);
        });

        section.addEventListener('mouseleave', () => {
            if (currentTooltip) {
                currentTooltip.classList.remove('show');
                currentTooltip.addEventListener('transitionend', () => {
                    if (currentTooltip && currentTooltip.parentNode) {
                        currentTooltip.remove();
                    }
                    currentTooltip = null;
                }, { once: true });
            }
        });
    });
}
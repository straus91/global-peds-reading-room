/**
 * Admin Prompt Versions Dashboard - Phase 1
 * Manage AI feedback prompt versions and A/B testing
 */

console.log('🔧 Dashboard Version: 2025-01-14-fix-v1');

const API_BASE = '/api';

// Show/hide states
function showLoading() {
    document.getElementById('loadingState').style.display = 'block';
    document.getElementById('errorState').style.display = 'none';
    document.getElementById('dashboardContent').style.display = 'none';
}

function showError() {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('errorState').style.display = 'block';
    document.getElementById('dashboardContent').style.display = 'none';
}

function showDashboard() {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('errorState').style.display = 'none';
    document.getElementById('dashboardContent').style.display = 'block';
}

// Fetch prompt versions
async function fetchPromptVersions() {
    try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            window.location.href = '/app/login.html';
            return null;
        }

        const response = await fetch(`${API_BASE}/cases/prompt-versions/analytics/by-version/`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.status === 401) {
            window.location.href = '/app/login.html';
            return null;
        }

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Failed to fetch prompt versions:', error);
        throw error;
    }
}

// Render versions table
function renderVersionsTable(versions) {
    const tbody = document.getElementById('versionsTableBody');

    if (!versions || versions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="11" style="text-align: center; padding: 20px; color: #888;">
                    No prompt versions found. Create your first version!
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = versions.map(version => {
        const statusBadge = version.is_active ?
            '<span style="background: #6aa84f; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">ACTIVE</span>' :
            '<span style="background: #e0e0e0; color: #666; padding: 4px 8px; border-radius: 4px; font-size: 12px;">Inactive</span>';

        const avgRating = (version.avg_overall != null) ? version.avg_overall.toFixed(2) : 'N/A';
        const accuracy = (version.avg_accuracy != null) ? version.avg_accuracy.toFixed(2) : 'N/A';
        const helpfulness = (version.avg_helpfulness != null) ? version.avg_helpfulness.toFixed(2) : 'N/A';
        const actionability = (version.avg_actionability != null) ? version.avg_actionability.toFixed(2) : 'N/A';
        const avgTokens = (version.average_tokens_per_use != null) ?
            Math.round(version.average_tokens_per_use).toLocaleString() : 'N/A';

        const createdDate = new Date(version.created_at).toLocaleDateString();

        const activateButton = version.is_active ?
            `<button class="btn btn-sm btn-secondary" disabled>Active</button>` :
            `<button class="btn btn-sm btn-primary" onclick="activateVersion('${version.prompt_version_id}')">Activate</button>`;

        return `
            <tr>
                <td style="font-weight: bold;">${version.version_name}</td>
                <td>${version.version_name}</td>
                <td>${statusBadge}</td>
                <td>${version.total_uses || 0}</td>
                <td>${avgRating}</td>
                <td>${accuracy}</td>
                <td>${helpfulness}</td>
                <td>${actionability}</td>
                <td>${avgTokens}</td>
                <td>${createdDate}</td>
                <td>
                    <div style="display: flex; gap: 5px;">
                        ${activateButton}
                        <button class="btn btn-sm btn-secondary" onclick="viewVersion('${version.prompt_version_id}')">View</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Render quick stats
function renderQuickStats(versions) {
    if (!versions) return;

    // Total versions
    document.getElementById('totalVersions').textContent = versions.length;

    // Active version
    const activeVersion = versions.find(v => v.is_active);
    document.getElementById('activeVersion').textContent =
        activeVersion ? activeVersion.version_name : 'None';

    // Best rating
    const ratingsWithData = versions.filter(v => v.avg_overall !== null);
    const bestRating = ratingsWithData.length > 0 ?
        Math.max(...ratingsWithData.map(v => v.avg_overall)) : null;
    document.getElementById('bestRating').textContent =
        bestRating !== null ? bestRating.toFixed(2) : 'N/A';

    // A/B tests count
    const abTestCount = versions.filter(v => v.is_ab_test).length;
    document.getElementById('abTestCount').textContent = abTestCount;
}

// Activate a prompt version
async function activateVersion(versionId) {
    if (!confirm('Are you sure you want to activate this prompt version? This will deactivate all other versions and invalidate cache.')) {
        return;
    }

    try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            window.location.href = '/app/login.html';
            return;
        }

        const response = await fetch(`${API_BASE}/cases/prompt-versions/${versionId}/activate/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to activate version: ${response.status}`);
        }

        const result = await response.json();
        alert(`Success: ${result.message || 'Version activated'}`);

        // Reload data
        initDashboard();
    } catch (error) {
        console.error('Failed to activate version:', error);
        alert('Failed to activate version. Please try again.');
    }
}

// View version details (placeholder)
function viewVersion(versionId) {
    alert(`View version details: ${versionId}\n\nThis feature will show the full prompt template and performance metrics.`);
    // Future implementation: Show modal with version details
}

// Show/hide create form
function showCreateForm() {
    document.getElementById('createFormSection').style.display = 'block';
    document.getElementById('createFormSection').scrollIntoView({ behavior: 'smooth' });
}

function hideCreateForm() {
    document.getElementById('createFormSection').style.display = 'none';
    document.getElementById('createVersionForm').reset();
}

// Handle create version form submission
async function handleCreateVersion(event) {
    event.preventDefault();

    const formData = {
        version_number: document.getElementById('versionNumber').value,
        name: document.getElementById('versionName').value,
        description: document.getElementById('versionDescription').value,
        prompt_template: document.getElementById('promptTemplate').value,
        is_active: document.getElementById('isActive').checked
    };

    try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            window.location.href = '/app/login.html';
            return;
        }

        const response = await fetch(`${API_BASE}/cases/prompt-versions/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create version');
        }

        const result = await response.json();
        alert('Prompt version created successfully!');

        // Hide form and reload data
        hideCreateForm();
        initDashboard();
    } catch (error) {
        console.error('Failed to create version:', error);
        alert(`Failed to create version: ${error.message}`);
    }
}

// Initialize dashboard
async function initDashboard() {
    showLoading();

    try {
        const response = await fetchPromptVersions();
        if (!response) return;

        // Extract versions array from response
        const versions = response.versions || [];

        renderVersionsTable(versions);
        renderQuickStats(versions);

        showDashboard();
    } catch (error) {
        console.error('Dashboard initialization failed:', error);
        showError();
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    initDashboard();

    // Create new button
    document.getElementById('createNewBtn').addEventListener('click', showCreateForm);

    // Cancel buttons
    document.getElementById('cancelCreateBtn').addEventListener('click', hideCreateForm);
    document.getElementById('cancelCreateBtn2').addEventListener('click', hideCreateForm);

    // Form submission
    document.getElementById('createVersionForm').addEventListener('submit', handleCreateVersion);
});

// Expose functions globally for onclick handlers
window.activateVersion = activateVersion;
window.viewVersion = viewVersion;

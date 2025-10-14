/**
 * Admin Feedback Dashboard - Phase 1
 * Fetches AI feedback quality metrics and renders visualizations
 */

console.log('🔧 Dashboard Version: 2025-01-14-fix-v1');

const API_BASE = '/api';
let trendChart = null;

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

// Fetch analytics data from multiple endpoints
async function fetchAnalytics() {
    try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            window.location.href = '/app/login.html';
            return null;
        }

        const headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };

        // Fetch from 4 specialized endpoints in parallel
        const [overallResponse, difficultyResponse, trendsResponse, falsePosResponse] = await Promise.all([
            fetch(`${API_BASE}/cases/detailed-ratings/analytics/`, { headers }),
            fetch(`${API_BASE}/cases/detailed-ratings/analytics/by-difficulty/`, { headers }),
            fetch(`${API_BASE}/cases/detailed-ratings/analytics/trends/?days=30`, { headers }),
            fetch(`${API_BASE}/cases/detailed-ratings/analytics/false-positives/`, { headers })
        ]);

        // Check for auth errors
        if (overallResponse.status === 401) {
            window.location.href = '/app/login.html';
            return null;
        }

        // Check all responses ok
        if (!overallResponse.ok || !difficultyResponse.ok || !trendsResponse.ok || !falsePosResponse.ok) {
            throw new Error(`API error: ${overallResponse.status}`);
        }

        // Parse all responses
        const [overall, difficulty, trends, falsePos] = await Promise.all([
            overallResponse.json(),
            difficultyResponse.json(),
            trendsResponse.json(),
            falsePosResponse.json()
        ]);

        // Transform into expected structure for render functions
        return {
            overall_metrics: {
                average_accuracy: overall.average_accuracy,
                average_helpfulness: overall.average_helpfulness,
                average_actionability: overall.average_actionability,
                average_overall: overall.average_overall,
                total_ratings: overall.total_ratings,
                false_positive_count: overall.false_positive_count,
                false_positive_rate: overall.false_positive_percentage ? overall.false_positive_percentage / 100 : null
            },
            by_difficulty: difficulty.by_difficulty || [],
            trend_last_30_days: trends.weekly_trends || [],
            false_positive_examples: falsePos.false_positives || []
        };
    } catch (error) {
        console.error('Failed to fetch analytics:', error);
        throw error;
    }
}

// Render overall metrics cards
function renderMetrics(data) {
    const { overall_metrics } = data;

    // Accuracy
    document.getElementById('avgAccuracy').textContent =
        (overall_metrics.average_accuracy != null) ?
        `${overall_metrics.average_accuracy.toFixed(1)}/5.0` : 'N/A';
    document.getElementById('accuracyCount').textContent =
        `${overall_metrics.total_ratings || 0} ratings`;

    // Helpfulness
    document.getElementById('avgHelpfulness').textContent =
        (overall_metrics.average_helpfulness != null) ?
        `${overall_metrics.average_helpfulness.toFixed(1)}/5.0` : 'N/A';
    document.getElementById('helpfulnessCount').textContent =
        `${overall_metrics.total_ratings || 0} ratings`;

    // Actionability
    document.getElementById('avgActionability').textContent =
        (overall_metrics.average_actionability != null) ?
        `${overall_metrics.average_actionability.toFixed(1)}/5.0` : 'N/A';
    document.getElementById('actionabilityCount').textContent =
        `${overall_metrics.total_ratings || 0} ratings`;

    // Overall
    document.getElementById('avgOverall').textContent =
        (overall_metrics.average_overall != null) ?
        `${overall_metrics.average_overall.toFixed(1)}/5.0` : 'N/A';
    document.getElementById('overallCount').textContent =
        `${overall_metrics.total_ratings || 0} ratings`;
}

// Render trend chart
function renderTrendChart(data) {
    const { trend_last_30_days } = data;

    const ctx = document.getElementById('trendChart').getContext('2d');

    // Destroy existing chart if it exists
    if (trendChart) {
        trendChart.destroy();
    }

    if (!trend_last_30_days || trend_last_30_days.length === 0) {
        // No data - show empty chart with message
        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Overall Rating',
                    data: [],
                    borderColor: '#4a86e8',
                    backgroundColor: 'rgba(74, 134, 232, 0.1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: true, position: 'top' },
                    title: {
                        display: true,
                        text: 'No trend data available yet'
                    }
                }
            }
        });
        return;
    }

    // Backend returns week_start and average_overall
    const dates = trend_last_30_days.map(item => {
        const date = new Date(item.week_start);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    const overallRatings = trend_last_30_days.map(item =>
        (item.average_overall != null) ? item.average_overall : 0
    );

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Overall Rating',
                data: overallRatings,
                borderColor: '#4a86e8',
                backgroundColor: 'rgba(74, 134, 232, 0.1)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Rating: ${context.parsed.y.toFixed(2)}/5.0`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 1,
                    max: 5,
                    ticks: {
                        stepSize: 0.5
                    },
                    title: {
                        display: true,
                        text: 'Rating (1-5)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Week Starting'
                    }
                }
            }
        }
    });
}

// Render difficulty breakdown table
function renderDifficultyTable(data) {
    const { by_difficulty } = data;
    const tbody = document.getElementById('difficultyTableBody');

    if (!by_difficulty || by_difficulty.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 20px; color: #888;">
                    No data available yet
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = by_difficulty.map(item => {
        const difficulty = item.difficulty || 'Unknown';
        const accuracy = (item.average_accuracy != null) ? item.average_accuracy.toFixed(1) : 'N/A';
        const helpfulness = (item.average_helpfulness != null) ? item.average_helpfulness.toFixed(1) : 'N/A';
        const actionability = (item.average_actionability != null) ? item.average_actionability.toFixed(1) : 'N/A';
        const overall = (item.average_overall != null) ? item.average_overall.toFixed(1) : 'N/A';
        const count = item.rating_count || 0;

        return `
            <tr>
                <td style="text-transform: capitalize; font-weight: bold;">${difficulty}</td>
                <td>${accuracy}</td>
                <td>${helpfulness}</td>
                <td>${actionability}</td>
                <td>${overall}</td>
                <td>${count}</td>
            </tr>
        `;
    }).join('');
}

// Render false positives section
function renderFalsePositives(data) {
    const { overall_metrics, false_positive_examples } = data;

    // False positive rate
    const fpRate = (overall_metrics.false_positive_rate != null) ?
        `${(overall_metrics.false_positive_rate * 100).toFixed(1)}%` : 'N/A';
    document.getElementById('fpRate').textContent = fpRate;

    const fpCount = overall_metrics.false_positive_count || 0;
    const totalRatings = overall_metrics.total_ratings || 0;
    document.getElementById('fpCount').textContent = `${fpCount} of ${totalRatings} ratings`;

    // Recent examples - backend returns array with case_identifier, false_positive_details
    const examplesList = document.getElementById('fpExamples');
    if (!false_positive_examples || false_positive_examples.length === 0) {
        examplesList.innerHTML = '<li style="color: #888;">No false positives reported yet</li>';
    } else {
        examplesList.innerHTML = false_positive_examples.slice(0, 5).map(example => {
            const caseId = example.case_identifier || 'Unknown case';
            const details = example.false_positive_details || 'No details provided';
            const truncated = details.length > 80 ? details.substring(0, 80) + '...' : details;
            return `<li style="margin-bottom: 8px;"><strong>${caseId}</strong>: "${truncated}"</li>`;
        }).join('');
    }
}

// Initialize dashboard
async function initDashboard() {
    showLoading();

    try {
        const data = await fetchAnalytics();
        if (!data) return;

        renderMetrics(data);
        renderTrendChart(data);
        renderDifficultyTable(data);
        renderFalsePositives(data);

        showDashboard();
    } catch (error) {
        console.error('Dashboard initialization failed:', error);
        showError();
    }
}

// Run on page load
document.addEventListener('DOMContentLoaded', initDashboard);

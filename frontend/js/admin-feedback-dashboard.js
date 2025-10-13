/**
 * Admin Feedback Dashboard - Phase 1
 * Fetches AI feedback quality metrics and renders visualizations
 */

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

// Fetch analytics data
async function fetchAnalytics() {
    try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            window.location.href = '/app/login.html';
            return null;
        }

        const response = await fetch(`${API_BASE}/detailed-ratings/analytics/`, {
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
        console.error('Failed to fetch analytics:', error);
        throw error;
    }
}

// Render overall metrics cards
function renderMetrics(data) {
    const { overall_metrics } = data;

    // Accuracy
    document.getElementById('avgAccuracy').textContent =
        overall_metrics.average_accuracy !== null ?
        `${overall_metrics.average_accuracy.toFixed(1)}/5.0` : 'N/A';
    document.getElementById('accuracyCount').textContent =
        `${overall_metrics.total_ratings} ratings`;

    // Helpfulness
    document.getElementById('avgHelpfulness').textContent =
        overall_metrics.average_helpfulness !== null ?
        `${overall_metrics.average_helpfulness.toFixed(1)}/5.0` : 'N/A';
    document.getElementById('helpfulnessCount').textContent =
        `${overall_metrics.total_ratings} ratings`;

    // Actionability
    document.getElementById('avgActionability').textContent =
        overall_metrics.average_actionability !== null ?
        `${overall_metrics.average_actionability.toFixed(1)}/5.0` : 'N/A';
    document.getElementById('actionabilityCount').textContent =
        `${overall_metrics.total_ratings} ratings`;

    // Overall
    document.getElementById('avgOverall').textContent =
        overall_metrics.average_overall !== null ?
        `${overall_metrics.average_overall.toFixed(1)}/5.0` : 'N/A';
    document.getElementById('overallCount').textContent =
        `${overall_metrics.total_ratings} ratings`;
}

// Render trend chart
function renderTrendChart(data) {
    const { trend_last_30_days } = data;

    const ctx = document.getElementById('trendChart').getContext('2d');

    // Destroy existing chart if it exists
    if (trendChart) {
        trendChart.destroy();
    }

    const dates = trend_last_30_days.map(item => item.date);
    const overallRatings = trend_last_30_days.map(item => item.avg_overall || 0);

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
                        text: 'Date'
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
        const accuracy = item.avg_accuracy !== null ? item.avg_accuracy.toFixed(1) : 'N/A';
        const helpfulness = item.avg_helpfulness !== null ? item.avg_helpfulness.toFixed(1) : 'N/A';
        const actionability = item.avg_actionability !== null ? item.avg_actionability.toFixed(1) : 'N/A';
        const overall = item.avg_overall !== null ? item.avg_overall.toFixed(1) : 'N/A';
        const count = item.count || 0;

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
    const fpRate = overall_metrics.false_positive_rate !== null ?
        `${(overall_metrics.false_positive_rate * 100).toFixed(1)}%` : 'N/A';
    document.getElementById('fpRate').textContent = fpRate;

    const fpCount = overall_metrics.false_positive_count || 0;
    const totalRatings = overall_metrics.total_ratings || 0;
    document.getElementById('fpCount').textContent = `${fpCount} of ${totalRatings} ratings`;

    // Recent examples
    const examplesList = document.getElementById('fpExamples');
    if (!false_positive_examples || false_positive_examples.length === 0) {
        examplesList.innerHTML = '<li style="color: #888;">No false positives reported yet</li>';
    } else {
        examplesList.innerHTML = false_positive_examples.slice(0, 5).map(example =>
            `<li style="margin-bottom: 8px;">${example.case_identifier || 'Unknown case'}: "${example.details ? example.details.substring(0, 80) + '...' : 'No details'}"</li>`
        ).join('');
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

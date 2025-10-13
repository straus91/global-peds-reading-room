/**
 * Admin Cost Dashboard - Phase 1
 * Fetches token usage and cost metrics, renders visualizations
 */

const API_BASE = '/api';
let costChart = null;

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

// Fetch cost trends data
async function fetchCostTrends() {
    try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            window.location.href = '/app/login.html';
            return null;
        }

        const response = await fetch(`${API_BASE}/detailed-ratings/analytics/cost-trends/?days=30`, {
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
        console.error('Failed to fetch cost trends:', error);
        throw error;
    }
}

// Fetch cache performance data
async function fetchCachePerformance() {
    try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            return null;
        }

        const response = await fetch(`${API_BASE}/detailed-ratings/analytics/cache-performance/?days=30`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Failed to fetch cache performance:', error);
        throw error;
    }
}

// Render today's usage summary
function renderTodayUsage(data) {
    const { total_cost_usd, total_requests, cached_requests, daily_breakdown } = data;

    // Get today's data (last item in daily_breakdown)
    const todayData = daily_breakdown.length > 0 ? daily_breakdown[daily_breakdown.length - 1] : null;

    if (todayData) {
        // Today's cost
        const cost = parseFloat(todayData.cost_usd) || 0;
        document.getElementById('todayCost').textContent = `$${cost.toFixed(2)}`;

        // Budget progress
        const budget = 10.00;
        const percentage = (cost / budget) * 100;
        document.getElementById('budgetProgress').style.width = `${Math.min(percentage, 100)}%`;
        document.getElementById('budgetText').textContent = `of $${budget.toFixed(2)} budget`;

        // Color code based on usage
        const progressBar = document.getElementById('budgetProgress');
        if (percentage > 80) {
            progressBar.style.background = '#e06666'; // Red
        } else if (percentage > 50) {
            progressBar.style.background = '#f1c232'; // Yellow
        } else {
            progressBar.style.background = '#4a86e8'; // Blue
        }

        // Requests
        document.getElementById('todayRequests').textContent = todayData.requests || 0;
        document.getElementById('todayCached').textContent = todayData.cached_count || 0;
        document.getElementById('todayUncached').textContent = (todayData.requests || 0) - (todayData.cached_count || 0);

        // Tokens
        const totalTokens = todayData.prompt_tokens + todayData.completion_tokens;
        const avgTokens = todayData.requests > 0 ? Math.round(totalTokens / todayData.requests) : 0;
        document.getElementById('avgTokens').textContent = avgTokens.toLocaleString();
        document.getElementById('totalTokens').textContent = `${totalTokens.toLocaleString()} total tokens`;
    } else {
        // No data yet
        document.getElementById('todayCost').textContent = '$0.00';
        document.getElementById('todayRequests').textContent = '0';
        document.getElementById('todayCached').textContent = '0';
        document.getElementById('todayUncached').textContent = '0';
        document.getElementById('avgTokens').textContent = '0';
        document.getElementById('totalTokens').textContent = '0 total tokens';
    }
}

// Render 30-day cost chart
function renderCostChart(data) {
    const { daily_breakdown } = data;

    const ctx = document.getElementById('costChart').getContext('2d');

    // Destroy existing chart if it exists
    if (costChart) {
        costChart.destroy();
    }

    const dates = daily_breakdown.map(item => item.date);
    const costs = daily_breakdown.map(item => parseFloat(item.cost_usd) || 0);

    costChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Daily Cost (USD)',
                data: costs,
                backgroundColor: '#4a86e8',
                borderColor: '#4a86e8',
                borderWidth: 1
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
                            return `Cost: $${context.parsed.y.toFixed(4)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Cost (USD)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
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

// Render cache performance
function renderCachePerformance(cacheData) {
    if (!cacheData) {
        document.getElementById('cacheHitRate').textContent = 'N/A';
        document.getElementById('cacheSavings').textContent = '$0.00';
        document.getElementById('cacheStats').textContent = 'No data';
        return;
    }

    // Hit rate
    const hitRate = cacheData.cache_hit_rate !== null ?
        `${cacheData.cache_hit_rate.toFixed(1)}%` : 'N/A';
    document.getElementById('cacheHitRate').textContent = hitRate;

    // Savings
    const savings = parseFloat(cacheData.cost_savings_usd) || 0;
    document.getElementById('cacheSavings').textContent = `$${savings.toFixed(2)}`;

    // Cache stats
    const active = cacheData.total_cached_entries || 0;
    const expired = cacheData.expired_entries || 0;
    document.getElementById('cacheStats').textContent = `Active: ${active} | Expired: ${expired}`;
}

// Render most expensive cases (from cost trends data)
function renderExpensiveCases(data) {
    const tbody = document.getElementById('expensiveCasesBody');

    // For now, show placeholder - this would require additional API endpoint
    // or processing of daily_breakdown data
    tbody.innerHTML = `
        <tr>
            <td colspan="3" style="text-align: center; padding: 20px; color: #888;">
                Coming soon - requires per-case cost tracking
            </td>
        </tr>
    `;

    // Future implementation would look like:
    // if (data.expensive_cases && data.expensive_cases.length > 0) {
    //     tbody.innerHTML = data.expensive_cases.slice(0, 5).map(caseData => `
    //         <tr>
    //             <td>${caseData.case_identifier}</td>
    //             <td>$${caseData.avg_cost.toFixed(4)}</td>
    //             <td>${caseData.request_count}</td>
    //         </tr>
    //     `).join('');
    // }
}

// Initialize dashboard
async function initDashboard() {
    showLoading();

    try {
        const [costData, cacheData] = await Promise.all([
            fetchCostTrends(),
            fetchCachePerformance()
        ]);

        if (!costData) return;

        renderTodayUsage(costData);
        renderCostChart(costData);
        renderCachePerformance(cacheData);
        renderExpensiveCases(costData);

        showDashboard();
    } catch (error) {
        console.error('Dashboard initialization failed:', error);
        showError();
    }
}

// Run on page load
document.addEventListener('DOMContentLoaded', initDashboard);

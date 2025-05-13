// In a new file ui.js
const UI = {
    // Show/hide loading state
    loading: {
        show(container, message = 'Loading...') {
            // If container is a string, treat as selector
            if (typeof container === 'string') {
                container = document.querySelector(container);
            }
            if (!container) return;
            
            // Create or update loading indicator
            let loader = container.querySelector('.loading-indicator');
            if (!loader) {
                loader = document.createElement('div');
                loader.className = 'loading-indicator';
                container.appendChild(loader);
            }
            loader.innerHTML = `<div class="spinner"></div><p>${message}</p>`;
            loader.style.display = 'flex';
        },
        
        hide(container) {
            if (typeof container === 'string') {
                container = document.querySelector(container);
            }
            if (!container) return;
            
            const loader = container.querySelector('.loading-indicator');
            if (loader) {
                loader.style.display = 'none';
            }
        }
    },
    
    // Enhanced toast system
    toast: {
        show(message, type = 'info', duration = 3000) {
            const container = document.getElementById('toastContainer');
            if (!container) return false;
            
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `
                <div class="toast-content">${message}</div>
                <button class="toast-close">&times;</button>
            `;
            
            // Add close handler
            toast.querySelector('.toast-close').addEventListener('click', () => {
                toast.classList.add('toast-hiding');
                setTimeout(() => toast.remove(), 300);
            });
            
            container.appendChild(toast);
            
            // Trigger animation
            setTimeout(() => toast.classList.add('toast-visible'), 10);
            
            // Auto-close after duration
            if (duration > 0) {
                setTimeout(() => {
                    if (document.body.contains(toast)) {
                        toast.classList.add('toast-hiding');
                        setTimeout(() => toast.remove(), 300);
                    }
                }, duration);
            }
            
            return toast;
        }
    },
    
    // Table utilities
    table: {
        // Clear and show loading state in a table
        showLoading(tableBody, colSpan) {
            if (typeof tableBody === 'string') {
                tableBody = document.querySelector(tableBody);
            }
            if (!tableBody) return;
            
            tableBody.innerHTML = `
                <tr class="table-loading-row">
                    <td colspan="${colSpan}" class="table-loading-cell">
                        <div class="spinner"></div>
                        <p>Loading data...</p>
                    </td>
                </tr>
            `;
        },
        
        // Show empty state in a table
        showEmpty(tableBody, colSpan, message = 'No items found') {
            if (typeof tableBody === 'string') {
                tableBody = document.querySelector(tableBody);
            }
            if (!tableBody) return;
            
            tableBody.innerHTML = `
                <tr class="table-empty-row">
                    <td colspan="${colSpan}" class="table-empty-cell">
                        ${message}
                    </td>
                </tr>
            `;
        }
    }
};

// Make it globally available
window.UI = UI;
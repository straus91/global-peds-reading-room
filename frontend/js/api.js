// js/api.js - API utility functions with improved error handling

// API configuration is now managed by config.js
// APP_CONFIG is available globally after config.js loads

// Token refresh state management
let isRefreshing = false;
let refreshPromise = null;

/**
 * Retrieves the stored authentication tokens (access & refresh).
 * @returns {object|null} Object with accessToken and refreshToken, or null if not found.
 */
function getAuthTokens() {
    const accessToken = localStorage.getItem('accessToken');
    const refreshToken = localStorage.getItem('refreshToken');
    
    if (accessToken) {
        return { accessToken, refreshToken };
    }
    return null;
}

/**
 * Stores the authentication tokens in localStorage.
 * @param {string} accessToken - The access token.
 * @param {string} refreshToken - The refresh token.
 */
function setAuthTokens(accessToken, refreshToken) {
    if (accessToken) {
        localStorage.setItem('accessToken', accessToken);
        console.log('[setAuthTokens] Stored accessToken.');
    }
    if (refreshToken) {
        localStorage.setItem('refreshToken', refreshToken);
    }
}

/**
 * Clears the stored authentication tokens from localStorage.
 */
function clearAuthTokens() {
    console.log('[clearAuthTokens] Clearing tokens from localStorage.');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
}

/**
 * Refreshes the access token using the refresh token.
 * @returns {Promise<boolean>} True if refresh was successful, false otherwise.
 */
async function refreshAccessToken() {
    const tokens = getAuthTokens();
    if (!tokens || !tokens.refreshToken) {
        console.log('[refreshAccessToken] No refresh token available');
        return false;
    }

    try {
        console.log('[refreshAccessToken] Attempting to refresh token');
        const response = await fetch(`${APP_CONFIG.api.getBaseUrl()}/auth/login/refresh/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify({
                refresh: tokens.refreshToken
            })
        });

        if (!response.ok) {
            console.log('[refreshAccessToken] Refresh failed with status:', response.status);
            return false;
        }

        const data = await response.json();
        if (data.access) {
            setAuthTokens(data.access, tokens.refreshToken);
            console.log('[refreshAccessToken] Token refreshed successfully');
            return true;
        } else {
            console.log('[refreshAccessToken] No access token in response');
            return false;
        }
    } catch (error) {
        console.error('[refreshAccessToken] Error refreshing token:', error);
        return false;
    }
}

/**
 * Logs out the user by clearing tokens and redirecting to login page.
 */
function logoutUser() {
    console.log('[logoutUser] Logging out user');
    clearAuthTokens();
    // Reset refresh state
    isRefreshing = false;
    refreshPromise = null;
    // Redirect to login page with /app/ prefix
    if (window.location.pathname !== '/app/login.html' &&
        window.location.pathname !== '/app/' &&
        window.location.pathname !== '/app/index.html') {
        window.location.href = '/app/login.html';
    }
}

/**
 * Makes an authenticated request to the API.
 * Automatically adds the Authorization header with the access token.
 * Handles basic response checking and JSON parsing with improved error handling.
 * @param {string} endpoint - The API endpoint path (e.g., '/users/me/').
 * @param {object} options - Fetch options (method, body, headers, etc.).
 * @param {boolean} includeAuth - Whether to include the Authorization header (default: true).
 * @returns {Promise<object>} A promise that resolves with the JSON response data.
 * @throws {Error} Throws an error for network issues or non-OK HTTP responses.
 */
async function apiRequest(endpoint, options = {}, includeAuth = true) {
    const url = endpoint.startsWith('/') ? `${APP_CONFIG.api.getBaseUrl()}${endpoint}` : `${APP_CONFIG.api.getBaseUrl()}/${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers,
    };

    if (includeAuth) {
        const tokens = getAuthTokens();
        if (tokens && tokens.accessToken) {
            headers['Authorization'] = `Bearer ${tokens.accessToken}`;
        } else {
            // Handle missing token case
            console.warn(`Auth required for ${endpoint} but no token found`);
        }
    }

    const fetchOptions = {
        ...options,
        headers: headers,
    };

    try {
        const response = await fetch(url, fetchOptions);
        let data;

        // Try to parse JSON response, but handle cases where it might not be valid JSON
        try {
            const text = await response.text();
            data = text ? JSON.parse(text) : {};
        } catch (jsonError) {
            console.warn("Response is not valid JSON:", jsonError);
            // Create a simple object with the response text as detail for error message
            data = { detail: 'Invalid response format from server' };
        }

        if (!response.ok) {
            // Handle 401 Unauthorized - potentially expired token
            if (response.status === 401 && includeAuth) {
                console.log('[apiRequest] Got 401, attempting token refresh');

                // Check if we're already refreshing to avoid multiple simultaneous refresh attempts
                if (isRefreshing) {
                    console.log('[apiRequest] Token refresh already in progress, waiting...');
                    await refreshPromise;
                    // Retry the original request with the new token
                    return apiRequest(endpoint, options, includeAuth);
                }

                // Start the refresh process
                isRefreshing = true;
                refreshPromise = refreshAccessToken();

                const refreshSuccess = await refreshPromise;
                isRefreshing = false;
                refreshPromise = null;

                if (refreshSuccess) {
                    console.log('[apiRequest] Token refreshed successfully, retrying request');
                    // Retry the original request with the new token
                    return apiRequest(endpoint, options, includeAuth);
                } else {
                    console.log('[apiRequest] Token refresh failed, logging out user');
                    logoutUser();
                    const error = new Error('Session expired. Please log in again.');
                    error.status = 401;
                    error.data = { detail: 'Session expired' };
                    throw error;
                }
            }

            console.error("API Error Details:", data);

            // Create a more informative error object
            const error = new Error(data?.detail || `HTTP error ${response.status}`);
            error.status = response.status;
            error.data = data;
            throw error;
        }

        return data;
    } catch (error) {
        // Enhance error handling
        if (!error.status) {
            // This is likely a network error (not an HTTP response error)
            console.error(`Network error with API request to ${endpoint}:`, error);
            error.message = `Network error: ${error.message}`;
        } else {
            console.error(`API Request failed (${error.status}): ${endpoint}`, error);
        }
        throw error;
    }
}
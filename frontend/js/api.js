// js/api.js - API utility functions with improved error handling

// Define the base URL for your backend API
const API_CONFIG = {
    BASE_URL: 'http://127.0.0.1:8000/api',
    // Add production URL based on environment
    // PROD_URL: 'https://api.globalpeds.org/api',
    
    getBaseUrl() {
        // Switch based on environment if needed
        return this.BASE_URL;
    }
};

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
    const url = endpoint.startsWith('/') ? `${API_CONFIG.getBaseUrl()}${endpoint}` : `${API_CONFIG.getBaseUrl()}/${endpoint}`;
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
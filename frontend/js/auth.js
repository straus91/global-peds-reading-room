// gr3/js/auth.js - Updated for Backend API Integration + Debugging

// NOTE: This script assumes api.js is loaded first in login.html

document.addEventListener('DOMContentLoaded', function() {
    // Ensure the country dropdown is loaded immediately after DOM is ready
    if (document.getElementById('registerCountry')) {
        loadCountries();
    }
    
    // Then initialize the rest of the auth functionality
    initAuth();
});

// Improve error handling for login/registration
async function handleLogin(email, password) {
    const submitButton = document.querySelector('#loginForm button[type="submit"]');
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-sm"></span> Logging in...';
    
    try {
        const response = await apiRequest('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        }, false);
        
        if (response.access && response.refresh) {
            setAuthTokens(response.access, response.refresh);
            await fetchUserDetailsAndRedirect();
        } else {
            throw new Error('Invalid response from server');
        }
    } catch (error) {
        const errorMessage = error.data?.detail || error.message || 'Login failed';
        showToast(errorMessage, 'error');
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Login';
    }
}

function initAuth() {
    if (!window.showToast) {
        window.showToast = function(message, type = 'info') {
            const toastContainer = document.getElementById('toastContainer');
            if (!toastContainer) { console.warn('Toast container not found.'); return; }
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.textContent = message;
            toastContainer.appendChild(toast);
            setTimeout(() => { toast.remove(); }, 3000);
        };
    }

    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const forgotPasswordForm = document.getElementById('forgotPasswordForm');
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const forgotPasswordLink = document.getElementById('forgotPasswordLink');
    const backToLoginBtn = document.getElementById('backToLoginBtn');

    // Load countries *before* setting up listeners that might depend on it
    // Ensure the select element exists before calling loadCountries
    if (document.getElementById('registerCountry')) {
        loadCountries();
    } else {
        console.error("#registerCountry select element not found on initial load.");
    }


    showForm(loginForm);
    if (loginTab) loginTab.classList.add('active');

    // --- Event Listeners ---
    loginTab?.addEventListener('click', () => { setActiveTab(loginTab, registerTab); showForm(loginForm); });
    registerTab?.addEventListener('click', () => { setActiveTab(registerTab, loginTab); showForm(registerForm); });
    forgotPasswordLink?.addEventListener('click', (e) => { e.preventDefault(); showForm(forgotPasswordForm); });
    backToLoginBtn?.addEventListener('click', () => { showForm(loginForm); setActiveTab(loginTab, registerTab); });

    // Login form submission (remains the same as previous version)
    loginForm?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        if (!email || !password) { showToast('Please fill in both email and password', 'error'); return; }
        const submitButton = loginForm.querySelector('button[type="submit"]');
        submitButton.disabled = true; submitButton.textContent = 'Logging in...';
        try {
            const response = await apiRequest('/auth/login/', { method: 'POST', body: JSON.stringify({ email: email, password: password }) }, false);
            if (response.access && response.refresh) {
                setAuthTokens(response.access, response.refresh);
                await fetchUserDetailsAndRedirect();
            } else { showToast('Login failed: Invalid response from server.', 'error'); }
        } catch (error) {
            console.error('Login error:', error);
            const errorMessage = error.data?.detail || error.message || 'Login failed. Please check your credentials.';
            if (error.status === 401) { showToast('Invalid credentials. Please try again.', 'error'); }
            else if (error.message.includes('User is not active')) { showToast('Account not active. Please wait for admin approval.', 'warning'); }
            else { showToast(errorMessage, 'error'); }
        } finally { submitButton.disabled = false; submitButton.textContent = 'Login'; }
    });

    // Register form submission with DEBUGGING
    registerForm?.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log("Register form submitted. Attempting to gather data..."); // Debug log

        const submitButton = registerForm.querySelector('button[type="submit"]');
        let formData = {}; // Initialize formData

        try {
            // --- DEBUGGING: Check each element before accessing value ---
            const firstNameEl = document.getElementById('registerFirstName');
            const lastNameEl = document.getElementById('registerLastName');
            const emailEl = document.getElementById('registerEmail');
            const passwordEl = document.getElementById('registerPassword');
            const password2El = document.getElementById('registerPasswordConfirm');
            const roleEl = document.getElementById('registerRole');
            const institutionEl = document.getElementById('registerInstitution');
            const countryEl = document.getElementById('registerCountry'); // The suspected element

            if (!firstNameEl) { console.error("Element with ID 'registerFirstName' not found!"); throw new Error("Form error: First name field missing."); }
            if (!lastNameEl) { console.error("Element with ID 'registerLastName' not found!"); throw new Error("Form error: Last name field missing."); }
            if (!emailEl) { console.error("Element with ID 'registerEmail' not found!"); throw new Error("Form error: Email field missing."); }
            if (!passwordEl) { console.error("Element with ID 'registerPassword' not found!"); throw new Error("Form error: Password field missing."); }
            if (!password2El) { console.error("Element with ID 'registerPasswordConfirm' not found!"); throw new Error("Form error: Confirm password field missing."); }
            if (!roleEl) { console.error("Element with ID 'registerRole' not found!"); throw new Error("Form error: Role field missing."); }
            if (!institutionEl) { console.error("Element with ID 'registerInstitution' not found!"); throw new Error("Form error: Institution field missing."); }
            if (!countryEl) {
                console.error("Element with ID 'registerCountry' not found! This is the likely cause.");
                throw new Error("Form error: Country field missing.");
            }
            console.log("All registration form elements found successfully."); // Debug log

            // If all elements found, gather values
            formData = {
                first_name: firstNameEl.value,
                last_name: lastNameEl.value,
                email: emailEl.value,
                password: passwordEl.value,
                password2: password2El.value,
                role: roleEl.value,
                institution: institutionEl.value,
                country: countryEl.value, // This was line ~135
            };
            console.log("Form data gathered:", formData); // Debug log

            // Basic frontend validation (can stay the same)
            if (!formData.first_name || !formData.last_name || !formData.email || !formData.password || !formData.password2 || !formData.role || !formData.institution || !formData.country) {
                showToast('Please fill in all required fields', 'error');
                return;
            }
            if (formData.password !== formData.password2) {
                showToast('Passwords do not match', 'error');
                return;
            }

            // Disable button
            submitButton.disabled = true;
            submitButton.textContent = 'Registering...';

            // Call the registration API endpoint
            const response = await apiRequest('/auth/register/', {
                method: 'POST',
                body: JSON.stringify(formData)
            }, false);

            showToast(response.message || 'Registration successful! Awaiting approval.', 'success');
            registerForm.reset();
            setActiveTab(loginTab, registerTab);
            showForm(loginForm);

        } catch (error) {
            console.error('Registration error:', error);
            // Display specific error from API or JS checks
            const errorMessage = error.data ? formatApiErrors(error.data) : (error.message || 'Registration failed. Please try again.');
            showToast(errorMessage, 'error');
        } finally {
            // Re-enable button only if it exists
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = 'Register';
            }
        }
    });

    // Forgot password form submission (remains the same)
    forgotPasswordForm?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const email = document.getElementById('resetEmail').value;
        if (!email) { showToast('Please enter your email address', 'error'); return; }
        const submitButton = forgotPasswordForm.querySelector('button[type="submit"]');
        submitButton.disabled = true; submitButton.textContent = 'Sending...';
        try {
            await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate network delay
            showToast('If an account exists for that email, a password reset link has been sent.', 'success');
            forgotPasswordForm.reset(); showForm(loginForm); setActiveTab(loginTab, registerTab);
        } catch (error) { console.error('Password reset error:', error); showToast('Failed to send reset link. Please try again later.', 'error');
        } finally { submitButton.disabled = false; submitButton.textContent = 'Send Reset Link'; }
    });
}

// Helper function to show the active form
function showForm(formToShow) { document.querySelectorAll('.auth-form').forEach(form => { form.style.display = 'none'; form.classList.remove('active'); }); if (formToShow) { formToShow.style.display = 'block'; formToShow.classList.add('active'); } }
// Helper function to set active tab
function setActiveTab(activeTab, inactiveTab) { activeTab?.classList.add('active'); inactiveTab?.classList.remove('active'); }
// Helper function to format API errors
function formatApiErrors(errors) { if (typeof errors === 'string') return errors; let messages = []; if (errors.detail) messages.push(errors.detail); for (const key in errors) { if (key !== 'detail' && Array.isArray(errors[key])) messages.push(`${key}: ${errors[key].join(' ')}`); else if (key !== 'detail') messages.push(`${key}: ${errors[key]}`); } return messages.join('; ') || 'An unknown error occurred.'; }

// Fetch user details after login
async function fetchUserDetailsAndRedirect() {
    try {
        const userData = await apiRequest('/users/me/');
        if (userData && userData.profile) {
             sessionStorage.setItem('user', JSON.stringify({ id: userData.id, name: `${userData.first_name} ${userData.last_name}`.trim() || userData.username, email: userData.email, role: userData.profile.role, isAdmin: userData.is_admin }));
            showToast('Login successful!', 'success');
            
            // Use robust relative path construction that works regardless of server setup
            const currentPath = window.location.pathname;
            const currentDir = currentPath.substring(0, currentPath.lastIndexOf('/') + 1);
            
            if (userData.is_admin) { 
                // From login.html to admin/dashboard.html
                window.location.href = currentDir + 'admin/dashboard.html'; 
            } else { 
                // From login.html to index.html  
                window.location.href = currentDir + 'index.html'; 
            }
        } else { throw new Error("User data or profile missing in response."); }
    } catch (error) { console.error("Failed to fetch user details after login:", error); showToast("Login successful, but failed to retrieve user details. Please try refreshing.", "warning"); clearAuthTokens(); }
}
// Load countries for the register form
function loadCountries() {
    const countrySelect = document.getElementById('registerCountry');
    if (!countrySelect) {
        console.error("Cannot load countries: #registerCountry element not found.");
        // Consider adding a retry mechanism or check if DOM is fully loaded
        return;
    }
    // Ensure the list isn't populated multiple times if initAuth runs again
    if (countrySelect.options.length > 1) {
        console.log("Countries already loaded.");
        return;
    }
    console.log("Loading countries..."); // Debug log
    // --- Use a more complete list ---
    const countries = ["Afghanistan","Albania","Algeria","Andorra","Angola","Antigua and Barbuda","Argentina","Armenia","Australia","Austria","Azerbaijan","Bahamas","Bahrain","Bangladesh","Barbados","Belarus","Belgium","Belize","Benin","Bhutan","Bolivia","Bosnia and Herzegovina","Botswana","Brazil","Brunei","Bulgaria","Burkina Faso","Burundi","Cabo Verde","Cambodia","Cameroon","Canada","Central African Republic","Chad","Chile","China","Colombia","Comoros","Congo, Democratic Republic of the","Congo, Republic of the","Costa Rica","Cote d'Ivoire","Croatia","Cuba","Cyprus","Czech Republic","Denmark","Djibouti","Dominica","Dominican Republic","Ecuador","Egypt","El Salvador","Equatorial Guinea","Eritrea","Estonia","Eswatini","Ethiopia","Fiji","Finland","France","Gabon","Gambia","Georgia","Germany","Ghana","Greece","Grenada","Guatemala","Guinea","Guinea-Bissau","Guyana","Haiti","Honduras","Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland","Israel","Italy","Jamaica","Japan","Jordan","Kazakhstan","Kenya","Kiribati","Korea, North","Korea, South","Kosovo","Kuwait","Kyrgyzstan","Laos","Latvia","Lebanon","Lesotho","Liberia","Libya","Liechtenstein","Lithuania","Luxembourg","Madagascar","Malawi","Malaysia","Maldives","Mali","Malta","Marshall Islands","Mauritania","Mauritius","Mexico","Micronesia","Moldova","Monaco","Mongolia","Montenegro","Morocco","Mozambique","Myanmar (Burma)","Namibia","Nauru","Nepal","Netherlands","New Zealand","Nicaragua","Niger","Nigeria","North Macedonia","Norway","Oman","Pakistan","Palau","Palestine State","Panama","Papua New Guinea","Paraguay","Peru","Philippines","Poland","Portugal","Qatar","Romania","Russia","Rwanda","Saint Kitts and Nevis","Saint Lucia","Saint Vincent and the Grenadines","Samoa","San Marino","Sao Tome and Principe","Saudi Arabia","Senegal","Serbia","Seychelles","Sierra Leone","Singapore","Slovakia","Slovenia","Solomon Islands","Somalia","South Africa","South Sudan","Spain","Sri Lanka","Sudan","Suriname","Sweden","Switzerland","Syria","Taiwan","Tajikistan","Tanzania","Thailand","Timor-Leste","Togo","Tonga","Trinidad and Tobago","Tunisia","Turkey","Turkmenistan","Tuvalu","Uganda","Ukraine","United Arab Emirates","United Kingdom","United States","Uruguay","Uzbekistan","Vanuatu","Vatican City","Venezuela","Vietnam","Yemen","Zambia","Zimbabwe"];
    countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        countrySelect.appendChild(option);
    });
}

if (!window.showToast) {
    window.showToast = function(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) { 
            console.warn('Toast container not found.'); 
            return; 
        }
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => { 
            toast.remove(); 
        }, 3000);
    };
}
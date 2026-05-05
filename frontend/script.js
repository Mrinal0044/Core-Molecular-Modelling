const API_BASE_URL = 'http://localhost:8000/api';

document.addEventListener('DOMContentLoaded', () => {
    
    // --- Global State ---
    let currentUserEmail = null;

    // --- Toast Notifications ---
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // --- Auth View Toggles ---
    const authView = document.getElementById('auth-view');
    const mainAppView = document.getElementById('main-app-view');
    const signinForm = document.getElementById('signin-form');
    const signupForm = document.getElementById('signup-form');
    
    document.getElementById('link-to-signup').addEventListener('click', (e) => {
        e.preventDefault();
        signinForm.style.display = 'none';
        signupForm.style.display = 'block';
    });

    document.getElementById('link-to-signin').addEventListener('click', (e) => {
        e.preventDefault();
        signupForm.style.display = 'none';
        signinForm.style.display = 'block';
    });

    document.getElementById('btn-logout').addEventListener('click', () => {
        currentUserEmail = null;
        mainAppView.style.display = 'none';
        authView.style.display = 'block';
        signinForm.reset();
        document.getElementById('otp-group').style.display = 'none';
        document.getElementById('btn-verify-otp').style.display = 'none';
        document.getElementById('btn-send-otp').style.display = 'flex';
        showToast('Logged out successfully');
    });

    // --- Signup Logic ---
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = signupForm.querySelector('button[type="submit"]');
        btn.querySelector('.btn-text').textContent = 'Registering...';
        btn.style.pointerEvents = 'none';

        const formData = new FormData(signupForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch(`${API_BASE_URL}/signup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            
            if (response.ok) {
                showToast(result.message, 'success');
                signupForm.reset();
                document.getElementById('link-to-signin').click();
                document.getElementById('signin-email').value = data.email;
            } else {
                showToast(result.detail || 'Signup failed', 'error');
            }
        } catch (error) {
            showToast('Network error during signup', 'error');
        } finally {
            btn.querySelector('.btn-text').textContent = 'Register Account';
            btn.style.pointerEvents = 'all';
        }
    });

    // --- Sign In Logic ---
    const btnSendOtp = document.getElementById('btn-send-otp');
    const btnVerifyOtp = document.getElementById('btn-verify-otp');
    const otpGroup = document.getElementById('otp-group');

    btnSendOtp.addEventListener('click', async (e) => {
        e.preventDefault();

        const email = document.getElementById('signin-email').value;
        if (!email) {
            showToast('Please enter your registered email', 'error');
            return;
        }

        btnSendOtp.querySelector('.btn-text').textContent = 'Sending...';
        btnSendOtp.style.pointerEvents = 'none';

        try {
            const response = await fetch(`${API_BASE_URL}/request-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const result = await response.json();

            if (response.ok) {
                showToast('OTP sent to your email!', 'success');
                
                otpGroup.style.display = 'block'; 
                btnSendOtp.style.display = 'none';
                btnVerifyOtp.style.display = 'block'; 
                
                currentUserEmail = email; 
                document.getElementById('signin-otp').setAttribute('required', 'true');
                document.getElementById('signin-otp').focus();

            } else {
                showToast(result.detail || 'Failed to send OTP', 'error');
            }
        } catch (error) {
            showToast('Network error requesting OTP', 'error');
        } finally {
            btnSendOtp.querySelector('.btn-text').textContent = 'Send OTP';
            btnSendOtp.style.pointerEvents = 'all';
        }
    });

    signinForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const otp = document.getElementById('signin-otp').value;
        if (!otp) {
            showToast('Please enter the OTP', 'error');
            return;
        }

        btnVerifyOtp.querySelector('.btn-text').textContent = 'Verifying...';
        btnVerifyOtp.style.pointerEvents = 'none';

        try {
            const response = await fetch(`${API_BASE_URL}/verify-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: currentUserEmail, otp })
            });
            const result = await response.json();

            if (response.ok) {
                showToast('Login successful!', 'success');
                document.getElementById('user-greeting').textContent = `Welcome, ${result.user.name || 'Researcher'}`;
                authView.style.display = 'none';
                mainAppView.style.display = 'block';
            } else {
                showToast(result.detail || 'Invalid OTP', 'error');
            }
        } catch (error) {
            showToast('Network error verifying OTP', 'error');
        } finally {
            btnVerifyOtp.querySelector('.btn-text').textContent = 'Verify & Login';
            btnVerifyOtp.style.pointerEvents = 'all';
        }
    });

    // --- Dynamic Target Proteins Logic ---
    const proteinContainer = document.getElementById('protein-inputs-container');
    const btnAddProtein = document.getElementById('btn-add-protein');
    const summaryContainer = document.getElementById('protein-summary-container');
    const summaryText = document.getElementById('protein-summary-text');

    const updateSummary = () => {
        const inputs = document.querySelectorAll('.protein-input');
        const proteins = Array.from(inputs)
            .map(input => input.value.trim())
            .filter(val => val !== '');
        
        if (proteins.length > 0) {
            summaryContainer.style.display = 'block';
            summaryText.textContent = proteins.join(', ');
        } else {
            summaryContainer.style.display = 'none';
            summaryText.textContent = '';
        }
    };

    if (btnAddProtein && proteinContainer) {
        btnAddProtein.addEventListener('click', () => {
            const row = document.createElement('div');
            row.className = 'input-wrapper';
            row.style.cssText = 'display: flex; gap: 10px; margin-bottom: 10px; align-items: center;';
            
            row.innerHTML = `
                <input type="text" name="targetProteins[]" class="protein-input" placeholder="e.g., AMPL" style="flex: 1;">
                <button type="button" class="text-btn btn-remove" style="color: #ff4757; padding: 0;">Remove</button>
            `;
            
            proteinContainer.appendChild(row);
            
            row.querySelector('.protein-input').addEventListener('input', updateSummary);
            
            row.querySelector('.btn-remove').addEventListener('click', (e) => {
                e.target.parentElement.remove();
                updateSummary();
            });
        });
    }

    const initialInput = document.querySelector('.protein-input');
    if (initialInput) {
        initialInput.addEventListener('input', updateSummary);
    }

    // --- MD Simulation Toggle ---
    const mdSimulationToggle = document.getElementById('md-simulation');
    const mdSettingsGroup = document.getElementById('md-settings');

    if(mdSimulationToggle && mdSettingsGroup) {
        mdSimulationToggle.addEventListener('change', (e) => {
            if (e.target.checked) {
                mdSettingsGroup.classList.add('show');
            } else {
                mdSettingsGroup.classList.remove('show');
            }
        });
    }

    // --- Form Submission Handling ---
    const form = document.getElementById('pharmx-form');
    const submitBtn = form.querySelector('.submit-btn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if(!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const originalText = submitBtn.querySelector('.btn-text').textContent;
        submitBtn.querySelector('.btn-text').textContent = 'Initializing...';
        submitBtn.style.pointerEvents = 'none';
        
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // --- IMPORTANT: Capture multiple values into arrays ---
        data.capabilities = formData.getAll('capabilities');
        data.simulations = formData.getAll('simulations');
        
        // Capture all dynamic protein rows into an array
        data.targetProteins = formData.getAll('targetProteins[]');
        delete data['targetProteins[]']; // Cleanup the raw string key from Object.fromEntries

        try {
            const response = await fetch(`${API_BASE_URL}/submit-form`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: currentUserEmail, formData: data })
            });
            const result = await response.json();

            if (response.ok) {
                submitBtn.querySelector('.btn-text').textContent = 'Pipeline Ready!';
                submitBtn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                showToast('Pipeline initialized! Notifications sent.', 'success');
                
                setTimeout(() => {
                    submitBtn.querySelector('.btn-text').textContent = originalText;
                    submitBtn.style.background = '';
                    submitBtn.style.pointerEvents = 'all';
                }, 3000);
            } else {
                showToast(result.detail || 'Submission failed', 'error');
                submitBtn.querySelector('.btn-text').textContent = originalText;
                submitBtn.style.pointerEvents = 'all';
            }
        } catch (error) {
            showToast('Network error during submission', 'error');
            submitBtn.querySelector('.btn-text').textContent = originalText;
            submitBtn.style.pointerEvents = 'all';
        }
    });
});
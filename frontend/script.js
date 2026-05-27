// Detect if running on a dev server (like Live Server) or production/FastAPI
const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port !== '8000' 
    ? 'http://localhost:8000/api' 
    : '/api';

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

    // --- UI Routing & View Controls ---
    const containerEl = document.querySelector('.container');
    const landingView = document.getElementById('landing-view');
    const brandHeader = document.getElementById('brand-header');
    const authView = document.getElementById('auth-view');
    const mainAppView = document.getElementById('main-app-view');
    
    const signinForm = document.getElementById('signin-form');
    const signupForm = document.getElementById('signup-form');

    // Navigation functions
    function showLandingPage() {
        landingView.style.display = 'flex';
        authView.style.display = 'none';
        mainAppView.style.display = 'none';
        brandHeader.style.display = 'none';
        containerEl.className = 'container';
    }

    function showAuthPage() {
        landingView.style.display = 'none';
        authView.style.display = 'flex';
        mainAppView.style.display = 'none';
        brandHeader.style.display = 'block';
        containerEl.className = 'container auth-active';
        signinForm.style.display = 'block';
        signupForm.style.display = 'none';
    }

    function showMainAppPage(userName) {
        landingView.style.display = 'none';
        authView.style.display = 'none';
        mainAppView.style.display = 'block';
        brandHeader.style.display = 'none';
        containerEl.className = 'container app-active';
        document.getElementById('user-greeting').textContent = `Welcome, ${userName || 'Researcher'}`;
    }

    // Wiring up landing page CTA buttons
    document.getElementById('btn-explore').addEventListener('click', showAuthPage);
    document.getElementById('btn-request-demo').addEventListener('click', showAuthPage);

    // Navbar link controls
    document.getElementById('nav-home').addEventListener('click', (e) => {
        e.preventDefault();
        showLandingPage();
    });
    
    // Add brand logo return-to-home functionality
    document.querySelectorAll('.logo-container').forEach(logo => {
        logo.addEventListener('click', () => {
            showLandingPage();
        });
        logo.style.cursor = 'pointer';
    });

    const placeholderNavToast = (e) => {
        e.preventDefault();
        showToast('Section coming soon. Explore the platform to access features!', 'success');
    };
    document.getElementById('nav-features').addEventListener('click', placeholderNavToast);
    document.getElementById('nav-about').addEventListener('click', placeholderNavToast);
    document.getElementById('nav-contact').addEventListener('click', placeholderNavToast);

    // Form switches
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
        signinForm.reset();
        document.getElementById('otp-group').style.display = 'none';
        document.getElementById('btn-verify-otp').style.display = 'none';
        document.getElementById('btn-send-otp').style.display = 'flex';
        showToast('Logged out successfully');
        showLandingPage();
    });

    // --- Watch Demo Modal Controller ---
    const demoModal = document.getElementById('demo-modal');
    const demoVideoIframe = document.getElementById('demo-video-iframe');
    const btnWatchDemo = document.getElementById('btn-watch-demo');
    const btnCloseModal = document.getElementById('btn-close-modal');

    function openDemoModal() {
        // Embed Google Drive preview with autoplay enabled
        demoVideoIframe.src = "https://drive.google.com/file/d/1VaZBZGNlN98Ezij-Ndrp01UeAJEcyxuG/preview?autoplay=1";
        demoModal.classList.add('active');
    }

    function closeDemoModal() {
        demoModal.classList.remove('active');
        // Stop playing by clearing the iframe src
        demoVideoIframe.src = "";
    }

    if (btnWatchDemo) btnWatchDemo.addEventListener('click', openDemoModal);
    if (btnCloseModal) btnCloseModal.addEventListener('click', closeDemoModal);
    
    // Close modal if clicked on the overlay background
    demoModal.addEventListener('click', (e) => {
        if (e.target === demoModal) {
            closeDemoModal();
        }
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
    const linkResendOtp = document.getElementById('link-resend-otp');

    let otpCooldown = false;
    let otpTimerInterval = null;

    function startOtpTimer() {
        const timerSpan = document.getElementById('otp-timer');
        let timeLeft = 30;
        otpCooldown = true;
        
        if(linkResendOtp) linkResendOtp.style.display = 'none';
        if(timerSpan) {
            timerSpan.style.display = 'inline';
            timerSpan.textContent = `(${timeLeft}s)`;
        }
        
        if(otpTimerInterval) clearInterval(otpTimerInterval);
        
        otpTimerInterval = setInterval(() => {
            timeLeft--;
            if(timerSpan) timerSpan.textContent = `(${timeLeft}s)`;
            
            if (timeLeft <= 0) {
                clearInterval(otpTimerInterval);
                otpCooldown = false;
                if(timerSpan) timerSpan.style.display = 'none';
                if(linkResendOtp) linkResendOtp.style.display = 'inline';
            }
        }, 1000);
    }

    const requestOtp = async (email, isResend = false) => {
        if (otpCooldown) return;

        const btn = isResend ? linkResendOtp : btnSendOtp;
        const originalText = isResend ? 'Resend OTP' : 'Send OTP';
        
        if (!isResend) {
            btn.querySelector('.btn-text').textContent = 'Sending...';
            btn.style.pointerEvents = 'none';
        } else {
            btn.textContent = 'Sending...';
            btn.style.pointerEvents = 'none';
            btn.style.color = '#94a3b8'; // grey out link
        }

        try {
            const response = await fetch(`${API_BASE_URL}/request-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const result = await response.json();

            if (response.ok) {
                showToast(isResend ? 'OTP resent to your email!' : 'OTP sent to your email!', 'success');
                
                if (!isResend) {
                    otpGroup.style.display = 'block'; 
                    btnSendOtp.style.display = 'none';
                    btnVerifyOtp.style.display = 'block'; 
                    
                    currentUserEmail = email; 
                    document.getElementById('signin-otp').setAttribute('required', 'true');
                    document.getElementById('signin-otp').focus();
                }
                
                startOtpTimer();
            } else {
                showToast(result.detail || 'Failed to send OTP', 'error');
            }
        } catch (error) {
            showToast('Network error requesting OTP', 'error');
        } finally {
            if (!isResend) {
                btn.querySelector('.btn-text').textContent = originalText;
                btn.style.pointerEvents = 'all';
            } else {
                btn.textContent = originalText;
                btn.style.pointerEvents = 'all';
                btn.style.color = ''; // reset link color
            }
        }
    };

    btnSendOtp.addEventListener('click', (e) => {
        e.preventDefault();
        const email = document.getElementById('signin-email').value;
        if (!email) {
            showToast('Please enter your registered email', 'error');
            return;
        }
        requestOtp(email, false);
    });

    if (linkResendOtp) {
        linkResendOtp.addEventListener('click', (e) => {
            e.preventDefault();
            if (currentUserEmail) {
                requestOtp(currentUserEmail, true);
            }
        });
    }

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
                showMainAppPage(result.user.name);
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

    // --- Dynamic Molecules Logic ---
    const moleculeContainer = document.getElementById('molecule-inputs-container');
    const btnAddMolecule = document.getElementById('btn-add-molecule');
    const moleculeSummaryContainer = document.getElementById('molecule-summary-container');
    const moleculeSummaryText = document.getElementById('molecule-summary-text');

    const updateMoleculeSummary = () => {
        const inputs = document.querySelectorAll('.molecule-input');
        const molecules = Array.from(inputs)
            .map(input => input.value.trim())
            .filter(val => val !== '');
        
        if (molecules.length > 0) {
            moleculeSummaryContainer.style.display = 'block';
            moleculeSummaryText.textContent = molecules.join(', ');
        } else {
            moleculeSummaryContainer.style.display = 'none';
            moleculeSummaryText.textContent = '';
        }
    };

    if (btnAddMolecule && moleculeContainer) {
        btnAddMolecule.addEventListener('click', () => {
            const row = document.createElement('div');
            row.className = 'input-wrapper';
            row.style.cssText = 'display: flex; gap: 10px; margin-bottom: 10px; align-items: center;';
            
            row.innerHTML = `
                <input type="text" name="molecules[]" class="molecule-input" placeholder="e.g., Aspirin" style="flex: 1;">
                <button type="button" class="text-btn btn-remove" style="color: #ff4757; padding: 0;">Remove</button>
            `;
            
            moleculeContainer.appendChild(row);
            
            row.querySelector('.molecule-input').addEventListener('input', updateMoleculeSummary);
            
            row.querySelector('.btn-remove').addEventListener('click', (e) => {
                e.target.parentElement.remove();
                updateMoleculeSummary();
            });
        });
    }

    const initialMoleculeInput = document.querySelector('.molecule-input');
    if (initialMoleculeInput) {
        initialMoleculeInput.addEventListener('input', updateMoleculeSummary);
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
        
        // Capture all dynamic rows into arrays
        data.molecules = formData.getAll('molecules[]');
        delete data['molecules[]'];

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
                submitBtn.querySelector('.btn-text').textContent = 'Sent';
                submitBtn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                submitBtn.style.pointerEvents = 'none';
                showToast('Pipeline initialized! Notifications sent.', 'success');
                // The button intentionally remains in the 'Sent' state and disabled
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
import { API_BASE_URL, globalState } from './config.js';
import { showToast } from './utils.js';
import { showLandingPage, showMainAppPage, signupForm, signinForm } from './ui.js';

export function setupAuth() {
    if (signupForm) {
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
    }

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
            btn.style.color = '#94a3b8';
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
                    if(otpGroup) otpGroup.style.display = 'block'; 
                    if(btnSendOtp) btnSendOtp.style.display = 'none';
                    if(btnVerifyOtp) btnVerifyOtp.style.display = 'block'; 
                    
                    globalState.currentUserEmail = email; 
                    const otpInput = document.getElementById('signin-otp');
                    if(otpInput) {
                        otpInput.setAttribute('required', 'true');
                        otpInput.focus();
                    }
                }
                
                startOtpTimer();
            } else {
                showToast(result.detail || 'Failed to send OTP', 'error');
            }
        } catch (error) {
            showToast('Network error requesting OTP', 'error');
        } finally {
            if (!isResend) {
                if(btn) {
                    const btnText = btn.querySelector('.btn-text');
                    if(btnText) btnText.textContent = originalText;
                    btn.style.pointerEvents = 'all';
                }
            } else {
                if(btn) {
                    btn.textContent = originalText;
                    btn.style.pointerEvents = 'all';
                    btn.style.color = ''; 
                }
            }
        }
    };

    if (btnSendOtp) {
        btnSendOtp.addEventListener('click', (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('signin-email');
            if(emailInput) {
                const email = emailInput.value;
                if (!email) {
                    showToast('Please enter your registered email', 'error');
                    return;
                }
                requestOtp(email, false);
            }
        });
    }

    if (linkResendOtp) {
        linkResendOtp.addEventListener('click', (e) => {
            e.preventDefault();
            if (globalState.currentUserEmail) {
                requestOtp(globalState.currentUserEmail, true);
            }
        });
    }

    if (signinForm) {
        signinForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const otpInput = document.getElementById('signin-otp');
            const otp = otpInput ? otpInput.value : '';
            if (!otp) {
                showToast('Please enter the OTP', 'error');
                return;
            }

            if(btnVerifyOtp) {
                const btnText = btnVerifyOtp.querySelector('.btn-text');
                if(btnText) btnText.textContent = 'Verifying...';
                btnVerifyOtp.style.pointerEvents = 'none';
            }

            try {
                const response = await fetch(`${API_BASE_URL}/verify-otp`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: globalState.currentUserEmail, otp })
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
                if(btnVerifyOtp) {
                    const btnText = btnVerifyOtp.querySelector('.btn-text');
                    if(btnText) btnText.textContent = 'Verify & Login';
                    btnVerifyOtp.style.pointerEvents = 'all';
                }
            }
        });
    }

    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            globalState.currentUserEmail = null;
            if(signinForm) signinForm.reset();
            
            if(otpGroup) otpGroup.style.display = 'none';
            if(btnVerifyOtp) btnVerifyOtp.style.display = 'none';
            if(btnSendOtp) btnSendOtp.style.display = 'flex';
            
            showToast('Logged out successfully');
            showLandingPage();
        });
    }
}

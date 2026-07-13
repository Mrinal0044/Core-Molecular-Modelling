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
                submitBtn.querySelector('.btn-text').textContent = 'Processing...';
                submitBtn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                submitBtn.style.pointerEvents = 'none';
                showToast('Pipeline initialized! Polling for results...', 'success');
                
                // Poll ALL jobs, not just the first one
                if (result.job_ids && result.job_ids.length > 0) {
                    let completedCount = 0;
                    const totalJobs = result.job_ids.length;
                    submitBtn.querySelector('.btn-text').textContent = `Processing 0/${totalJobs}...`;
                    
                    result.job_ids.forEach((jobId) => {
                        pollJobStatus(jobId, () => {
                            completedCount++;
                            if (completedCount >= totalJobs) {
                                submitBtn.querySelector('.btn-text').textContent = `Completed (${totalJobs}/${totalJobs})`;
                            } else {
                                submitBtn.querySelector('.btn-text').textContent = `Processing ${completedCount}/${totalJobs}...`;
                            }
                        });
                    });
                }
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

    async function pollJobStatus(jobId, onComplete) {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/job-status/${jobId}`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.status === 'Completed' || data.status === 'Failed') {
                        clearInterval(interval);
                        
                        if (data.result_data) {
                            console.log('Job Result:', data.result_data);
                            const r = data.result_data;
                            
                            // Show the results view
                            const resultsView = document.getElementById('results-view');
                            if (resultsView) resultsView.style.display = 'block';
                            
                            const container = document.getElementById('results-container');
                            const card = document.createElement('div');
                            card.style.cssText = 'background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; gap: 0.75rem;';
                            
                            const molLabel = r.molecule || 'Unknown Ligand';
                            const targetLabel = r.target || 'Unknown Target';
                            const iupacName = r.pubchem_data?.iupac_name || '';
                            
                            let html = `
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <h4 style="color: #4facfe; margin: 0 0 0.25rem 0; font-size: 1.1rem;">🧬 ${iupacName || molLabel}</h4>
                                        ${iupacName ? `<span style="font-size: 0.75rem; opacity: 0.5; font-family: monospace;">${molLabel}</span><br>` : ''}
                                        <span style="font-size: 0.8rem; opacity: 0.6;">Target: <strong style="color: #00f2fe;">${targetLabel}</strong> · Job: ${jobId.substring(0,8)}</span>
                                    </div>
                                    <span style="background: ${data.status === 'Completed' ? 'rgba(16,185,129,0.2)' : 'rgba(255,71,87,0.2)'}; color: ${data.status === 'Completed' ? '#10b981' : '#ff4757'}; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">${data.status}</span>
                                </div>
                                
                                <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">`;
                            
                            // RDKit Docking Score
                            if (r.binding_affinity !== undefined) {
                                html += `
                                    <div style="flex: 1; min-width: 150px; background: rgba(16,185,129,0.08); padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid rgba(16,185,129,0.25);">
                                        <span style="font-size: 0.7rem; opacity: 0.7; display: block; margin-bottom: 4px;">⚡ Docking Score</span>
                                        <strong style="color: #10b981; font-size: 1.4rem;">${r.binding_affinity}</strong>
                                        <span style="font-size: 0.75rem; opacity: 0.6;"> kcal/mol</span>
                                        ${r.scoring_method ? `<div style="font-size: 0.65rem; opacity: 0.4; margin-top: 2px;">${r.scoring_method}</div>` : ''}
                                    </div>`;
                            }
                            
                            // PubChem Affinity Prediction
                            if (r.pubchem_affinity !== undefined) {
                                html += `
                                    <div style="flex: 1; min-width: 150px; background: rgba(0,242,254,0.08); padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid rgba(0,242,254,0.25);">
                                        <span style="font-size: 0.7rem; opacity: 0.7; display: block; margin-bottom: 4px;">🔬 PubChem Prediction</span>
                                        <strong style="color: #00f2fe; font-size: 1.4rem;">${r.pubchem_affinity}</strong>
                                        <span style="font-size: 0.75rem; opacity: 0.6;"> kcal/mol</span>
                                    </div>`;
                            }
                            
                            // Confidence
                            if (r.prediction_confidence !== undefined) {
                                const pct = Math.round(r.prediction_confidence * 100);
                                const confColor = pct >= 80 ? '#10b981' : pct >= 50 ? '#f59e0b' : '#ff4757';
                                html += `
                                    <div style="flex: 1; min-width: 120px; background: rgba(79,172,254,0.08); padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid rgba(79,172,254,0.25);">
                                        <span style="font-size: 0.7rem; opacity: 0.7; display: block; margin-bottom: 4px;">📊 Confidence</span>
                                        <strong style="color: ${confColor}; font-size: 1.4rem;">${pct}%</strong>
                                    </div>`;
                            }
                            
                            // Drug-likeness badge
                            if (r.pubchem_data?.druglike !== undefined) {
                                const isDrug = r.pubchem_data.druglike;
                                html += `
                                    <div style="flex: 1; min-width: 120px; background: rgba(${isDrug ? '16,185,129' : '255,71,87'},0.08); padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid rgba(${isDrug ? '16,185,129' : '255,71,87'},0.25);">
                                        <span style="font-size: 0.7rem; opacity: 0.7; display: block; margin-bottom: 4px;">💊 Drug-Likeness</span>
                                        <strong style="color: ${isDrug ? '#10b981' : '#ff4757'}; font-size: 1.1rem;">${isDrug ? 'PASS' : 'FAIL'}</strong>
                                        <div style="font-size: 0.65rem; opacity: 0.5; margin-top: 2px;">Lipinski: ${r.pubchem_data.lipinski_violations || 0} violations</div>
                                    </div>`;
                            }
                            
                            html += `</div>`;
                            
                            // Molecular Properties Row (from PubChem + RDKit)
                            const desc = r.descriptors || r.pubchem_data;
                            if (desc) {
                                html += `
                                <div style="display: flex; gap: 0.75rem; flex-wrap: wrap; padding: 0.75rem; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
                                    <span style="font-size: 0.7rem; opacity: 0.5; width: 100%; margin-bottom: 2px;">Molecular Properties</span>`;
                                
                                const props = [
                                    { label: 'MW', value: desc.molecular_weight, unit: 'g/mol' },
                                    { label: 'LogP', value: desc.logp, unit: '' },
                                    { label: 'HBD', value: desc.hbd, unit: '' },
                                    { label: 'HBA', value: desc.hba, unit: '' },
                                    { label: 'TPSA', value: desc.tpsa, unit: 'Å²' },
                                    { label: 'Rot. Bonds', value: desc.rotatable_bonds, unit: '' },
                                ];
                                
                                props.forEach(p => {
                                    if (p.value !== undefined && p.value !== null) {
                                        html += `<div style="text-align: center; min-width: 60px;">
                                            <div style="font-size: 0.65rem; opacity: 0.5;">${p.label}</div>
                                            <div style="color: #e2e8f0; font-size: 0.9rem; font-weight: 600;">${p.value}</div>
                                            ${p.unit ? `<div style="font-size: 0.55rem; opacity: 0.4;">${p.unit}</div>` : ''}
                                        </div>`;
                                    }
                                });
                                html += `</div>`;
                            }
                            
                            // Bioactivity (from PubChem)
                            if (r.pubchem_data?.total_assays) {
                                const bio = r.pubchem_data;
                                html += `
                                <div style="display: flex; gap: 0.75rem; align-items: center; padding: 0.5rem 0.75rem; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
                                    <span style="font-size: 0.7rem; opacity: 0.5;">PubChem Bioactivity:</span>
                                    <span style="color: #10b981; font-size: 0.85rem; font-weight: 600;">${bio.active_assays} active</span>
                                    <span style="opacity: 0.4; font-size: 0.8rem;">/ ${bio.total_assays} assays tested</span>
                                    ${bio.pubchem_cid ? `<a href="https://pubchem.ncbi.nlm.nih.gov/compound/${bio.pubchem_cid}" target="_blank" style="color: #4facfe; font-size: 0.75rem; margin-left: auto; text-decoration: none;">View on PubChem ↗</a>` : ''}
                                </div>`;
                            }
                            
                            // Error
                            if (r.error) {
                                html += `<div style="color: #ff4757; font-size: 0.85rem;">Error: ${r.error}</div>`;
                            }
                            
                            card.innerHTML = html;
                            if (container) container.appendChild(card);
                        }
                        
                        if (data.status === 'Completed') {
                            showToast(`Job completed for ${data.result_data?.molecule || 'molecule'}!`, 'success');
                        } else {
                            showToast(`Job failed: ${data.result_data?.error || 'unknown error'}`, 'error');
                        }
                        
                        if (onComplete) onComplete();
                    }
                }
            } catch (err) {
                console.error("Polling error", err);
            }
        }, 3000);
    }
});
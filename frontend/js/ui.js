import { showToast } from './utils.js';

export const containerEl = document.querySelector('.container');
export const landingView = document.getElementById('landing-view');
export const brandHeader = document.getElementById('brand-header');
export const authView = document.getElementById('auth-view');
export const mainAppView = document.getElementById('main-app-view');
export const signinForm = document.getElementById('signin-form');
export const signupForm = document.getElementById('signup-form');

export function showLandingPage() {
    landingView.style.display = 'flex';
    authView.style.display = 'none';
    mainAppView.style.display = 'none';
    brandHeader.style.display = 'none';
    containerEl.className = 'container';
}

export function showAuthPage() {
    landingView.style.display = 'none';
    authView.style.display = 'flex';
    mainAppView.style.display = 'none';
    brandHeader.style.display = 'block';
    containerEl.className = 'container auth-active';
    signinForm.style.display = 'block';
    signupForm.style.display = 'none';
}

export function showMainAppPage(userName) {
    landingView.style.display = 'none';
    authView.style.display = 'none';
    mainAppView.style.display = 'block';
    brandHeader.style.display = 'none';
    containerEl.className = 'container app-active';
    document.getElementById('user-greeting').textContent = `Welcome, ${userName || 'Researcher'}`;
}

export function setupUIControls() {
    const btnExplore = document.getElementById('btn-explore');
    const btnRequestDemo = document.getElementById('btn-request-demo');
    if (btnExplore) btnExplore.addEventListener('click', showAuthPage);
    if (btnRequestDemo) btnRequestDemo.addEventListener('click', showAuthPage);

    const navHome = document.getElementById('nav-home');
    if (navHome) navHome.addEventListener('click', (e) => {
        e.preventDefault();
        showLandingPage();
    });
    
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
    
    const navFeatures = document.getElementById('nav-features');
    const navAbout = document.getElementById('nav-about');
    const navContact = document.getElementById('nav-contact');
    
    if(navFeatures) navFeatures.addEventListener('click', placeholderNavToast);
    if(navAbout) navAbout.addEventListener('click', placeholderNavToast);
    if(navContact) navContact.addEventListener('click', placeholderNavToast);

    const linkSignup = document.getElementById('link-to-signup');
    const linkSignin = document.getElementById('link-to-signin');
    if(linkSignup) linkSignup.addEventListener('click', (e) => {
        e.preventDefault();
        signinForm.style.display = 'none';
        signupForm.style.display = 'block';
    });

    if(linkSignin) linkSignin.addEventListener('click', (e) => {
        e.preventDefault();
        signupForm.style.display = 'none';
        signinForm.style.display = 'block';
    });
}

export function setupDemoModal() {
    const demoModal = document.getElementById('demo-modal');
    const demoVideoIframe = document.getElementById('demo-video-iframe');
    const btnWatchDemo = document.getElementById('btn-watch-demo');
    const btnCloseModal = document.getElementById('btn-close-modal');

    function openDemoModal() {
        if(demoVideoIframe) demoVideoIframe.src = "https://drive.google.com/file/d/1VaZBZGNlN98Ezij-Ndrp01UeAJEcyxuG/preview?autoplay=1";
        if(demoModal) demoModal.classList.add('active');
    }

    function closeDemoModal() {
        if(demoModal) demoModal.classList.remove('active');
        if(demoVideoIframe) demoVideoIframe.src = "";
    }

    if (btnWatchDemo) btnWatchDemo.addEventListener('click', openDemoModal);
    if (btnCloseModal) btnCloseModal.addEventListener('click', closeDemoModal);
    
    if (demoModal) {
        demoModal.addEventListener('click', (e) => {
            if (e.target === demoModal) {
                closeDemoModal();
            }
        });
    }
}

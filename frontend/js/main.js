import { setupUIControls, setupDemoModal } from './ui.js';
import { setupAuth } from './auth.js';
import { setupForm } from './form.js';
import { setupDashboardControls } from './dashboard.js';

document.addEventListener('DOMContentLoaded', () => {
    setupUIControls();
    setupDemoModal();
    setupAuth();
    setupForm();
    setupDashboardControls();
});

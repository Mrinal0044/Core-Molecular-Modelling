import { API_BASE_URL, globalState } from './config.js';
import { showToast } from './utils.js';
import { renderDashboardCharts } from './dashboard.js';

export function setupForm() {
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
            if(summaryContainer) summaryContainer.style.display = 'block';
            if(summaryText) summaryText.textContent = proteins.join(', ');
        } else {
            if(summaryContainer) summaryContainer.style.display = 'none';
            if(summaryText) summaryText.textContent = '';
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
            if(moleculeSummaryContainer) moleculeSummaryContainer.style.display = 'block';
            if(moleculeSummaryText) moleculeSummaryText.textContent = molecules.join(', ');
        } else {
            if(moleculeSummaryContainer) moleculeSummaryContainer.style.display = 'none';
            if(moleculeSummaryText) moleculeSummaryText.textContent = '';
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

    const form = document.getElementById('pharmx-form');
    
    if (form) {
        const submitBtn = form.querySelector('.submit-btn');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            if(!form.checkValidity()) {
                form.reportValidity();
                return;
            }

            const btnText = submitBtn.querySelector('.btn-text');
            const originalText = btnText ? btnText.textContent : 'Submit';
            if(btnText) btnText.textContent = 'Initializing...';
            submitBtn.style.pointerEvents = 'none';
            
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            data.capabilities = formData.getAll('capabilities');
            data.simulations = formData.getAll('simulations');
            
            data.molecules = formData.getAll('molecules[]');
            delete data['molecules[]'];

            data.targetProteins = formData.getAll('targetProteins[]');
            delete data['targetProteins[]'];

            try {
                const response = await fetch(`${API_BASE_URL}/submit-form`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: globalState.currentUserEmail, formData: data })
                });
                const result = await response.json();

                if (response.ok) {
                    showToast('Pipeline initialized! Analysis complete.', 'success');
                    
                    document.getElementById('main-app-view').style.display = 'none';
                    document.getElementById('results-view').style.display = 'block';
                    
                    renderDashboardCharts(data);
                } else {
                    showToast(result.detail || 'Submission failed', 'error');
                    if(btnText) btnText.textContent = originalText;
                    submitBtn.style.pointerEvents = 'all';
                }
            } catch (error) {
                showToast('Network error during submission', 'error');
                if(btnText) btnText.textContent = originalText;
                submitBtn.style.pointerEvents = 'all';
            }
        });
    }
}

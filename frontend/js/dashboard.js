export function renderDashboardCharts(formData) {
    const capabilities = formData.capabilities || [];
    
    // Toggle Card Visibility
    const cardDocking = document.getElementById('card-docking');
    const cardAdme = document.getElementById('card-adme');
    const cardSynergy = document.getElementById('card-synergy');
    const cardNetwork = document.getElementById('card-network');
    const chartDoseResponse = document.getElementById('chart-dose-response');

    if (cardDocking) {
        if (capabilities.includes('molecular_docking') || capabilities.includes('binding_affinity') || capabilities.includes('ic50_computation') || capabilities.includes('dose_response')) {
            cardDocking.style.display = 'flex';
        } else {
            cardDocking.style.display = 'none';
        }
    }

    if (chartDoseResponse) {
        if (capabilities.includes('dose_response')) {
            chartDoseResponse.style.display = 'block';
        } else {
            chartDoseResponse.style.display = 'none';
        }
    }

    if (cardAdme) {
        if (capabilities.includes('adme_toxicity')) {
            cardAdme.style.display = 'flex';
        } else {
            cardAdme.style.display = 'none';
        }
    }

    if (cardSynergy) {
        if (capabilities.includes('synergy_heatmaps')) {
            cardSynergy.style.display = 'flex';
        } else {
            cardSynergy.style.display = 'none';
        }
    }

    if (cardNetwork) {
        if (capabilities.includes('receptor_network')) {
            cardNetwork.style.display = 'flex';
        } else {
            cardNetwork.style.display = 'none';
        }
    }

    // Render logic (only if the element is visible and Plotly is loaded)
    if (capabilities.includes('dose_response') && document.getElementById('chart-dose-response') && window.Plotly) {
        const xData = [-9, -8, -7, -6, -5, -4];
        const yData = [5, 10, 45, 80, 95, 100];
        const trace1 = {
            x: xData,
            y: yData,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#00f2fe', width: 3, shape: 'spline' },
            marker: { color: '#00f2fe', size: 8 }
        };
        const layout1 = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { l: 30, r: 10, t: 10, b: 30 },
            xaxis: { title: 'Log Conc.', color: '#94a3b8', gridcolor: 'rgba(255,255,255,0.05)', titlefont: {size: 10}, tickfont: {size: 9} },
            yaxis: { title: 'Inhibition (%)', color: '#94a3b8', gridcolor: 'rgba(255,255,255,0.05)', titlefont: {size: 10}, tickfont: {size: 9} },
            height: 200
        };
        Plotly.newPlot('chart-dose-response', [trace1], layout1, {displayModeBar: false, responsive: true});
    }

    if (capabilities.includes('synergy_heatmaps') && document.getElementById('chart-synergy-heatmap') && window.Plotly) {
        const zValues = [
            [0, 5, 12, 18, 22],
            [4, 15, 30, 45, 55],
            [10, 25, 60, 75, 85],
            [15, 35, 70, 90, 95],
            [20, 40, 80, 95, 98]
        ];
        const trace2 = {
            z: zValues,
            type: 'heatmap',
            colorscale: [
                [0, 'rgba(3, 6, 18, 0)'],
                [0.5, '#1e40af'],
                [1, '#00f2fe']
            ],
            showscale: true,
            colorbar: { tickfont: { color: '#94a3b8' } }
        };
        const layout2 = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { l: 40, r: 20, t: 20, b: 40 },
            xaxis: { title: 'Drug A Concentration', color: '#94a3b8', gridcolor: 'transparent' },
            yaxis: { title: 'Drug B Concentration', color: '#94a3b8', gridcolor: 'transparent' },
        };
        Plotly.newPlot('chart-synergy-heatmap', [trace2], layout2, {displayModeBar: false, responsive: true});
    }

    if (capabilities.includes('receptor_network') && document.getElementById('chart-interaction-network') && window.Plotly) {
        const traceNodes = {
            x: [1, 2, 2.5, 3, 4, 1.5, 3.5],
            y: [2, 3, 1.5, 3.5, 2, 1, 1],
            mode: 'markers+text',
            type: 'scatter',
            text: ['Target', 'EGFR', 'BRAF', 'MEK', 'ERK', 'PI3K', 'AKT'],
            textposition: 'top center',
            textfont: { color: '#e2e8f0', size: 12 },
            marker: { size: [30, 20, 20, 20, 20, 20, 20], color: ['#00f2fe', '#1e40af', '#1e40af', '#1e40af', '#1e40af', '#10b981', '#10b981'] }
        };
        
        const traceEdges = {
            x: [1, 2, null, 1, 2.5, null, 2, 3, null, 3, 4, null, 1, 1.5, null, 1.5, 3.5],
            y: [2, 3, null, 2, 1.5, null, 3, 3.5, null, 3.5, 2, null, 2, 1, null, 1, 1],
            mode: 'lines',
            type: 'scatter',
            line: { color: 'rgba(0, 242, 254, 0.3)', width: 2 },
            hoverinfo: 'none'
        };

        const layout3 = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { l: 10, r: 10, t: 20, b: 10 },
            xaxis: { showgrid: false, zeroline: false, showticklabels: false },
            yaxis: { showgrid: false, zeroline: false, showticklabels: false },
            showlegend: false
        };
        Plotly.newPlot('chart-interaction-network', [traceEdges, traceNodes], layout3, {displayModeBar: false, responsive: true});
    }
}

export function setupDashboardControls() {
    const btnBackToForm = document.getElementById('btn-back-to-form');
    if (btnBackToForm) {
        btnBackToForm.addEventListener('click', () => {
            document.getElementById('results-view').style.display = 'none';
            document.getElementById('main-app-view').style.display = 'block';
            const form = document.getElementById('pharmx-form');
            if(form) {
                const submitBtn = form.querySelector('.submit-btn');
                if(submitBtn) {
                    const btnText = submitBtn.querySelector('.btn-text');
                    if(btnText) btnText.textContent = 'Initialize Quantum Pipeline';
                    submitBtn.style.pointerEvents = 'all';
                }
            }
        });
    }
}

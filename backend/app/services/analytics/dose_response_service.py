import io
import base64
import numpy as np
import threading
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from backend.app.services.analytics.math_models import fit_4pl, hill_4pl
from backend.app.services.analytics.demo_data import generate_concentration_series

_matplotlib_lock = threading.Lock()

class DoseResponseService:
    @staticmethod
    def generate_demo_plot(ligand_name: str, target_name: str, true_ic50: float = 0.05) -> dict:
        """
        Generates synthetic dose-response data based on a true IC50,
        fits a 4PL curve to it, and generates a base64 plot.
        Returns a dict containing the fitted IC50 and the base64 image.
        """
        # Generate synthetic concentrations (μM)
        concentrations = generate_concentration_series(true_ic50, 10, 2)
        
        # Generate synthetic responses (inhibition %) with some noise
        # using the hill_4pl model: hill_4pl(x, E0, Emax, EC50, h)
        E0 = 0.0
        Emax = 100.0
        h = 1.2
        true_responses = hill_4pl(np.array(concentrations), E0, Emax, true_ic50, h)
        noise = np.random.normal(0, 5.0, len(concentrations)) # 5% noise
        observed_responses = np.clip(true_responses + noise, 0, 100)

        # Fit the model
        params = fit_4pl(concentrations, observed_responses)
        fitted_ic50 = params["EC50"]
        
        # Plotting
        with _matplotlib_lock:
            fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")
            
            # Plot the fitted curve
            smooth_conc = np.logspace(np.log10(min(concentrations)/2), np.log10(max(concentrations)*2), 100)
            smooth_resp = hill_4pl(smooth_conc, params["E0"], params["Emax"], fitted_ic50, params["h"])
            
            ax.semilogx(smooth_conc, smooth_resp, color='blue', linewidth=2.5, label='Fitted 4PL Curve')
            
            # Plot the points
            ax.scatter(concentrations, observed_responses, color='red', s=40, zorder=3, label='Observed Data')
            
            # Highlight IC50
            y_ic50 = hill_4pl(fitted_ic50, params["E0"], params["Emax"], fitted_ic50, params["h"])
            ax.plot(fitted_ic50, y_ic50, 'o', markersize=10, markerfacecolor='none', markeredgecolor='green', markeredgewidth=2, label=f"IC50 = {fitted_ic50:.3g} µM")
            ax.vlines(fitted_ic50, 0, y_ic50, colors='green', linestyles='--', linewidth=1.5)

            title = f"Dose-Response: {ligand_name}"
            if target_name:
                title += f" against {target_name}"
            ax.set_title(title, fontsize=14, weight='bold')
            ax.set_xlabel("Concentration (µM)", fontsize=12)
            ax.set_ylabel("Inhibition (%)", fontsize=12)
            ax.set_ylim(-5, 105)
            ax.grid(True, which='both', linestyle=':', alpha=0.5)
            ax.legend(loc='best')
            
            fig.tight_layout()
            
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=120)
            plt.close(fig)
            buf.seek(0)
            b64_image = base64.b64encode(buf.read()).decode("utf-8")
            
        return {
            "ic50_um": fitted_ic50,
            "plot_base64": b64_image
        }

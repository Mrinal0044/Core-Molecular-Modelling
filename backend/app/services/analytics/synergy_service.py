import io
import base64
import numpy as np
import pandas as pd
import threading
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from backend.app.services.analytics.math_models import compute_all_synergy
from backend.app.services.analytics.demo_data import generate_concentration_series, generate_demo

_matplotlib_lock = threading.Lock()

class SynergyService:
    @staticmethod
    def generate_demo_synergy(ligand_a: str, ligand_b: str, target_name: str, ic50_a: float, ic50_b: float) -> dict:
        """
        Generates synthetic checkerboard data (assuming some ZIP synergy)
        and computes true Bliss, Loewe, ZIP scores using the robust models.
        Returns the metrics and the base64 heatmap.
        """
        # Generate concentration series based on IC50s (6x6 matrix)
        conc_a = generate_concentration_series(ic50_a, 6, 2)
        conc_b = generate_concentration_series(ic50_b, 6, 2)
        
        # Generate synthetic checkerboard responses using a 'strong' synergy mode
        d1, d2, E = generate_demo('strong', conc_a, conc_b)
        
        # Add some noise to make it look realistic
        noise = np.random.normal(0, 3.0, len(E))
        E = np.clip(E + noise, 0, 100)
        
        # Compute real synergy scores using our robust models
        results = compute_all_synergy(d1, d2, E)
        
        # We'll plot the ZIP synergy score heatmap
        model_results = results.get("zip", results.get("bliss"))
        if not model_results:
            return None
            
        synergy_scores = model_results["synergy"]
        mean_synergy = model_results["mean"]
        
        # Reshape for heatmap
        df = pd.DataFrame({"d1": d1, "d2": d2, "synergy": synergy_scores})
        pivot = df.pivot_table(index="d1", columns="d2", values="synergy")
        pivot = pivot.sort_index(ascending=False)
        
        # Generate Heatmap
        with _matplotlib_lock:
            fig, ax = plt.subplots(figsize=(7, 6), facecolor="white")
            
            title = f"Synergy Map (ZIP Model)\nMean Score: {mean_synergy:.2f}"
            ax.set_title(title, fontsize=12, fontweight="bold", pad=12, color="#7c3aed")
            
            # Custom colormap: green(antagonistic) -> white(additive) -> red(synergistic)
            from matplotlib.colors import LinearSegmentedColormap
            colors_list = ["#d4edda", "#ffffff", "#f8d7da", "#dc3545", "#721c24"]
            cmap_synergy = LinearSegmentedColormap.from_list("synergy", colors_list, N=256)
            
            sns.heatmap(
                pivot, annot=True, fmt=".1f", cmap=cmap_synergy,
                center=0, vmin=-20, vmax=50,
                linewidths=0.5, linecolor="white",
                cbar_kws={"label": "Synergy Score", "shrink": 0.8},
                ax=ax, annot_kws={"fontsize": 9}
            )
            ax.set_xlabel(f"{ligand_b} (µM)", fontsize=10)
            ax.set_ylabel(f"{ligand_a} (µM)", fontsize=10)
            
            # Add target text
            if target_name:
                fig.text(0.5, 0.01, f"Target: {target_name}", ha="center", fontsize=9, color="gray")
                
            fig.tight_layout()
            
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            b64_image = base64.b64encode(buf.read()).decode("utf-8")
            
        return {
            "mean_score": mean_synergy,
            "max_score": model_results.get("max", 0),
            "heatmap_base64": b64_image
        }

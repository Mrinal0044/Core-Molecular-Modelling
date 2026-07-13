"""
Binding Affinity Prediction Service.
Uses PubChem REST API for real molecular data instead of DeepPurpose.
"""
import logging
from typing import Tuple, Dict, Any, Optional
from backend.app.services.pubchem_api import (
    get_compound_properties,
    get_cid_from_smiles,
    get_bioactivity_summary,
    compute_druglikeness_score
)

logger = logging.getLogger(__name__)


class BindingAffinityService:
    @staticmethod
    def predict(smiles: str, target_name: str) -> Tuple[float, float, Optional[Dict[str, Any]]]:
        """
        Predicts binding affinity using real PubChem data.
        Returns: (affinity_score, confidence, extra_data_dict)
        """
        print(f"[PREDICTION] Running PubChem-based prediction for '{smiles[:40]}...' vs '{target_name}'")

        extra_data = {}

        # 1. Fetch real molecular properties from PubChem
        properties = get_compound_properties(smiles)
        if properties:
            druglikeness = compute_druglikeness_score(properties)
            affinity = druglikeness["estimated_affinity_kcal"]
            extra_data["iupac_name"] = properties.get("IUPACName", "Unknown")
            extra_data["molecular_weight"] = properties.get("MolecularWeight")
            extra_data["logp"] = properties.get("XLogP")
            extra_data["hbd"] = properties.get("HBondDonorCount")
            extra_data["hba"] = properties.get("HBondAcceptorCount")
            extra_data["tpsa"] = properties.get("TPSA")
            extra_data["rotatable_bonds"] = properties.get("RotatableBondCount")
            extra_data["lipinski_violations"] = druglikeness["lipinski_violations"]
            extra_data["druglike"] = druglikeness["druglike"]

            # Confidence is higher when we have real PubChem data
            confidence = 0.75
            print(f"[PREDICTION] PubChem affinity estimate: {affinity} kcal/mol (Lipinski violations: {druglikeness['lipinski_violations']})")
        else:
            # Fallback: basic estimate
            affinity = -7.0
            confidence = 0.30
            print(f"[PREDICTION] PubChem lookup failed. Using default estimate.")

        # 2. Check for real bioactivity data
        cid = get_cid_from_smiles(smiles)
        if cid:
            extra_data["pubchem_cid"] = cid
            bio = get_bioactivity_summary(cid)
            if bio:
                extra_data["total_assays"] = bio["total_assays"]
                extra_data["active_assays"] = bio["active_assays"]
                extra_data["activity_ratio"] = bio["activity_ratio"]
                # If we have real bioactivity data, boost confidence
                if bio["total_assays"] > 0:
                    confidence = min(0.95, confidence + 0.15)

        return affinity, confidence, extra_data

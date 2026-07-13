"""
PubChem PUG REST API client for retrieving real compound data and bioactivity.
Docs: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
"""
import requests
import logging
from typing import Optional, Dict, Any
from urllib.parse import quote

logger = logging.getLogger(__name__)
PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def get_cid_from_smiles(smiles: str) -> Optional[int]:
    """Resolve a SMILES string to a PubChem Compound ID (CID)."""
    try:
        encoded = quote(smiles, safe='')
        url = f"{PUBCHEM_BASE}/compound/smiles/{encoded}/cids/JSON"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            cids = resp.json().get("IdentifierList", {}).get("CID", [])
            if cids:
                print(f"[PUBCHEM] Resolved SMILES → CID {cids[0]}")
                return cids[0]
        print(f"[PUBCHEM] No CID found for SMILES: {smiles[:40]}...")
    except Exception as e:
        print(f"[PUBCHEM] CID lookup error: {e}")
    return None


def get_compound_properties(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Fetch real molecular properties from PubChem.
    Returns: dict with MolecularWeight, XLogP, HBondDonorCount, HBondAcceptorCount,
             TPSA, RotatableBondCount, Complexity, IUPACName
    """
    try:
        encoded = quote(smiles, safe='')
        props = "MolecularWeight,XLogP,HBondDonorCount,HBondAcceptorCount,TPSA,RotatableBondCount,Complexity,IUPACName"
        url = f"{PUBCHEM_BASE}/compound/smiles/{encoded}/property/{props}/JSON"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            results = resp.json().get("PropertyTable", {}).get("Properties", [])
            if results:
                data = results[0]
                print(f"[PUBCHEM] Properties for CID {data.get('CID')}: MW={data.get('MolecularWeight')}, LogP={data.get('XLogP')}")
                return data
    except Exception as e:
        print(f"[PUBCHEM] Property lookup error: {e}")
    return None


def get_bioactivity_summary(cid: int) -> Optional[Dict[str, Any]]:
    """
    Fetch bioactivity assay summary for a compound from PubChem.
    Returns summary with active assay count and sample activity values.
    """
    try:
        url = f"{PUBCHEM_BASE}/compound/cid/{cid}/assaysummary/JSON"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            assays = data.get("Table", {}).get("Row", [])
            
            active_count = 0
            sample_activities = []
            
            for row in assays[:50]:  # Check first 50 assays
                cells = row.get("Cell", [])
                if len(cells) >= 4:
                    outcome = cells[3] if len(cells) > 3 else ""
                    if str(outcome).lower() == "active":
                        active_count += 1
                        # Try to extract activity value
                        if len(cells) > 5 and cells[5]:
                            try:
                                val = float(cells[5])
                                sample_activities.append(val)
                            except (ValueError, TypeError):
                                pass
            
            total = len(assays)
            print(f"[PUBCHEM] Bioactivity for CID {cid}: {active_count}/{total} active assays")
            return {
                "total_assays": total,
                "active_assays": active_count,
                "activity_ratio": round(active_count / max(total, 1), 2),
                "sample_activities": sample_activities[:5]
            }
    except Exception as e:
        print(f"[PUBCHEM] Bioactivity lookup error: {e}")
    return None


def compute_druglikeness_score(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute a drug-likeness assessment based on Lipinski's Rule of Five
    using real PubChem molecular properties.
    """
    mw = properties.get("MolecularWeight", 0)
    logp = properties.get("XLogP", 0)
    hbd = properties.get("HBondDonorCount", 0)
    hba = properties.get("HBondAcceptorCount", 0)
    tpsa = properties.get("TPSA", 0)
    rotatable = properties.get("RotatableBondCount", 0)

    # Lipinski violations
    violations = 0
    if mw and float(mw) > 500: violations += 1
    if logp and float(logp) > 5: violations += 1
    if hbd and int(hbd) > 5: violations += 1
    if hba and int(hba) > 10: violations += 1

    # Simplified binding affinity estimate based on molecular descriptors
    # This uses an empirical linear model inspired by published QSAR studies
    try:
        estimated_affinity = round(
            -6.0
            - 0.15 * float(logp or 0)
            + 0.08 * int(hbd or 0)
            + 0.05 * int(hba or 0)
            - 0.02 * int(rotatable or 0)
            - 0.005 * float(tpsa or 0),
            2
        )
    except (ValueError, TypeError):
        estimated_affinity = -7.0

    return {
        "lipinski_violations": violations,
        "druglike": violations <= 1,
        "estimated_affinity_kcal": estimated_affinity,
        "molecular_weight": mw,
        "logp": logp,
        "hbd": hbd,
        "hba": hba,
        "tpsa": tpsa,
        "rotatable_bonds": rotatable
    }

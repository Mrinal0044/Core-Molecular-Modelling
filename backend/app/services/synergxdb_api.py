"""
SYNERGxDB REST API client for drug combination synergy data.
API Docs: https://synergxdb.ca/documentation/
No authentication required.
"""
import requests
import logging
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

SYNERGXDB_BASE = "https://synergxdb.ca/api"
_drug_cache: Optional[List[Dict]] = None


def _get_drug_list() -> List[Dict]:
    """Fetch and cache the full drug list from SYNERGxDB."""
    global _drug_cache
    if _drug_cache is not None:
        return _drug_cache
    try:
        resp = requests.get(f"{SYNERGXDB_BASE}/drugs", timeout=20)
        if resp.status_code == 200:
            _drug_cache = resp.json()
            print(f"[SYNERGxDB] Cached {len(_drug_cache)} drugs")
            return _drug_cache
    except Exception as e:
        print(f"[SYNERGxDB] Failed to fetch drug list: {e}")
    return []


def find_drug_by_pubchem_cid(cid: int) -> Optional[Dict]:
    """
    Search the SYNERGxDB drug list for a drug matching a PubChem CID.
    Returns the drug dict with idDrug, name, smiles, etc. or None.
    """
    if not cid:
        return None
    cid_str = str(cid)
    drugs = _get_drug_list()
    for drug in drugs:
        if drug.get("idPubChem") == cid_str:
            print(f"[SYNERGxDB] Matched CID {cid} → '{drug['name']}' (idDrug={drug['idDrug']})")
            return drug
    print(f"[SYNERGxDB] No drug found for CID {cid}")
    return None


def find_drug_by_smiles(smiles: str) -> Optional[Dict]:
    """
    Fallback: search by SMILES string match.
    """
    drugs = _get_drug_list()
    for drug in drugs:
        if drug.get("smiles") and drug["smiles"] == smiles:
            print(f"[SYNERGxDB] Matched SMILES → '{drug['name']}' (idDrug={drug['idDrug']})")
            return drug
    return None


def get_synergy_combos(id_drug: int, limit: int = 20) -> List[Dict]:
    """
    Fetch drug combination synergy data for a given drug.
    Returns list of combo objects sorted by highest absolute Bliss score.
    Each combo includes: comboId, drugNameA, drugNameB, bliss, loewe, hsa, zip,
                          sampleName, tissue, sourceName, etc.
    """
    try:
        resp = requests.get(
            f"{SYNERGXDB_BASE}/combos",
            params={"drugId1": id_drug},
            timeout=15
        )
        if resp.status_code == 200:
            combos = resp.json()
            if combos:
                # Sort by absolute ZIP score (most synergistic first)
                combos.sort(key=lambda c: abs(c.get("zip", 0)), reverse=True)
                print(f"[SYNERGxDB] Found {len(combos)} combos for drug {id_drug}, top ZIP={combos[0].get('zip')}")
                return combos[:limit]
    except Exception as e:
        print(f"[SYNERGxDB] Combo lookup failed: {e}")
    return []


def get_dose_response_matrix(combo_id: int) -> List[Dict]:
    """
    Fetch the dose-response matrix for a specific drug combination.
    Returns list of dicts with: concA, concB, response (viability %).
    Response is viability: 100 = no effect, 0 = full inhibition.
    """
    try:
        resp = requests.get(
            f"{SYNERGXDB_BASE}/combos/{combo_id}/dose_response",
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            if data:
                print(f"[SYNERGxDB] Got {len(data)} dose-response points for combo {combo_id}")
                return data
    except Exception as e:
        print(f"[SYNERGxDB] Dose-response fetch failed: {e}")
    return []


def get_synergy_data_for_molecule(pubchem_cid: int, smiles: str = None) -> Optional[Dict]:
    """
    High-level function: given a PubChem CID (and optional SMILES fallback),
    find the best synergy combo and its dose-response matrix.
    
    Returns a dict with:
        - drug_name: name of the queried drug
        - partner_drug: name of the combo partner
        - combo: full combo object (bliss, loewe, hsa, zip, cell line, tissue, etc.)
        - dose_response: list of dose-response data points
        - source: "SYNERGxDB"
    Or None if the drug is not found in SYNERGxDB.
    """
    # Try to find the drug
    drug = find_drug_by_pubchem_cid(pubchem_cid)
    if not drug and smiles:
        drug = find_drug_by_smiles(smiles)
    if not drug:
        return None

    id_drug = drug["idDrug"]
    drug_name = drug["name"]

    # Get top synergy combo
    combos = get_synergy_combos(id_drug, limit=5)
    if not combos:
        print(f"[SYNERGxDB] No combos found for '{drug_name}'")
        return None

    # Pick the combo with highest absolute ZIP score
    best_combo = combos[0]
    combo_id = best_combo["comboId"]

    # Determine partner drug name
    if best_combo.get("drugNameA", "").lower() == drug_name.lower():
        partner_drug = best_combo.get("drugNameB", "Unknown")
    else:
        partner_drug = best_combo.get("drugNameA", "Unknown")

    # Fetch dose-response matrix
    dose_response = get_dose_response_matrix(combo_id)
    if not dose_response:
        print(f"[SYNERGxDB] No dose-response data for combo {combo_id}")
        return None

    return {
        "drug_name": drug_name,
        "partner_drug": partner_drug,
        "combo": best_combo,
        "dose_response": dose_response,
        "source": "SYNERGxDB"
    }

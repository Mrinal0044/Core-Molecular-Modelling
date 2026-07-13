import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import rdkit and pubchempy, but don't crash if not installed (for mock mode)
try:
    import pubchempy as pcp
    from rdkit import Chem
    from rdkit.Chem import AllChem
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False
    logger.warning("rdkit or pubchempy not installed. Operating in mock mode for structure generation.")

# ── Common drug target names → known PDB IDs ──
# This avoids API calls for well-known targets.
KNOWN_PROTEIN_MAP = {
    "parp":       "7AAP",
    "parp1":      "7AAP",
    "parp2":      "3KCZ",
    "egfr":       "1M17",
    "her2":       "3PP0",
    "braf":       "3OG7",
    "cdk2":       "1HCK",
    "ace2":       "1R42",
    "insulin":    "4INS",
    "p53":        "1TSR",
    "hiv protease": "1HVR",
    "thrombin":   "1PPB",
    "trypsin":    "1S0Q",
    "lysozyme":   "1AKI",
    "albumin":    "1AO6",
    "hemoglobin": "1GZX",
    "myoglobin":  "1MBN",
    "collagen":   "1CAG",
    "kinase":     "1ATP",
    "cox2":       "5IKQ",
    "jak2":       "3FUP",
    "vegfr":      "3WZE",
    "abl":        "2HYY",
    "crambin":    "1CRN",
}


def _download_pdb(pdb_id: str, output_dir: str) -> Optional[str]:
    """Downloads a PDB file by ID from RCSB. Returns the file path or None."""
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            file_path = os.path.join(output_dir, f"{pdb_id}.pdb")
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"[STRUCTURE] Downloaded PDB: {pdb_id} ({len(response.content)} bytes)")
            return file_path
        else:
            print(f"[STRUCTURE] PDB download failed for '{pdb_id}' (HTTP {response.status_code})")
            return None
    except Exception as e:
        print(f"[STRUCTURE] PDB download error for '{pdb_id}': {e}")
        return None


def _search_rcsb_by_name(protein_name: str) -> Optional[str]:
    """
    Searches the RCSB PDB by protein name and returns the best-matching PDB ID.
    Uses the RCSB Search API v2.
    """
    search_url = "https://search.rcsb.org/rcsbsearch/v2/query"
    query = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {
                "value": protein_name
            }
        },
        "return_type": "entry",
        "request_options": {
            "results_content_type": ["experimental"],
            "paginate": {"start": 0, "rows": 1}
        }
    }
    try:
        resp = requests.post(search_url, json=query, timeout=10,
                             headers={"Content-Type": "application/json"})
        print(f"[STRUCTURE] RCSB search for '{protein_name}': HTTP {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("result_set", [])
            if results:
                pdb_id = results[0].get("identifier", "").upper()
                print(f"[STRUCTURE] RCSB search resolved '{protein_name}' → {pdb_id}")
                return pdb_id
    except Exception as e:
        print(f"[STRUCTURE] RCSB search API error: {e}")
    return None


def fetch_protein_pdb(protein_name: str, output_dir: str) -> Optional[str]:
    """
    Fetches a PDB file from the RCSB Protein Data Bank.
    Resolution order:
      1. Check the built-in KNOWN_PROTEIN_MAP for common drug targets.
      2. If it looks like a 4-letter PDB ID, try direct download.
      3. Fall back to RCSB full-text search API.
    """
    name = protein_name.strip()
    lookup_key = name.lower()

    # 1. Check built-in mapping
    if lookup_key in KNOWN_PROTEIN_MAP:
        pdb_id = KNOWN_PROTEIN_MAP[lookup_key]
        print(f"[STRUCTURE] Mapped '{name}' → PDB ID '{pdb_id}' (known target)")
        result = _download_pdb(pdb_id, output_dir)
        if result:
            return result

    # 2. Try as a direct PDB ID
    if len(name) == 4 and name.isalnum():
        print(f"[STRUCTURE] Trying '{name.upper()}' as a direct PDB ID...")
        result = _download_pdb(name.upper(), output_dir)
        if result:
            return result

    # 3. Search RCSB by name
    print(f"[STRUCTURE] Searching RCSB for '{name}'...")
    pdb_id = _search_rcsb_by_name(name)
    if pdb_id:
        return _download_pdb(pdb_id, output_dir)

    print(f"[STRUCTURE] ERROR: Could not resolve protein '{name}' to any PDB structure.")
    return None


def _resolve_to_smiles(name_or_smiles: str) -> Optional[str]:
    """
    Attempts to interpret the input as SMILES first. If RDKit rejects it,
    falls back to looking up the compound by name on PubChem.
    """
    if not RDKIT_AVAILABLE:
        return name_or_smiles

    # 1. Try parsing as SMILES directly
    mol = Chem.MolFromSmiles(name_or_smiles)
    if mol is not None:
        print(f"[STRUCTURE] Valid SMILES: '{name_or_smiles}'")
        return name_or_smiles

    # 2. SMILES parse failed — treat as a compound name and query PubChem
    print(f"[STRUCTURE] '{name_or_smiles}' is not valid SMILES. Looking up on PubChem...")
    try:
        compounds = pcp.get_compounds(name_or_smiles, 'name')
        if compounds:
            canonical = compounds[0].canonical_smiles
            print(f"[STRUCTURE] PubChem resolved '{name_or_smiles}' → {canonical}")
            return canonical
        else:
            print(f"[STRUCTURE] PubChem found no results for '{name_or_smiles}'")
    except Exception as e:
        print(f"[STRUCTURE] PubChem lookup error for '{name_or_smiles}': {e}")

    return None


def generate_ligand_3d(smiles_or_name: str, output_dir: str) -> Optional[str]:
    """
    Generates a 3D .sdf file for a ligand.
    Accepts a SMILES string OR a compound name (e.g., 'Aspirin').
    Invalid SMILES are automatically resolved via PubChem.
    """
    if RDKIT_AVAILABLE:
        smiles = _resolve_to_smiles(smiles_or_name)
        if smiles is None:
            print(f"[STRUCTURE] ERROR: Could not resolve '{smiles_or_name}' to a valid molecule.")
            return None

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            print(f"[STRUCTURE] ERROR: RDKit cannot parse resolved SMILES: {smiles}")
            return None

        mol = Chem.AddHs(mol)
        result = AllChem.EmbedMolecule(mol, randomSeed=42)
        if result == -1:
            # Fallback: use random coordinates
            AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
        AllChem.MMFFOptimizeMolecule(mol)

        safe_name = "".join([c if c.isalnum() else "_" for c in smiles_or_name])[:50]
        file_path = os.path.join(output_dir, f"{safe_name}.sdf")

        writer = Chem.SDWriter(file_path)
        writer.write(mol)
        writer.close()
        print(f"[STRUCTURE] Generated 3D ligand: {file_path}")
        return file_path
    else:
        # Mock mode
        safe_name = "".join([c if c.isalnum() else "_" for c in smiles_or_name])[:50]
        file_path = os.path.join(output_dir, f"{safe_name}.sdf")
        with open(file_path, "w") as f:
            f.write("MOCK SDF FILE CONTENT")
        return file_path

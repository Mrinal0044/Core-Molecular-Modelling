from app.services.prediction import validate_smiles, validate_protein_sequence

def test_validate_smiles_success():
    # Valid smiles: Ethanol, Benzene, Caffeine
    assert validate_smiles("CCO") is True
    assert validate_smiles("c1ccccc1") is True
    assert validate_smiles("CN1C=NC2=C1C(=O)N(C(=O)N2C)C") is True

def test_validate_smiles_failure():
    # Invalid smiles representations
    assert validate_smiles("C=C=C=C=C=C=C=C=C") is False  # Chemical structure issue or invalid valence
    assert validate_smiles("abc") is False
    assert validate_smiles("") is False
    assert validate_smiles("   ") is False

def test_validate_protein_sequence_success():
    # Standard amino acids sequence
    assert validate_protein_sequence("MKTLLILAVMSTW") is True
    assert validate_protein_sequence("mktllilavmstw") is True  # Case insensitive
    assert validate_protein_sequence("MKT LLIL AVMSTW") is True  # Handles whitespace

def test_validate_protein_sequence_failure():
    # Contains non-amino acid letters (like B, J, O, U, X, Z)
    assert validate_protein_sequence("MKTLLILAVMSTWJ") is False
    assert validate_protein_sequence("MKTX") is False
    assert validate_protein_sequence("") is False
    assert validate_protein_sequence("   ") is False

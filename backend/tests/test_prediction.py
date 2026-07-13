from unittest.mock import patch
# pyrefly: ignore [missing-import]
from fastapi import status
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient

@patch("app.services.prediction.DeepPurposePredictor.predict_affinity")
def test_predict_binding_affinity_success(mock_predict, client: TestClient, auth_headers: dict):
    # Mocking prediction return value
    mock_predict.return_value = -9.34

    payload = {
        "smiles": "CCN(CC)CC",
        "protein_sequence": "MKTLLILAVMSTW"
    }
    response = client.post(
        "/api/binding-affinity/predict",
        json=payload,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["binding_affinity"] == -9.34
    assert data["confidence"] == 0.90
    assert data["unit"] == "kcal/mol"
    assert data["model"] == "DeepPurpose"

def test_predict_binding_affinity_invalid_smiles(client: TestClient, auth_headers: dict):
    payload = {
        "smiles": "invalid_smiles_string",
        "protein_sequence": "MKTLLILAVMSTW"
    }
    response = client.post(
        "/api/binding-affinity/predict",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid SMILES" in response.json()["detail"]

def test_predict_binding_affinity_invalid_sequence(client: TestClient, auth_headers: dict):
    payload = {
        "smiles": "CCN(CC)CC",
        "protein_sequence": "MKTLLILAVMSTW_INVALID_CHAR"
    }
    response = client.post(
        "/api/binding-affinity/predict",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Protein sequence contains invalid amino acids" in response.json()["detail"]

def test_predict_binding_affinity_unauthorized(client: TestClient):
    payload = {
        "smiles": "CCN(CC)CC",
        "protein_sequence": "MKTLLILAVMSTW"
    }
    response = client.post(
        "/api/binding-affinity/predict",
        json=payload
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

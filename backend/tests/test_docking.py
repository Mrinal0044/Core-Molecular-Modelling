import os
import shutil
import pytest
from unittest.mock import patch, MagicMock
# pyrefly: ignore [missing-import]
from fastapi import status
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from app.models.docking import DockingJob
from datetime import datetime, timezone

@patch("app.services.docking.run_docking_task")
@patch("app.services.docking.DockingService._save_uploaded_file")
def test_run_docking_success(mock_save_file, mock_celery_task, client: TestClient, auth_headers: dict):
    # Setup mock behaviors
    mock_save_file.return_value = None
    mock_celery_task.delay.return_value = MagicMock()

    files = {
        "protein": ("protein.pdb", b"ATOM      1  N   ALA ...", "chemical/x-pdb"),
        "ligands": ("ligand.sdf", b"$$$$", "chemical/x-mdl-sdfile")
    }
    
    data = {
        "exhaustiveness": 8,
        "num_modes": 9,
        "energy_range": 3.0
    }
    
    response = client.post(
        "/api/docking/run",
        files=files,
        data=data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    res_data = response.json()
    assert res_data["success"] is True
    assert "job_id" in res_data
    assert res_data["message"] == "Docking started."
    assert mock_celery_task.delay.called

def test_run_docking_invalid_protein_format(client: TestClient, auth_headers: dict):
    files = {
        "protein": ("protein.txt", b"dummy txt", "text/plain"),
        "ligands": ("ligand.sdf", b"$$$$", "chemical/x-mdl-sdfile")
    }
    response = client.post(
        "/api/docking/run",
        files=files,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported protein file format" in response.json()["detail"]

def test_run_docking_invalid_ligand_format(client: TestClient, auth_headers: dict):
    files = {
        "protein": ("protein.pdb", b"dummy pdb", "chemical/x-pdb"),
        "ligands": ("ligand.txt", b"dummy txt", "text/plain")
    }
    response = client.post(
        "/api/docking/run",
        files=files,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported ligand file format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_job_status_success(client: TestClient, auth_headers: dict, db_session: AsyncSession, test_user):
    # Insert job directly in DB
    job_id = uuid4()
    job = DockingJob(
        id=job_id,
        user_id=test_user.id,
        protein_path="uploads/dummy.pdb",
        ligand_path="uploads/dummy.sdf",
        status="Running",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(job)
    await db_session.commit()

    response = client.get(
        f"/api/docking/jobs/{job_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "Running"
    assert data["progress"] == 0.5

@pytest.mark.asyncio
async def test_get_job_results_not_ready(client: TestClient, auth_headers: dict, db_session: AsyncSession, test_user):
    job_id = uuid4()
    job = DockingJob(
        id=job_id,
        user_id=test_user.id,
        protein_path="uploads/dummy.pdb",
        ligand_path="uploads/dummy.sdf",
        status="Running",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(job)
    await db_session.commit()

    response = client.get(
        f"/api/docking/results/{job_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "is still in status" in response.json()["detail"]

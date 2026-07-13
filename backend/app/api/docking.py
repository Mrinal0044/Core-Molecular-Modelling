from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.docking import DockingService
from app.schemas.docking import (
    DockingRunResponse,
    DockingJobStatusResponse,
    DockingJobResultResponse,
)

router = APIRouter(prefix="/api/docking", tags=["Molecular Docking"])

@router.post(
    "/run",
    response_model=DockingRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit molecular docking job",
    description="Upload a receptor protein (.pdb) and ligand file (.sdf, .mol2, or .pdbqt) to start docking asynchronously."
)
async def run_docking(
    protein: UploadFile = File(..., description="Receptor protein structure file (.pdb)"),
    ligands: UploadFile = File(..., description="Ligand structure file (.sdf, .mol2, or .pdbqt)"),
    exhaustiveness: int = Form(8, ge=1, le=64, description="Exhaustiveness of the global search"),
    num_modes: int = Form(9, ge=1, le=100, description="Maximum number of binding modes to generate"),
    energy_range: float = Form(3.0, ge=1.0, le=20.0, description="Maximum energy difference between the best binding mode and the worst (kcal/mol)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await DockingService.submit_docking_job(
        db=db,
        user_id=current_user.id,
        protein_file=protein,
        ligand_file=ligands,
        exhaustiveness=exhaustiveness,
        num_modes=num_modes,
        energy_range=energy_range,
    )

@router.get(
    "/jobs/{job_id}",
    response_model=DockingJobStatusResponse,
    summary="Get docking job status",
    description="Check the current workflow execution state and progress of the docking job."
)
async def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Ensure standard route logic maps to the docking service
    return await DockingService.get_job_status(db=db, job_id=job_id)

@router.get(
    "/results/{job_id}",
    response_model=DockingJobResultResponse,
    summary="Get docking results",
    description="Fetch affinity scores, poses coordinate blocks, statistics, and execution duration for completed jobs."
)
async def get_job_results(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await DockingService.get_job_results(db=db, job_id=job_id)

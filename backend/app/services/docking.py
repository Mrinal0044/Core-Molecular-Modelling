import os
import shutil
import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.docking import DockingJob
from app.schemas.docking import (
    DockingRunResponse,
    DockingJobStatusResponse,
    DockingJobResultResponse,
)

logger = logging.getLogger(__name__)

class DockingService:
    """Service to handle Molecular Docking workflows and file handoffs."""

    @staticmethod
    async def submit_docking_job(
        db: AsyncSession,
        user_id: UUID,
        protein_file: UploadFile,
        ligand_file: UploadFile,
        exhaustiveness: int,
        num_modes: int,
        energy_range: float,
    ) -> DockingRunResponse:
        
        # 1. Validate File Extensions
        protein_ext = os.path.splitext(protein_file.filename or "")[1].lower()
        ligand_ext = os.path.splitext(ligand_file.filename or "")[1].lower()

        if protein_ext not in settings.ALLOWED_PROTEIN_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported protein file format. Must be: {', '.join(settings.ALLOWED_PROTEIN_EXTENSIONS)}"
            )

        if ligand_ext not in settings.ALLOWED_LIGAND_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported ligand file format. Must be: {', '.join(settings.ALLOWED_LIGAND_EXTENSIONS)}"
            )

        # 2. Setup Workspaces
        job_id = uuid4()
        job_upload_dir = os.path.join(settings.UPLOAD_DIR, str(job_id))
        job_output_dir = os.path.join(settings.OUTPUT_DIR, str(job_id))

        os.makedirs(job_upload_dir, exist_ok=True)
        os.makedirs(job_output_dir, exist_ok=True)

        protein_path = os.path.join(job_upload_dir, f"protein{protein_ext}")
        ligand_path = os.path.join(job_upload_dir, f"ligand{ligand_ext}")

        # 3. Stream Uploads with Size Checks
        await DockingService._save_uploaded_file(protein_file, protein_path)
        await DockingService._save_uploaded_file(ligand_file, ligand_path)

        # 4. Insert Job into database
        db_job = DockingJob(
            id=job_id,
            user_id=user_id,
            protein_path=protein_path,
            ligand_path=ligand_path,
            status="Pending",
            output_directory=job_output_dir,
        )
        db.add(db_job)
        await db.commit()
        await db.refresh(db_job)

        # 5. Dispatch Celery Task (Late import to prevent circular dependency)
        from app.workers.tasks import run_docking_task
        run_docking_task.delay(
            job_id=str(job_id),
            protein_path=protein_path,
            ligand_path=ligand_path,
            output_dir=job_output_dir,
            exhaustiveness=exhaustiveness,
            num_modes=num_modes,
            energy_range=energy_range,
        )

        logger.info(f"Submitted Docking job {job_id} for user {user_id}")
        return DockingRunResponse(
            success=True,
            job_id=job_id,
            message="Docking started."
        )

    @staticmethod
    async def get_job_status(db: AsyncSession, job_id: UUID) -> DockingJobStatusResponse:
        """Query DB for docking job state and map to status format."""
        stmt = select(DockingJob).where(DockingJob.id == job_id)
        result = await db.execute(stmt)
        job = result.scalars().first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Docking job {job_id} not found."
            )

        # Map state to progress float
        progress_map = {
            "Pending": 0.0,
            "Running": 0.5,
            "Completed": 1.0,
            "Failed": 0.0
        }
        progress = progress_map.get(job.status, 0.0)

        return DockingJobStatusResponse(
            status=job.status,
            progress=progress,
            created_at=job.created_at,
            finished_at=job.finished_at
        )

    @staticmethod
    async def get_job_results(db: AsyncSession, job_id: UUID) -> DockingJobResultResponse:
        """Query DB and read output directory to compile docking scores and files."""
        stmt = select(DockingJob).where(DockingJob.id == job_id)
        result = await db.execute(stmt)
        job = result.scalars().first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Docking job {job_id} not found."
            )

        if job.status == "Pending" or job.status == "Running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Docking job {job_id} is still in status '{job.status}'. Results are not ready."
            )

        if job.status == "Failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Docking job {job_id} failed. Review logs for details."
            )

        # Gather files inside outputs/
        output_files = []
        all_poses = []
        docking_stats = {}
        execution_time = None

        if job.output_directory and os.path.exists(job.output_directory):
            output_files = [
                f for f in os.listdir(job.output_directory)
                if os.path.isfile(os.path.join(job.output_directory, f))
            ]
            
            # Read output poses if PDBQT is generated
            poses_path = os.path.join(job.output_directory, "output_poses.pdbqt")
            if os.path.exists(poses_path):
                all_poses = DockingService._parse_pdbqt_poses(poses_path)

            # Read Vina log metrics
            log_path = os.path.join(job.output_directory, "docking.log")
            if os.path.exists(log_path):
                docking_stats = DockingService._parse_vina_log(log_path)

        if job.finished_at and job.created_at:
            execution_time = (job.finished_at - job.created_at).total_seconds()

        return DockingJobResultResponse(
            best_docking_score=job.score,
            all_docking_poses=all_poses,
            output_files=output_files,
            docking_statistics=docking_stats,
            execution_time=execution_time
        )

    @staticmethod
    async def _save_uploaded_file(file: UploadFile, dest_path: str):
        """Save a FastAPI UploadFile in chunks, rejecting if exceeding maxSize."""
        size = 0
        try:
            with open(dest_path, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > settings.MAX_UPLOAD_SIZE:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"Upload file exceeds maximum limit of {settings.MAX_UPLOAD_SIZE / (1024*1024):.0f}MB"
                        )
                    buffer.write(chunk)
        except HTTPException:
            # Clean up partial file on limits violation
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise
        except Exception as e:
            logger.error(f"Failed to save uploaded file {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving uploaded file: {str(e)}"
            )

    @staticmethod
    def _parse_pdbqt_poses(filepath: str) -> list:
        """Parse different models (poses) inside output pdbqt file."""
        poses = []
        current_pose = []
        pose_num = 0
        
        try:
            with open(filepath, "r") as f:
                for line in f:
                    if line.startswith("MODEL"):
                        pose_num = int(line.split()[1])
                        current_pose = []
                    elif line.startswith("ENDMDL"):
                        poses.append({
                            "pose_number": pose_num,
                            "pdbqt_content": "".join(current_pose)
                        })
                    else:
                        current_pose.append(line)
        except Exception as e:
            logger.warning(f"Error parsing poses from {filepath}: {str(e)}")
        
        return poses

    @staticmethod
    def _parse_vina_log(filepath: str) -> dict:
        """Extract score statistics from AutoDock Vina output log."""
        stats = {}
        modes = []
        try:
            with open(filepath, "r") as f:
                reading_table = False
                for line in f:
                    # Look for table header
                    if "mode |   affinity" in line:
                        reading_table = True
                        continue
                    if reading_table:
                        if line.startswith("-----") or line.strip() == "":
                            # End of table or divider line
                            if len(modes) > 0 and line.strip() == "":
                                reading_table = False
                            continue
                        # Try parsing table row
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                mode = int(parts[0])
                                affinity = float(parts[1])
                                rmsh_lb = float(parts[2])
                                rmsh_ub = float(parts[3])
                                modes.append({
                                    "mode": mode,
                                    "affinity": affinity,
                                    "rmsd_lb": rmsh_lb,
                                    "rmsd_ub": rmsh_ub
                                })
                            except ValueError:
                                pass
            if modes:
                stats["modes"] = modes
                stats["best_affinity"] = modes[0]["affinity"]
        except Exception as e:
            logger.warning(f"Error parsing Vina log {filepath}: {str(e)}")
        
        return stats

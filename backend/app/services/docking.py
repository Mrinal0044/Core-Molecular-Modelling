import uuid
import threading
import logging
from backend.database import SessionLocal, DockingJob
from backend.app.workers.tasks import execute_docking_pipeline

logger = logging.getLogger(__name__)


class DockingService:
    @staticmethod
    def submit_job(user_id: int, protein_name: str, ligand_name: str) -> str:
        db = SessionLocal()
        try:
            job_id = str(uuid.uuid4())
            new_job = DockingJob(
                job_id=job_id,
                user_id=user_id,
                status="Pending"
            )
            db.add(new_job)
            db.commit()

            # Run the pipeline in a background thread (no Redis/Celery needed)
            threading.Thread(
                target=execute_docking_pipeline,
                args=(job_id, protein_name, ligand_name),
                daemon=True
            ).start()

            return job_id
        finally:
            db.close()

    @staticmethod
    def get_job_status(job_id: str):
        db = SessionLocal()
        try:
            job = db.query(DockingJob).filter(DockingJob.job_id == job_id).first()
            if not job:
                return None
            return {
                "job_id": job.job_id,
                "status": job.status,
                "result_data": job.result_data
            }
        finally:
            db.close()

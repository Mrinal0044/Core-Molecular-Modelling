import os
import subprocess
import logging
import traceback
from datetime import datetime, timezone
from celery import shared_task
from app.config import settings
from app.database import SessionLocal
from app.models.docking import DockingJob

logger = logging.getLogger(__name__)

def calculate_receptor_bounding_box(pdb_path: str):
    """
    Parse receptor PDB coordinates to find the geometric center and bounding box.
    This enables zero-config blind docking by automatically mapping the grid box.
    """
    xs, ys, zs = [], [], []
    try:
        with open(pdb_path, "r") as f:
            for line in f:
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    try:
                        x = float(line[30:38].strip())
                        y = float(line[38:46].strip())
                        z = float(line[46:54].strip())
                        xs.append(x)
                        ys.append(y)
                        zs.append(z)
                    except (ValueError, IndexError):
                        continue
    except Exception as e:
        logger.error(f"Error reading coordinates from PDB: {str(e)}")
        
    if not xs:
        # Default fallback values if coordinates parsing fails
        return (0.0, 0.0, 0.0), (20.0, 20.0, 20.0)

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)

    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    center_z = (min_z + max_z) / 2.0

    # Bounding box size = max spread with 5.0 Å buffer, bounded by standard pocket values
    size_x = max(max_x - min_x, 15.0) + 5.0
    size_y = max(max_y - min_y, 15.0) + 5.0
    size_z = max(max_z - min_z, 15.0) + 5.0

    return (center_x, center_y, center_z), (size_x, size_y, size_z)

def run_subprocess_command(cmd: list, step_name: str):
    """Run shell command with error checking and log reporting."""
    logger.info(f"Executing step '{step_name}': {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout
    except FileNotFoundError as e:
        logger.error(f"Executable not found for step '{step_name}': {str(e)}")
        raise RuntimeError(
            f"Required CLI executable is missing on host environment. "
            f"Verify that Open Babel and AutoDock Vina are installed. Detailed error: {str(e)}"
        ) from e
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess '{step_name}' failed. Stderr: {e.stderr}. Stdout: {e.stdout}")
        raise RuntimeError(
            f"Execution failed during '{step_name}' step. CLI Stderr: {e.stderr}"
        ) from e

@shared_task(name="app.workers.tasks.run_docking_task")
def run_docking_task(
    job_id: str,
    protein_path: str,
    ligand_path: str,
    output_dir: str,
    exhaustiveness: int,
    num_modes: int,
    energy_range: float,
):
    """Celery task executing format conversion and AutoDock Vina execution."""
    logger.info(f"Starting Celery task for DockingJob: {job_id}")
    
    # Initialize DB Session
    db = SessionLocal()
    
    # 1. Update job to Running
    job = db.query(DockingJob).filter(DockingJob.id == job_id).first()
    if not job:
        logger.error(f"DockingJob {job_id} not found in DB at Celery worker initialization.")
        db.close()
        return

    job.status = "Running"
    db.commit()

    try:
        # 2. File Conversion
        # Define output pdbqt target filenames
        receptor_pdbqt = os.path.join(output_dir, "receptor.pdbqt")
        ligand_pdbqt = os.path.join(output_dir, "ligand.pdbqt")
        output_poses = os.path.join(output_dir, "output_poses.pdbqt")
        log_path = os.path.join(output_dir, "docking.log")

        # Convert Protein .pdb -> .pdbqt using Open Babel
        # -xr: prepare receptor (rigid, ignore/remove nonpolar hydrogens or charge corrections if needed)
        convert_receptor_cmd = [
            settings.OBABEL_EXECUTABLE,
            "-ipdb", protein_path,
            "-opdbqt",
            "-O", receptor_pdbqt,
            "-xr"
        ]
        run_subprocess_command(convert_receptor_cmd, "Receptor preparation (Open Babel)")

        # Convert Ligand (.sdf, .mol2, .pdbqt) -> .pdbqt using Open Babel
        ligand_ext = os.path.splitext(ligand_path)[1].lower().replace(".", "")
        convert_ligand_cmd = [
            settings.OBABEL_EXECUTABLE,
            f"-i{ligand_ext}", ligand_path,
            "-opdbqt",
            "-O", ligand_pdbqt,
            "--gen3d"  # Ensure 3D coordinate generation for 2D molecular inputs
        ]
        run_subprocess_command(convert_ligand_cmd, "Ligand preparation (Open Babel)")

        # 3. Calculate Docking Box Parameters
        (cx, cy, cz), (sx, sy, sz) = calculate_receptor_bounding_box(protein_path)

        # 4. Run AutoDock Vina
        vina_cmd = [
            settings.VINA_EXECUTABLE,
            "--receptor", receptor_pdbqt,
            "--ligand", ligand_pdbqt,
            "--center_x", f"{cx:.4f}",
            "--center_y", f"{cy:.4f}",
            "--center_z", f"{cz:.4f}",
            "--size_x", f"{sx:.4f}",
            "--size_y", f"{sy:.4f}",
            "--size_z", f"{sz:.4f}",
            "--exhaustiveness", str(exhaustiveness),
            "--num_modes", str(num_modes),
            "--energy_range", str(energy_range),
            "--out", output_poses,
            "--log", log_path
        ]
        run_subprocess_command(vina_cmd, "AutoDock Vina Docking")

        # 5. Parse Best Docking Score
        best_score = None
        if os.path.exists(log_path):
            best_score = parse_best_score(log_path)

        # 6. Update DB to Completed
        job.status = "Completed"
        job.score = best_score
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Completed DockingJob {job_id} successfully. Score: {best_score}")

    except Exception as e:
        logger.error(f"DockingJob {job_id} failed during execution: {str(e)}")
        logger.error(traceback.format_exc())
        
        job.status = "Failed"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        
    finally:
        db.close()

def parse_best_score(log_path: str) -> float | None:
    """Parse the best affinity binding score (mode 1) from Vina output logs."""
    try:
        with open(log_path, "r") as f:
            table_started = False
            for line in f:
                if "mode |   affinity" in line:
                    table_started = True
                    continue
                if table_started:
                    if line.startswith("-----") or line.strip() == "":
                        continue
                    # The first numeric row after header dividers is mode 1
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            return float(parts[1])
                        except ValueError:
                            pass
    except Exception as e:
        logger.warning(f"Failed to parse best score from log {log_path}: {str(e)}")
    return None

# Quantum PharmX Backend Services

Quantum PharmX is a production-ready computational chemistry and AI drug discovery backend. It provides asynchronous Molecular Docking workflows (via AutoDock Vina and Open Babel) and ligand-protein Binding Affinity Predictions (via RDKit and DeepPurpose).

---

## Architecture & Workflow Overview

### Module 1: Molecular Docking
1. **API Submission**: Users upload a receptor structure (`.pdb`) and a ligand file (`.sdf`, `.mol2`, or `.pdbqt`) via `POST /api/docking/run` along with parameters (`exhaustiveness`, `num_modes`, `energy_range`).
2. **Database Ingestion**: The backend creates a UUID-identified `DockingJob` record in PostgreSQL with status `Pending`.
3. **Queueing**: A Celery task is dispatched via Redis.
4. **Execution Pipeline (Celery Worker)**:
   - Sets job status to `Running`.
   - Converts the receptor PDB to PDBQT format using **Open Babel**.
   - Converts the ligand molecular file to PDBQT format using **Open Babel** (with `--gen3d` for 3D coordinate creation if given 2D inputs).
   - Automatically parses coordinates from the receptor to calculate the pocket's **3D geometric center and bounding box** dynamically (blind docking).
   - Spawns a subprocess running **AutoDock Vina** with the computed box.
   - Parses the output log file to extract the top mode binding affinity energy score and the structural poses from the output PDBQT.
   - Saves results in PostgreSQL and flags status as `Completed` or `Failed`.

### Module 2: Binding Affinity Prediction
1. **Input Validation**: Validates ligand SMILES representations using **RDKit** and verifies the protein sequence contains only standard single-letter IUPAC amino acids.
2. **Encoding & Prediction**: Passes coordinates and sequence text through a singleton-wrapped pre-trained **DeepPurpose** model (`MPNN_CNN_BindingDB` architecture) to predict the binding affinity score (in $K_d$ log-scales/free energy approximations).
3. **Results**: Stores the inference run in PostgreSQL and returns the score, model name, and confidence back to the user.

---

## Computational Tools Installation

If you are running the project locally outside of Docker, install the external binary tools below:

### 1. Open Babel (File Converter)
* **macOS** (Homebrew):
  ```bash
  brew install open-babel
  ```
* **Ubuntu/Debian**:
  ```bash
  sudo apt-get update && sudo apt-get install -y openbabel
  ```

### 2. AutoDock Vina (Docking Engine)
* **Ubuntu/Debian**:
  ```bash
  sudo apt-get update && sudo apt-get install -y autodock-vina
  # The binary installs as `autodock-vina`. Create an alias for `vina`:
  sudo ln -sf /usr/bin/autodock-vina /usr/bin/vina
  ```
* **macOS/Windows**: Download pre-compiled executables from the official [AutoDock Vina Releases Page](https://github.com/ccsb-scripps/AutoDock-Vina/releases) and add the binary to your system PATH.

### 3. RDKit & DeepPurpose (Python AI Engine)
We recommend using a Conda environment to avoid local dependency compilation errors:
```bash
conda create -n pharmx python=3.12 -y
conda activate pharmx
conda install -c conda-forge rdkit -y
pip install torch
pip install DeepPurpose
```

---

## Docker Execution (Recommended)

Docker Compose configures PostgreSQL, Redis, FastAPI, and Celery out of the box. Host paths for uploads and outputs are automatically shared via mounted Docker volumes.

1. **Build and Run**:
   ```bash
   docker compose up --build
   ```
2. **Automatic Migrations**: The containers automatically run Alembic migrations (`alembic upgrade head`) and configure the database schema tables before launching.
3. **API Access**: The API will be available at `http://localhost:8000`. OpenAPI documentation is loaded at `http://localhost:8000/docs`.

---

## Local Development Startup

If running locally:
1. **Setup Env**: Copy `.env` and adjust database and celery coordinates:
   ```bash
   cp .env.example .env
   ```
2. **Start Services**: Ensure Redis and PostgreSQL are running locally.
3. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```
5. **Start FastAPI Application**:
   ```bash
   uvicorn app.main:app --reload
   ```
6. **Start Celery Worker**:
   ```bash
   celery -A app.workers.celery_app.celery_app worker --loglevel=info
   ```

---

## Running Unit Tests
Unit tests use an in-memory SQLite database configuration to run database assertions quickly and cleanly without polluting production databases.
Run tests using:
```bash
pytest -v
```

---

## API Usage Guidelines

### 1. User Authentication
* **Register User**:
  `POST /api/auth/register`
  ```json
  {
    "email": "scientist@pharmx.com",
    "password": "securepassword123"
  }
  ```
* **Retrieve Access Token**:
  `POST /api/auth/login`
  ```json
  {
    "email": "scientist@pharmx.com",
    "password": "securepassword123"
  }
  ```
  *Copy the returned `access_token` and append it to downstream requests as an `Authorization: Bearer <token>` header.*

### 2. Molecular Docking API
* **Submit Job**:
  `POST /api/docking/run` (Accepts `multipart/form-data`)
  - `protein`: upload receptor structure (`.pdb`)
  - `ligands`: upload ligand structure (`.sdf`, `.mol2`, or `.pdbqt`)
  - `exhaustiveness` (Form parameter, default: `8`)
  - `num_modes` (Form parameter, default: `9`)
  - `energy_range` (Form parameter, default: `3.0`)
* **Poll Status**:
  `GET /api/docking/jobs/{job_id}`
* **Fetch Results**:
  `GET /api/docking/results/{job_id}`

### 3. Binding Affinity Prediction API
* **Predict Affinity**:
  `POST /api/binding-affinity/predict`
  ```json
  {
    "smiles": "CCN(CC)CC",
    "protein_sequence": "MKTLLILAVMSTW"
  }
  ```

from pydantic import BaseModel, Field
from typing import Optional

class BindingAffinityRequest(BaseModel):
    smiles: str = Field(..., description="SMILES string of the ligand molecule.")
    protein_sequence: str = Field(..., description="Amino acid sequence of the protein receptor.")

class BindingAffinityResponse(BaseModel):
    binding_affinity: float
    confidence: float
    unit: str = "kcal/mol"
    model: str = "DeepPurpose"

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any

class DockingRunResponse(BaseModel):
    success: bool
    job_id: UUID
    message: str

class DockingJobStatusResponse(BaseModel):
    status: str
    progress: float
    created_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DockingJobResultResponse(BaseModel):
    best_docking_score: Optional[float] = Field(None, serialization_alias="Best Docking Score")
    all_docking_poses: List[Dict[str, Any]] = Field(default_factory=list, serialization_alias="All Docking Poses")
    output_files: List[str] = Field(default_factory=list, serialization_alias="Output Files")
    docking_statistics: Dict[str, Any] = Field(default_factory=dict, serialization_alias="Docking Statistics")
    execution_time: Optional[float] = Field(None, serialization_alias="Execution Time")

    class Config:
        populate_by_name = True
        from_attributes = True

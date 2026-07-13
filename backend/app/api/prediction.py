from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.prediction import BindingAffinityService
from app.schemas.prediction import BindingAffinityRequest, BindingAffinityResponse

router = APIRouter(prefix="/api/binding-affinity", tags=["Binding Affinity"])

@router.post(
    "/predict",
    response_model=BindingAffinityResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict ligand-protein binding affinity",
    description="Analyze binding affinity (kcal/mol) of a small molecule ligand (SMILES) to a target protein sequence using DeepPurpose."
)
async def predict_binding_affinity(
    request: BindingAffinityRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await BindingAffinityService.create_prediction(
        db=db,
        user_id=current_user.id,
        request=request
    )

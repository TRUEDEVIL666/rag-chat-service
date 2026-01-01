from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.core.factory import get_ai_model_service
from app.schemas.ai_model import (
    AiProviderResponse, AiModelResponse, AiModelProviderRequest, AiModelTypeRequest,
    AiProviderCreate, AiProviderUpdate, AiModelCreate, AiModelUpdate
)
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/providers", response_model=List[AiProviderResponse])
def list_providers(
    service=Depends(get_ai_model_service),
    auth=Depends(get_current_user)
):
  try:
    return service.list_providers(access_token=auth.get("token"))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/{provider_id}/models", response_model=List[AiModelResponse])
def list_models_by_provider(
    req: AiModelProviderRequest = Depends(),
    service=Depends(get_ai_model_service),
    auth=Depends(get_current_user)
):
  try:
    return service.get_models_by_provider(str(req.provider_id), model_type=req.model_type, access_token=auth.get("token"))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/type/{model_type}", response_model=List[AiModelResponse])
def list_models_by_type(
    req: AiModelTypeRequest = Depends(),
    service=Depends(get_ai_model_service),
    auth=Depends(get_current_user)
):
  try:
    return service.list_models_by_type(req.model_type, access_token=auth.get("token"))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=List[AiModelResponse])
def list_all_models(
    service=Depends(get_ai_model_service),
    auth=Depends(get_current_user)
):
  try:
    return service.list_all_models(access_token=auth.get("token"))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers", response_model=AiProviderResponse)
def create_provider(
    data: AiProviderCreate,
    service=Depends(get_ai_model_service),
    auth=Depends(get_current_user)
):
  try:
    return service.create_provider(data.dict(exclude_unset=True), access_token=auth.get("token"))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.put("/providers/{provider_id}", response_model=AiProviderResponse)
def update_provider(
    provider_id: str,
    data: AiProviderUpdate,
    service=Depends(get_ai_model_service),
    auth=Depends(get_current_user)
):
  try:
    return service.update_provider(provider_id, data.dict(exclude_unset=True), access_token=auth.get("token"))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.delete("/providers/{provider_id}")
def delete_provider(
    provider_id: str,
    service=Depends(get_ai_model_service),
    auth=Depends(get_current_user)
):
  try:
    success = service.delete_provider(
      provider_id, access_token=auth.get("token"))
    if not success:
      raise HTTPException(status_code=404, detail="Provider not found")
    return {"message": "Provider deleted successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/models", response_model=AiModelResponse)
def create_model(
    data: AiModelCreate,
    service=Depends(get_ai_model_service),
    auth=Depends(get_current_user)
):
  try:
    return service.create_model(data.dict(exclude_unset=True), access_token=auth.get("token"))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.put("/models/{model_id}", response_model=AiModelResponse)
def update_model(
    model_id: str,
    data: AiModelUpdate,
    service=Depends(get_ai_model_service),
    auth=Depends(get_current_user)
):
  try:
    return service.update_model(model_id, data.dict(exclude_unset=True), access_token=auth.get("token"))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.delete("/models/{model_id}")
def delete_model(
    model_id: str,
    service=Depends(get_ai_model_service),
    auth=Depends(get_current_user)
):
  try:
    success = service.delete_model(model_id, access_token=auth.get("token"))
    if not success:
      raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

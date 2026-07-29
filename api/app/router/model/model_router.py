from fastapi import APIRouter, Depends

from app.request.model.model import (
    ModelCreateRequest,
    ModelDeleteRequest,
    ModelUpdateRequest,
)
from app.service.model.model_service import ModelService, get_model_service

model_router = APIRouter(prefix="/model", tags=["model"])


@model_router.post("/create")
async def create_model(
    request: ModelCreateRequest,
    model_service: ModelService = Depends(get_model_service),
):
    model_id = await model_service.create_model(request)
    return {"id": model_id}


@model_router.post("/delete")
async def delete_model(
    request: ModelDeleteRequest,
    model_service: ModelService = Depends(get_model_service),
):
    await model_service.delete_model(request)
    return {"status": "success"}


@model_router.post("/update")
async def update_model(
    request: ModelUpdateRequest,
    model_service: ModelService = Depends(get_model_service),
):
    return await model_service.update_model(request)


@model_router.get("/list")
async def get_model_list(
    model_service: ModelService = Depends(get_model_service),
):
    return await model_service.get_model_list()

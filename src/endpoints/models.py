"""
Model management endpoints
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import optional_auth, verify_auth
from ..model_manager import model_manager
from ..models import Model, ModelList

router = APIRouter()


@router.get("/models", response_model=ModelList)
async def list_models(auth: dict | None = Depends(optional_auth)):
    """List available models"""
    available_models = model_manager.list_available_models()

    models = []
    for model_info in available_models:
        model = Model(
            id=model_info["id"],
            object="model",
            created=int(datetime.utcnow().timestamp()),
            owned_by="libraxis",
            root=model_info["id"],
            parent=None
        )
        models.append(model)

    return ModelList(object="list", data=models)


@router.get("/models/{model_id}")
async def retrieve_model(model_id: str, auth: dict = Depends(verify_auth)):
    """Get details about a specific model"""
    # Replace slashes in model_id
    model_id = model_id.replace("--", "/")

    # Check if model exists
    available_models = model_manager.list_available_models()
    model_info = next((m for m in available_models if m["id"] == model_id), None)

    if not model_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )

    # Get additional info if model is loaded
    loaded_info = model_manager.get_model_info(model_id)

    response = {
        "id": model_id,
        "object": "model",
        "created": int(datetime.utcnow().timestamp()),
        "owned_by": "libraxis",
        "root": model_id,
        "parent": None,
        "permission": [],
        "loaded": model_info["loaded"],
        "path": model_info["path"]
    }

    if loaded_info:
        response.update({
            "loaded_at": loaded_info["loaded_at"],
            "memory_usage_gb": loaded_info["memory_usage"]
        })

    return response


@router.post("/models/{model_id}/load")
async def load_model(model_id: str, auth: dict = Depends(verify_auth)):
    """Load a model into memory"""
    model_id = model_id.replace("--", "/")

    try:
        await model_manager.load_model(model_id)
        return {
            "status": "success",
            "message": f"Model {model_id} loaded successfully",
            "memory_usage": model_manager.memory_usage
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/models/{model_id}/unload")
async def unload_model(model_id: str, auth: dict = Depends(verify_auth)):
    """Unload a model from memory"""
    model_id = model_id.replace("--", "/")

    try:
        await model_manager.unload_model(model_id)
        return {
            "status": "success",
            "message": f"Model {model_id} unloaded successfully",
            "memory_usage": model_manager.memory_usage
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/models/memory/usage")
async def get_memory_usage(auth: dict = Depends(verify_auth)):
    """Get current memory usage"""
    return {
        "memory_usage": model_manager.memory_usage,
        "loaded_models": list(model_manager.models.keys()),
        "current_model": model_manager.current_model
    }

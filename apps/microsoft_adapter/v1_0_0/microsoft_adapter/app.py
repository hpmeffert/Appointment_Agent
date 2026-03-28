from fastapi import APIRouter

router = APIRouter(prefix="/api/microsoft/v1.0.0", tags=["microsoft-adapter-v1.0.0"])


@router.get("/help")
def help_view() -> dict[str, object]:
    return {
        "module": "microsoft_adapter",
        "version": "v1.0.0",
        "status": "prepared",
    }

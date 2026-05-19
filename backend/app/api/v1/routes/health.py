from fastapi import APIRouter

router = APIRouter()

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/")
def health_check():
    return {"status": "ok"}

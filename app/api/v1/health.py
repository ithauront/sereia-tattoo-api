from fastapi import APIRouter

router = APIRouter(prefix="/healthz")


@router.get("")
def healthz():
    return {"status": "ok"}

from fastapi import APIRouter

router = APIRouter(
    prefix='/api/v1/system',
    tags=['System'],
)

@router.get(
    '/health',
)
async def health_check() -> dict:
    return {
        'status': 'service_healthy',
    }

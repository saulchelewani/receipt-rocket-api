from fastapi import FastAPI

from core.settings import settings
from apps.tenants.routes import router as tenant_router

app = FastAPI(
    title="Receipt Rocket API",
    description="Receipt Rocket API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.include_router(tenant_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)

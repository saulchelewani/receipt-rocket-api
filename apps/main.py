from fastapi import FastAPI

from apps.activation.routes import router as activation_router
from apps.config.routes import router as config_router
from apps.profiles.routes import router as profiles_router
from apps.tenants.routes import router as tenant_router
from core.settings import settings

app = FastAPI(
    title="Receipt Rocket API",
    description="Receipt Rocket API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.include_router(tenant_router, prefix=settings.API_V1_STR)
app.include_router(profiles_router, prefix=settings.API_V1_STR)

app.include_router(activation_router, prefix=settings.API_V1_STR)

app.include_router(config_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)

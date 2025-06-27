from fastapi import FastAPI

from apps.activation.routes import router as activation_router
from apps.auth.routes import router as auth_router
from apps.config.routes import router as config_router
from apps.products.routes import router as products_router
from apps.profiles.routes import router as profiles_router
from apps.roles.routes import router as roles_router
from apps.routes.routes import router as routes_router
from apps.sales.routes import router as sales_router
from apps.tenants.routes import router as tenant_router
from apps.terminals.routes import router as terminals_router
from apps.users.routes import router as users_router
from core.settings import settings

app = FastAPI(
    title="Receipt Rocket API",
    description="Receipt Rocket API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.include_router(tenant_router, prefix=settings.API_V1_STR)
app.include_router(profiles_router, prefix=settings.API_V1_STR)

app.include_router(terminals_router, prefix=settings.API_V1_STR)

app.include_router(auth_router)

app.include_router(activation_router, prefix=settings.API_V1_STR)

app.include_router(roles_router, prefix=settings.API_V1_STR)

app.include_router(config_router, prefix=settings.API_V1_STR)
app.include_router(products_router, prefix=settings.API_V1_STR)
app.include_router(sales_router, prefix=settings.API_V1_STR)

app.include_router(routes_router, prefix=settings.API_V1_STR)

app.include_router(users_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)

import httpx

from core.settings import settings


async def get_configuration():
    headers = {
        "accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.MRA_EIS_URL}/api/v1/configuration/get-latest-configs",
            headers=headers)

    return response.json()

import httpx


async def async_http_get(url, **kwargs):
    async with httpx.AsyncClient() as client:
        return await client.get(url, **kwargs)


async def async_http_post(url, **kwargs):
    async with httpx.AsyncClient() as client:
        return await client.post(url, **kwargs)

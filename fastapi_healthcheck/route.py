from typing import Callable
from cachetools import TTLCache
from starlette.responses import JSONResponse
from .service import HealthCheckFactory
from .enum import HealthCheckStatusEnum

cache = TTLCache(maxsize=1, ttl=10)

def healthCheckRoute(factory: HealthCheckFactory) -> Callable:
    """
    This function is passed to the add_api_route with the built factory.

    When called, the endpoint method within, will be called and it will run the job bound to the factory.
    The results will be parsed and sent back to the requestor via JSON.
    """
    
    _factory = factory

    def endpoint() -> JSONResponse:
        if "health" in cache:
            return JSONResponse(content=cache["health"], status_code=200)
        res = _factory.check()
        cache["health"] = res
        if res['status'] == HealthCheckStatusEnum.UNHEALTHY.value:
            return JSONResponse(content=res, status_code=500)
        return JSONResponse(content=res, status_code=200)

    return endpoint


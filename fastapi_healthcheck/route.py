from typing import Callable
from cachetools import TTLCache
from starlette.responses import JSONResponse
from .service import HealthCheckFactory
from .enum import HealthCheckStatusEnum

CACHE_TTL_SECONDS = 10


def healthCheckRoute(factory: HealthCheckFactory) -> Callable:
    """
    This function is passed to the add_api_route with the built factory.

    When called, the endpoint method within, will be called and it will run the job bound to the factory.
    The results will be parsed and sent back to the requestor via JSON.

    Results are cached for CACHE_TTL_SECONDS. A cached result is answered with the same
    status code as a fresh one (500 when Unhealthy), so every caller sees the failure, not
    only the one whose request happened to run the checks.
    """

    _factory = factory
    # One cache per route, so two factories never answer with each other's result.
    cache = TTLCache(maxsize=1, ttl=CACHE_TTL_SECONDS)

    def endpoint() -> JSONResponse:
        # Returns None if key is missing or expired.
        res = cache.get("health")

        if res is None:
            # cache was empty or expired. Regenerate.
            res = _factory.check()
            cache["health"] = res

        if res['status'] == HealthCheckStatusEnum.UNHEALTHY.value:
            return JSONResponse(content=res, status_code=500)
        return JSONResponse(content=res, status_code=200)

    return endpoint

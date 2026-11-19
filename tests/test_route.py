"""healthCheckRoute: status codes on fresh and cached results.

Run with: python -m pytest tests/
"""
import json

from fastapi_healthcheck import HealthCheckFactory, healthCheckRoute
from fastapi_healthcheck.enum import HealthCheckStatusEnum
from fastapi_healthcheck.service import HealthCheckBase
from fastapi_healthcheck.domain import HealthCheckInterface


class FlagCheck(HealthCheckBase, HealthCheckInterface):
    """A check whose result the test sets, counting how often it really ran."""

    def __init__(self, healthy: bool, alias: str = "flag") -> None:
        self._alias = alias
        self._tags = []
        self.healthy = healthy
        self.calls = 0

    def __checkHealth__(self) -> HealthCheckStatusEnum:
        self.calls += 1
        return HealthCheckStatusEnum.HEALTHY if self.healthy else HealthCheckStatusEnum.UNHEALTHY


def _route(check):
    factory = HealthCheckFactory()
    factory.add(check)
    return healthCheckRoute(factory=factory)


def _status(response):
    return response.status_code, json.loads(response.body)["status"]


def test_healthy_is_200_fresh_and_cached():
    check = FlagCheck(healthy=True)
    endpoint = _route(check)

    assert _status(endpoint()) == (200, "Healthy")
    assert _status(endpoint()) == (200, "Healthy")
    assert check.calls == 1  # second answer came from the cache


def test_cached_unhealthy_is_still_500():
    # The bug in 1.0.6: the cached copy of an Unhealthy result was answered with 200,
    # so a prober landing inside the TTL after another prober saw a pass.
    check = FlagCheck(healthy=False)
    endpoint = _route(check)

    assert _status(endpoint()) == (500, "Unhealthy")
    assert _status(endpoint()) == (500, "Unhealthy")
    assert check.calls == 1


def test_routes_do_not_share_a_cache():
    healthy_route = _route(FlagCheck(healthy=True, alias="a"))
    unhealthy_route = _route(FlagCheck(healthy=False, alias="b"))

    assert _status(unhealthy_route()) == (500, "Unhealthy")
    assert _status(healthy_route()) == (200, "Healthy")

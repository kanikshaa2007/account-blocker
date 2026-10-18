"""Test-only stubs for optional third-party deps missing in minimal envs.

Only activates when the real package cannot be imported, so full
`uv sync` environments keep using the real implementation.

Note: Stage 1 moderation router tests are isolated (they load
`app/services/moderation/router.py` directly by file path) and do not
need this stub. This stub exists only for legacy tests that import via
the `app.services` package chain; it intentionally does not fake
deeper `zep_cloud.*` submodules, so tests needing the real SDK still
fail clearly instead of passing on fakes.
"""

import sys
import types


def _ensure_zep_cloud_stub() -> None:
    try:
        import zep_cloud  # noqa: F401
        return
    except ImportError:
        pass

    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            return _Dummy()

    def _factory(*args, **kwargs):
        return _Dummy()

    zep_cloud = types.ModuleType("zep_cloud")
    zep_cloud.BatchAddItem = _Dummy
    zep_cloud.EntityEdgeSourceTarget = _Dummy

    class NotFoundError(Exception):
        pass

    zep_cloud.NotFoundError = NotFoundError

    client = types.ModuleType("zep_cloud.client")

    class Zep(_Dummy):
        pass

    client.Zep = Zep
    core = types.ModuleType("zep_cloud.core")
    api_error = types.ModuleType("zep_cloud.core.api_error")

    class ApiError(Exception):
        def __init__(self, *args, status_code=None, headers=None, body=None, **kwargs):
            super().__init__(*args)
            self.status_code = status_code
            self.headers = headers or {}
            self.body = body

    api_error.ApiError = ApiError
    core.api_error = api_error

    zep_cloud.client = client
    zep_cloud.core = core

    sys.modules["zep_cloud"] = zep_cloud
    sys.modules["zep_cloud.client"] = client
    sys.modules["zep_cloud.core"] = core
    sys.modules["zep_cloud.core.api_error"] = api_error


_ensure_zep_cloud_stub()

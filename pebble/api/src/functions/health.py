import azure.functions as func

from src.functions._http import api_handler, json_response
from src.logger import get_logger
from src.services.registry import get_services

bp = func.Blueprint()
logger = get_logger("health")


def compute_health_status(checks: dict[str, bool]) -> str:
    """All services are Essential: all up -> healthy, none up -> unhealthy, otherwise degraded."""
    if all(checks.values()):
        return "healthy"
    if not any(checks.values()):
        return "unhealthy"
    return "degraded"


def _safe(check) -> bool:  # noqa: ANN001
    try:
        return bool(check())
    except Exception as exc:  # noqa: BLE001
        logger.warning("health_check_failed", error=repr(exc))
        return False


@bp.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@api_handler
def health(req: func.HttpRequest) -> func.HttpResponse:
    try:
        services = get_services()
        checks = {
            "database": _safe(services.repository.health_check),
            "storage": _safe(services.blob_store.health_check),
            "amazon": _safe(services.product_search.health_check),
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("services_unavailable", error=repr(exc))
        checks = {"database": False, "storage": False, "amazon": False}

    status = compute_health_status(checks)
    # degraded still serves traffic, so it stays 200; only unhealthy is 503
    return json_response(
        {"status": status, "services": checks}, 503 if status == "unhealthy" else 200
    )

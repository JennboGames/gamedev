import azure.functions as func

from src.functions._http import api_handler, json_response
from src.services.registry import get_services

bp = func.Blueprint()


@bp.route(route="color-map", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@api_handler
def get_color_map(req: func.HttpRequest) -> func.HttpResponse:
    return json_response(get_services().color_maps().latest())

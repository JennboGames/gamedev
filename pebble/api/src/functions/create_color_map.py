import azure.functions as func

from src.functions._http import api_handler, json_response, parse_body
from src.models.api import ColorMapRequest
from src.services.registry import get_services

bp = func.Blueprint()


@bp.route(route="color-map", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@api_handler
def create_color_map(req: func.HttpRequest) -> func.HttpResponse:
    body = parse_body(req, ColorMapRequest, optional=True)
    product_ids = [str(pid) for pid in body.product_ids] if body.product_ids else None
    return json_response(get_services().color_maps().generate(product_ids), 201)

import azure.functions as func

from src.functions._http import api_handler, json_response, parse_uuid_param
from src.services.registry import get_services

bp = func.Blueprint()


@bp.route(route="shades/{id}/extract-hex", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@api_handler
def extract_shade_hex(req: func.HttpRequest) -> func.HttpResponse:
    shade_id = parse_uuid_param(req, "id")
    shade = get_services().collector().reextract_shade(shade_id)
    return json_response(shade)

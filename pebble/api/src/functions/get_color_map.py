import azure.functions as func
from pydantic import TypeAdapter

from src.functions._http import api_handler, json_response
from src.models.api import ColorMapShape
from src.services.registry import get_services

bp = func.Blueprint()

_SHAPE = TypeAdapter(ColorMapShape)


@bp.route(route="color-map", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@api_handler
def get_color_map(req: func.HttpRequest) -> func.HttpResponse:
    shape = _SHAPE.validate_python(req.params.get("shape", "rectangle"))
    return json_response(get_services().color_maps().latest(shape))

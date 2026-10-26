import azure.functions as func

from src.errors.error_types import NotFoundError
from src.functions._http import api_handler, json_response, parse_uuid_param
from src.services.registry import get_services

bp = func.Blueprint()


@bp.route(route="products/{id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@api_handler
def get_product(req: func.HttpRequest) -> func.HttpResponse:
    product_id = parse_uuid_param(req, "id")
    product = get_services().repository.get_product(product_id)
    if product is None:
        raise NotFoundError("Product", product_id)
    return json_response(product)

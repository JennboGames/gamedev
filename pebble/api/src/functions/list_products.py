import azure.functions as func

from src.functions._http import api_handler, json_response
from src.models.api import ProductList
from src.services.registry import get_services

bp = func.Blueprint()


@bp.route(route="products", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@api_handler
def list_products(req: func.HttpRequest) -> func.HttpResponse:
    return json_response(ProductList(items=get_services().repository.list_products()))

import azure.functions as func

from src.functions._http import api_handler, json_response
from src.models.api import SearchResponse
from src.services.registry import get_services

bp = func.Blueprint()


@bp.route(route="catalog/import", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@api_handler
def import_catalog(req: func.HttpRequest) -> func.HttpResponse:
    search_id, products = get_services().catalog_importer().import_catalog()
    return json_response(SearchResponse(search_id=search_id, products=products), 201)

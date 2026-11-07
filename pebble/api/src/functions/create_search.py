import uuid

import azure.functions as func

from src.functions._http import api_handler, json_response, parse_body
from src.models.api import SearchRequest, SearchResponse
from src.services.registry import get_services

bp = func.Blueprint()


@bp.route(route="searches", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@api_handler
def create_search(req: func.HttpRequest) -> func.HttpResponse:
    body = parse_body(req, SearchRequest)
    products, warnings = get_services().search_catalog(body.query.strip(), body.max_products)
    return json_response(
        SearchResponse(search_id=uuid.uuid4(), products=products, warnings=warnings), 201
    )

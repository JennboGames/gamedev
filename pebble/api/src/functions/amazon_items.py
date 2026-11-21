import azure.functions as func

from src.functions._http import api_handler, json_response, parse_body
from src.models.api import AmazonItemsRequest
from src.services.amazon_creators import get_client

bp = func.Blueprint()


@bp.route(route="experimental/amazon/items", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@api_handler
def amazon_items(req: func.HttpRequest) -> func.HttpResponse:
    body = parse_body(req, AmazonItemsRequest)
    return json_response(get_client().get_items(body.asins))

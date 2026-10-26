import azure.functions as func

from src.functions import (
    create_color_map,
    create_search,
    extract_shade_hex,
    get_color_map,
    get_product,
    health,
    list_product_shades,
    list_products,
    openapi,
)
from src.services.registry import initialize_services

# Picks providers once; invalid production configuration fails startup here.
initialize_services()

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

for module in (
    health,
    create_search,
    list_products,
    get_product,
    list_product_shades,
    extract_shade_hex,
    create_color_map,
    get_color_map,
    openapi,
):
    app.register_functions(module.bp)

from src.services.config import AppConfig


def make_config(**overrides) -> AppConfig:
    values = dict(
        environment="Development",
        storage_connection_string=None,
        database_url=None,
        azure_storage_account=None,
        azure_postgres_host=None,
        azure_postgres_database=None,
        azure_postgres_user=None,
        amazon_access_key="AKIATEST",
        amazon_secret_key="secret",
        amazon_partner_tag="tag-20",
        amazon_host="webservices.amazon.com",
        amazon_region="us-east-1",
        amazon_marketplace="www.amazon.com",
        max_shades_per_product=60,
        extraction_workers=2,
    )
    values.update(overrides)
    return AppConfig(**values)

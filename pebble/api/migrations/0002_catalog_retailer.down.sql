DELETE FROM products WHERE retailer = 'catalog';
ALTER TABLE products DROP CONSTRAINT products_retailer_check;
ALTER TABLE products ADD CONSTRAINT products_retailer_check
    CHECK (retailer IN ('amazon', 'ulta', 'sephora'));

CREATE TABLE searches (
    id         UUID PRIMARY KEY,
    query      TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE products (
    id              UUID PRIMARY KEY,
    retailer        TEXT NOT NULL CHECK (retailer IN ('amazon', 'ulta', 'sephora')),
    asin            TEXT NOT NULL,
    title           TEXT NOT NULL,
    brand           TEXT,
    detail_page_url TEXT,
    image_url       TEXT,
    status          TEXT NOT NULL DEFAULT 'collected' CHECK (status IN ('collected', 'extracting', 'partial')),
    search_id       UUID REFERENCES searches (id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT products_retailer_asin_key UNIQUE (retailer, asin)
);

CREATE INDEX products_search_id_idx ON products (search_id);
CREATE INDEX products_created_at_idx ON products (created_at DESC);

CREATE TABLE shades (
    id               UUID PRIMARY KEY,
    product_id       UUID NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    asin             TEXT NOT NULL,
    name             TEXT NOT NULL,
    swatch_url       TEXT,
    swatch_blob_name TEXT,
    hex              TEXT CHECK (hex ~ '^#[0-9A-F]{6}$'),
    hue              DOUBLE PRECISION CHECK (hue >= 0 AND hue <= 360),
    lightness        DOUBLE PRECISION CHECK (lightness >= 0 AND lightness <= 100),
    status           TEXT NOT NULL CHECK (status IN ('extracted', 'failed')),
    error            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT shades_product_asin_key UNIQUE (product_id, asin)
);

CREATE INDEX shades_product_name_idx ON shades (product_id, name);

CREATE TABLE color_maps (
    id         UUID PRIMARY KEY,
    blob_name  TEXT NOT NULL,
    width      INTEGER,
    height     INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX color_maps_created_at_idx ON color_maps (created_at DESC);

CREATE TABLE color_map_markers (
    id           UUID PRIMARY KEY,
    color_map_id UUID NOT NULL REFERENCES color_maps (id) ON DELETE CASCADE,
    shade_id     UUID NOT NULL REFERENCES shades (id) ON DELETE CASCADE,
    x            DOUBLE PRECISION NOT NULL CHECK (x >= 0 AND x <= 1),
    y            DOUBLE PRECISION NOT NULL CHECK (y >= 0 AND y <= 1),
    hex          TEXT NOT NULL CHECK (hex ~ '^#[0-9A-F]{6}$'),
    hue          DOUBLE PRECISION NOT NULL,
    lightness    DOUBLE PRECISION NOT NULL
);

CREATE INDEX color_map_markers_color_map_id_idx ON color_map_markers (color_map_id);
CREATE INDEX color_map_markers_shade_id_idx ON color_map_markers (shade_id);

ALTER TABLE color_maps ADD COLUMN shape TEXT NOT NULL DEFAULT 'rectangle'
    CHECK (shape IN ('rectangle', 'wheel'));

DROP INDEX color_maps_created_at_idx;
CREATE INDEX color_maps_shape_created_at_idx ON color_maps (shape, created_at DESC);

DROP INDEX color_maps_shape_created_at_idx;
CREATE INDEX color_maps_created_at_idx ON color_maps (created_at DESC);

DELETE FROM color_maps WHERE shape <> 'rectangle';
ALTER TABLE color_maps DROP COLUMN shape;

from io import BytesIO

import pytest
from PIL import Image

from src.models.domain import MapShade
from src.services.color_extractor import PillowColorExtractor
from src.services.color_map import ColorMapRenderer
from src.services.color_math import hex_to_hue_lightness, map_position, rgb_to_hex
from tests.conftest import IVORY, make_png


def test_hex_to_hue_lightness_for_pure_red():
    assert hex_to_hue_lightness("#FF0000") == (0.0, 50.0)


def test_hex_to_hue_lightness_rejects_malformed_hex():
    with pytest.raises(ValueError):
        hex_to_hue_lightness("F1D2B5")


def test_map_position_red_left_yellow_right():
    assert map_position(0, 50)[0] == 0.0
    assert map_position(30, 50)[0] == 0.5
    assert map_position(60, 50)[0] == 1.0
    assert map_position(120, 50)[0] == 1.0


def test_map_position_white_top_black_bottom():
    assert map_position(30, 100)[1] == 0.0
    assert map_position(30, 0)[1] == 1.0


def test_map_position_wraps_magenta_reds_to_red_edge():
    assert map_position(330, 50)[0] == 0.0


def test_extractor_returns_swatch_color():
    assert PillowColorExtractor().extract_hex(make_png(IVORY)) == rgb_to_hex(*IVORY)


def test_extractor_ignores_white_border():
    image = Image.new("RGB", (40, 40), (255, 255, 255))
    image.paste(Image.new("RGB", (30, 30), (122, 74, 50)), (5, 5))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    assert PillowColorExtractor().extract_hex(buffer.getvalue()) == "#7A4A32"


def test_extractor_rejects_non_images():
    with pytest.raises(ValueError):
        PillowColorExtractor().extract_hex(b"not an image")


def test_renderer_produces_png_of_configured_size():
    renderer = ColorMapRenderer(width=300, height=200)
    shade = MapShade("s1", "p1", "1N1", "Double Wear", "#F1D2B5", 28.0, 81.0)
    png = renderer.render(renderer.plot([shade]))
    image = Image.open(BytesIO(png))
    assert image.format == "PNG"
    assert image.size == (300, 200)


def test_renderer_plots_lighter_shades_higher():
    renderer = ColorMapRenderer()
    light = MapShade("s1", "p1", "light", "P", "#F1D2B5", 28.0, 81.0)
    dark = MapShade("s2", "p1", "dark", "P", "#4B2E22", 19.0, 21.0)
    plotted = renderer.plot([light, dark])
    assert plotted[0].y < plotted[1].y

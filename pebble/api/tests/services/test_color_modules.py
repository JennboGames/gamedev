from io import BytesIO

import pytest
from PIL import Image

from src.models.domain import MapShade
from src.services.color_extractor import PillowColorExtractor
from src.services.color_map import ColorMapRenderer
from src.services.color_math import (
    WHEEL_RADIUS,
    hex_to_hue_lightness,
    map_position,
    rgb_to_hex,
    wheel_position,
)
from src.services.color_wheel import ColorWheelRenderer
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


def test_wheel_position_puts_white_at_the_center():
    assert wheel_position(30, 100) == (0.5, 0.5)
    assert wheel_position(200, 100) == (0.5, 0.5)


def test_wheel_position_hue_is_the_angle_clockwise_from_the_top():
    x, y = wheel_position(0, 0)
    assert (x, round(y, 4)) == (0.5, round(0.5 - WHEEL_RADIUS, 4))
    x, y = wheel_position(90, 0)
    assert (round(x, 4), y) == (round(0.5 + WHEEL_RADIUS, 4), 0.5)
    x, y = wheel_position(180, 0)
    assert (x, round(y, 4)) == (0.5, round(0.5 + WHEEL_RADIUS, 4))


def test_wheel_position_darker_shades_sit_farther_from_the_center():
    light = wheel_position(28, 81)
    dark = wheel_position(28, 21)
    distance = lambda p: ((p[0] - 0.5) ** 2 + (p[1] - 0.5) ** 2) ** 0.5  # noqa: E731
    assert distance(light) < distance(dark) <= WHEEL_RADIUS


def test_wheel_renderer_produces_a_square_png_and_a_plain_surface_outside_the_rim():
    renderer = ColorWheelRenderer(size=300)
    shade = MapShade("s1", "p1", "1N1", "Double Wear", "#F1D2B5", 28.0, 81.0)
    image = Image.open(BytesIO(renderer.render(renderer.plot([shade]))))
    assert image.format == "PNG"
    assert image.size == (300, 300)
    assert image.getpixel((2, 2)) == (250, 246, 242)  # outside the rim
    assert image.getpixel((150, 150)) != (250, 246, 242)  # inside the wheel


@pytest.mark.parametrize("renderer", [ColorMapRenderer(300, 200), ColorWheelRenderer(300)])
def test_background_leaves_markers_to_the_web_app_but_the_full_image_has_them(renderer):
    shade = MapShade("s1", "p1", "1N1", "Double Wear", "#F1D2B5", 28.0, 81.0)
    marker = renderer.plot([shade])[0]
    point = (round(marker.x * (renderer.width - 1)), round(marker.y * (renderer.height - 1)))

    full = Image.open(BytesIO(renderer.render([marker]))).getpixel(point)
    background = Image.open(BytesIO(renderer.render_background())).getpixel(point)

    assert full == (241, 210, 181)
    assert background != full

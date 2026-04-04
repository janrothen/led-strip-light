#!/usr/bin/env python3

from unittest.mock import Mock

import werkzeug
from led.color import Color
from http_server import create_app


def _build_client():
    if not hasattr(werkzeug, "__version__"):
        werkzeug.__version__ = "patched-for-tests"

    led_controller = Mock()
    led_controller.is_sequence_running.return_value = False
    led_controller.is_on.return_value = False
    led_controller.get_color.return_value = Color.BLACK
    led_controller.get_brightness_percentage.return_value = 0

    effect_runner = Mock()

    app = create_app(
        config_manager=Mock(),
        led_controller=led_controller,
        profile_manager=Mock(),
        effect_runner=effect_runner,
    )
    app.testing = True
    return app.test_client(), led_controller, effect_runner


def test_list_effects_defaults():
    client, _, _ = _build_client()
    response = client.get("/effects")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["active"] is None
    assert "breathing" in payload["available"]


def test_start_breathing_effect():
    client, _, effect_runner = _build_client()
    response = client.post("/effects/breathing", json={"color": "00FF00", "duration": 1500})

    assert response.status_code == 200
    effect_runner.run_breathing_effect.assert_called_once_with(color=Color.GREEN, duration=1500)


def test_active_effect_clears_when_sequence_finishes():
    client, led_controller, _ = _build_client()
    start_response = client.post("/effects/random")
    assert start_response.status_code == 200

    led_controller.is_sequence_running.return_value = False
    response = client.get("/effects")
    payload = response.get_json()
    assert payload["active"] is None


def test_stop_effect_calls_controller_with_short_timeout():
    client, led_controller, _ = _build_client()
    led_controller.is_sequence_running.return_value = True

    response = client.post("/effects/stop")
    assert response.status_code == 200
    led_controller.stop_current_sequence.assert_called_once_with(timeout=2)


def test_cycle_requires_list_colors():
    client, _, _ = _build_client()
    response = client.post("/effects/cycle", json={"colors": "FF0000"})

    assert response.status_code == 400
    assert "colors must be a list" in response.get_json()["error"]


def test_unknown_effect_returns_404():
    client, _, _ = _build_client()
    response = client.post("/effects/not-real")

    assert response.status_code == 404
    assert "unknown effect" in response.get_json()["error"]

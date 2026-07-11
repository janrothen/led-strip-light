#!/usr/bin/env python3

from unittest.mock import Mock

import werkzeug

from http_server import create_app
from led.color import Color


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
    response = client.post(
        "/effects/breathing", json={"color": "00FF00", "duration": 1500}
    )

    assert response.status_code == 200
    effect_runner.run_breathing_effect.assert_called_once_with(
        color=Color.GREEN, duration=1500
    )


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


def test_turn_on_when_not_active():
    client, led_controller, _ = _build_client()
    led_controller.is_on.return_value = False
    led_controller.is_sequence_running.return_value = False

    response = client.post("/on")

    assert response.status_code == 200
    led_controller.switch_on.assert_called_once()


def test_turn_on_when_already_active():
    client, led_controller, _ = _build_client()
    led_controller.is_on.return_value = True

    response = client.post("/on")

    assert response.status_code == 200
    led_controller.switch_on.assert_not_called()


def test_turn_off():
    client, led_controller, _ = _build_client()
    led_controller.is_sequence_running.return_value = False

    response = client.post("/off")

    assert response.status_code == 200
    led_controller.switch_off.assert_called_once()


def test_get_status_when_on():
    client, led_controller, _ = _build_client()
    led_controller.is_on.return_value = True

    response = client.get("/status")

    assert response.status_code == 200
    assert response.data == b"1"


def test_get_status_when_off():
    client, led_controller, _ = _build_client()
    led_controller.is_on.return_value = False
    led_controller.is_sequence_running.return_value = False

    response = client.get("/status")

    assert response.status_code == 200
    assert response.data == b"0"


def test_get_color():
    client, led_controller, _ = _build_client()
    led_controller.get_display_color.return_value = Color(255, 0, 0)

    response = client.get("/color")

    assert response.status_code == 200
    assert response.data == b"#FF0000"


def test_get_color_when_off_returns_last_known_color():
    client, led_controller, _ = _build_client()
    led_controller.get_display_color.return_value = Color(
        255, 147, 41
    )  # WARM_YELLOW fallback

    response = client.get("/color")

    assert response.status_code == 200
    assert response.data == b"#FF9329"


def test_set_color():
    client, led_controller, _ = _build_client()
    led_controller.is_sequence_running.return_value = False

    response = client.post("/color/FF0000")

    assert response.status_code == 200
    led_controller.set_color.assert_called_once_with(Color(255, 0, 0))


def test_set_color_invalid_returns_400():
    client, led_controller, _ = _build_client()

    response = client.post("/color/notacolor")

    assert response.status_code == 400
    assert "Unknown color" in response.get_json()["error"]
    led_controller.set_color.assert_not_called()


def test_get_brightness():
    client, led_controller, _ = _build_client()
    led_controller.get_brightness_percentage.return_value = 75

    response = client.get("/brightness")

    assert response.status_code == 200
    assert response.data == b"75"


def test_set_brightness():
    client, led_controller, _ = _build_client()
    led_controller.is_sequence_running.return_value = False

    response = client.post("/brightness/80")

    assert response.status_code == 200
    led_controller.set_brightness.assert_called_once_with(80)


def test_set_brightness_out_of_range_returns_400():
    client, led_controller, _ = _build_client()
    led_controller.set_brightness.side_effect = ValueError(
        "Brightness must be between 0 and 100"
    )

    response = client.post("/brightness/150")

    assert response.status_code == 400
    assert "Brightness" in response.get_json()["error"]


def test_start_campfire_effect():
    client, _, effect_runner = _build_client()
    response = client.post("/effects/campfire", json={"duration": 5000})

    assert response.status_code == 200
    effect_runner.run_campfire_effect.assert_called_once()


def test_start_candle_effect():
    client, _, effect_runner = _build_client()
    response = client.post("/effects/candle")

    assert response.status_code == 200
    effect_runner.run_candle_effect.assert_called_once()


def test_start_aurora_effect_default():
    client, _, effect_runner = _build_client()
    response = client.post("/effects/aurora")

    assert response.status_code == 200
    effect_runner.run_aurora_effect.assert_called_once_with()


def test_start_aurora_effect_with_params():
    client, _, effect_runner = _build_client()
    response = client.post(
        "/effects/aurora",
        json={
            "duration": 60000,
            "update_hz": 30,
            "hue_min": 0.4,
            "hue_max": 0.7,
            "saturation": 0.8,
            "tau_ms": 3000,
            "gamma": 2.2,
        },
    )

    assert response.status_code == 200
    kwargs = effect_runner.run_aurora_effect.call_args[1]
    assert kwargs["duration"] == 60000
    assert kwargs["update_hz"] == 30
    assert kwargs["hue_min"] == 0.4
    assert kwargs["hue_max"] == 0.7
    assert kwargs["saturation"] == 0.8
    assert kwargs["tau_ms"] == 3000
    assert kwargs["gamma"] == 2.2


def test_list_effects_includes_aurora():
    client, _, _ = _build_client()
    payload = client.get("/effects").get_json()
    assert "aurora" in payload["available"]


def test_start_heartbeat_effect_default():
    client, _, effect_runner = _build_client()
    response = client.post("/effects/heartbeat")

    assert response.status_code == 200
    effect_runner.run_heartbeat_effect.assert_called_once_with(color=Color(255, 0, 0))


def test_start_heartbeat_effect_with_params():
    client, _, effect_runner = _build_client()
    response = client.post(
        "/effects/heartbeat",
        json={
            "color": "FF69B4",
            "beat_ms": 220,
            "gap_ms": 100,
            "rest_ms": 400,
            "second_beat_scale": 0.5,
        },
    )

    assert response.status_code == 200
    kwargs = effect_runner.run_heartbeat_effect.call_args[1]
    assert kwargs["color"] == Color(0xFF, 0x69, 0xB4)
    assert kwargs["beat_ms"] == 220
    assert kwargs["gap_ms"] == 100
    assert kwargs["rest_ms"] == 400
    assert kwargs["second_beat_scale"] == 0.5


def test_list_effects_includes_heartbeat():
    client, _, _ = _build_client()
    payload = client.get("/effects").get_json()
    assert "heartbeat" in payload["available"]


def test_start_rainbow_effect_default():
    client, _, effect_runner = _build_client()
    response = client.post("/effects/rainbow")

    assert response.status_code == 200
    effect_runner.run_rainbow_effect.assert_called_once_with()


def test_start_rainbow_effect_with_params():
    client, _, effect_runner = _build_client()
    response = client.post(
        "/effects/rainbow",
        json={
            "period_ms": 5000,
            "duration": 30000,
            "update_hz": 30,
            "saturation": 0.8,
            "brightness": 0.5,
            "gamma": 2.2,
        },
    )

    assert response.status_code == 200
    kwargs = effect_runner.run_rainbow_effect.call_args[1]
    assert kwargs["period_ms"] == 5000
    assert kwargs["duration"] == 30000
    assert kwargs["update_hz"] == 30
    assert kwargs["saturation"] == 0.8
    assert kwargs["brightness"] == 0.5
    assert kwargs["gamma"] == 2.2


def test_list_effects_includes_rainbow():
    client, _, _ = _build_client()
    payload = client.get("/effects").get_json()
    assert "rainbow" in payload["available"]


def test_start_lightning_effect_default():
    client, _, effect_runner = _build_client()
    response = client.post("/effects/lightning")

    assert response.status_code == 200
    effect_runner.run_lightning_effect.assert_called_once_with()


def test_start_lightning_effect_with_params():
    client, _, effect_runner = _build_client()
    response = client.post(
        "/effects/lightning",
        json={
            "flash_color": "00FFFF",
            "background_color": "0A0014",
            "min_gap_ms": 500,
            "max_gap_ms": 1500,
            "flash_ms": 80,
            "intensity_min": 0.4,
            "intensity_max": 0.9,
            "aftershock_chance": 0.3,
            "max_aftershocks": 1,
            "duration": 20000,
            "gamma": 2.2,
        },
    )

    assert response.status_code == 200
    kwargs = effect_runner.run_lightning_effect.call_args[1]
    assert kwargs["flash_color"] == Color(0, 255, 255)
    assert kwargs["background_color"] == Color(0x0A, 0x00, 0x14)
    assert kwargs["min_gap_ms"] == 500
    assert kwargs["max_gap_ms"] == 1500
    assert kwargs["flash_ms"] == 80
    assert kwargs["intensity_min"] == 0.4
    assert kwargs["intensity_max"] == 0.9
    assert kwargs["aftershock_chance"] == 0.3
    assert kwargs["max_aftershocks"] == 1
    assert kwargs["duration"] == 20000
    assert kwargs["gamma"] == 2.2


def test_list_effects_includes_lightning():
    client, _, _ = _build_client()
    payload = client.get("/effects").get_json()
    assert "lightning" in payload["available"]


def test_start_cycle_effect_with_colors_list():
    client, _, effect_runner = _build_client()
    response = client.post(
        "/effects/cycle", json={"colors": ["FF0000", "00FF00"], "duration": 1000}
    )

    assert response.status_code == 200
    call_kwargs = effect_runner.run_cycle_effect.call_args[1]
    assert len(call_kwargs["colors"]) == 2
    assert call_kwargs["duration"] == 1000


def test_start_fade_effect():
    client, _, effect_runner = _build_client()
    response = client.post(
        "/effects/fade", json={"from": "000000", "to": "FFFFFF", "duration": 3000}
    )

    assert response.status_code == 200
    effect_runner.run_fade_effect.assert_called_once_with(
        from_color=Color(0, 0, 0),
        to_color=Color(255, 255, 255),
        duration=3000,
    )


def test_start_profile_effect():
    client, _, effect_runner = _build_client()
    response = client.post("/effects/profile", json={"duration": 8000})

    assert response.status_code == 200
    effect_runner.run_profile_effect.assert_called_once_with(duration=8000)


def test_stop_effect_when_not_running():
    client, led_controller, _ = _build_client()
    led_controller.is_sequence_running.return_value = False

    response = client.post("/effects/stop")

    assert response.status_code == 200
    led_controller.stop_current_sequence.assert_not_called()


def test_stop_effect_timeout_is_swallowed():
    client, led_controller, _ = _build_client()
    led_controller.is_sequence_running.return_value = True
    led_controller.stop_current_sequence.side_effect = TimeoutError("stuck")

    response = client.post("/effects/stop")

    assert response.status_code == 200


def test_stop_effect_clears_name_even_on_timeout():
    client, led_controller, _ = _build_client()

    # Start an effect so active_effect["name"] is set
    led_controller.is_sequence_running.return_value = False
    client.post("/effects/random")

    # Now simulate a stuck sequence on stop
    led_controller.is_sequence_running.return_value = True
    led_controller.stop_current_sequence.side_effect = TimeoutError("stuck")

    client.post("/effects/stop")

    # Name must be cleared regardless of the timeout
    led_controller.is_sequence_running.return_value = False
    payload = client.get("/effects").get_json()
    assert payload["active"] is None


def test_start_effect_exception_returns_400():
    client, _, effect_runner = _build_client()
    effect_runner.run_breathing_effect.side_effect = ValueError("bad param")

    response = client.post("/effects/breathing", json={"color": "FF0000"})

    assert response.status_code == 400
    assert "bad param" in response.get_json()["error"]

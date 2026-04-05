#!/usr/bin/env python3

import os

from flask import Flask, Response, jsonify, request, send_from_directory

from config.config_manager import ConfigManager
from led.color import Color
from led.effect_runner import EffectRunner
from led.gpio_service import GPIOService
from led.led_strip_light_controller import LEDStripLightController
from led.profile_manager import ProfileManager

_FLAME_KEYS_INT = {"duration", "update_hz", "tau_ms"}
_FLAME_KEYS_FLOAT = {"min_brightness", "max_brightness", "hue_jitter", "saturation", "spark_chance", "spark_gain", "gamma"}
_FLAME_KEYS = [
    "duration",
    "update_hz",
    "min_brightness",
    "max_brightness",
    "hue_jitter",
    "saturation",
    "spark_chance",
    "spark_gain",
    "tau_ms",
    "gamma",
]


def _parse_color(value: str) -> Color:
    return Color.from_hex(value.lstrip("#"))


def _parse_flame_kwargs(data: dict) -> dict:
    kwargs = {}
    for k in _FLAME_KEYS:
        if k not in data:
            continue
        if k in _FLAME_KEYS_INT:
            kwargs[k] = int(data[k])
        elif k in _FLAME_KEYS_FLOAT:
            kwargs[k] = float(data[k])
    return kwargs


def _resolve_dependencies(
    config_manager, gpio_service, led_controller, profile_manager, effect_runner
):
    if config_manager is None:
        config_manager = ConfigManager()
    if led_controller is None:
        if gpio_service is None:
            pin_assignment = config_manager.get_pin_assignment()
            gpio_service = GPIOService(
                red_pin=pin_assignment.red,
                green_pin=pin_assignment.green,
                blue_pin=pin_assignment.blue,
            )
        led_controller = LEDStripLightController(gpio_service=gpio_service)
    if profile_manager is None:
        profile_manager = ProfileManager(config_manager)
    if effect_runner is None:
        effect_runner = EffectRunner(led_controller, profile_manager)
    return config_manager, led_controller, profile_manager, effect_runner


def _dispatch_effect(effect_name: str, data: dict, effect_runner: EffectRunner) -> None:
    if effect_name == "breathing":
        color_hex = data.get("color", "FF0000")
        duration = int(data.get("duration", 2000))
        effect_runner.run_breathing_effect(color=_parse_color(color_hex), duration=duration)
    elif effect_name == "campfire":
        effect_runner.run_campfire_effect(**_parse_flame_kwargs(data))
    elif effect_name == "candle":
        effect_runner.run_candle_effect(**_parse_flame_kwargs(data))
    elif effect_name == "random":
        interval = int(data.get("interval", 2000))
        effect_runner.run_random_effect(interval=interval)
    elif effect_name == "cycle":
        duration = int(data.get("duration", 2000))
        colors_raw = data.get("colors")
        colors = None
        if colors_raw:
            if not isinstance(colors_raw, list):
                raise ValueError("colors must be a list of hex strings")
            colors = [_parse_color(c) for c in colors_raw]
        effect_runner.run_cycle_effect(colors=colors, duration=duration)
    elif effect_name == "fade":
        from_hex = data.get("from", "000000")
        to_hex = data.get("to", "FFFFFF")
        duration = int(data.get("duration", 5000))
        effect_runner.run_fade_effect(
            from_color=_parse_color(from_hex),
            to_color=_parse_color(to_hex),
            duration=duration,
        )
    elif effect_name == "profile":
        duration = int(data.get("duration", 10000))
        effect_runner.run_profile_effect(duration=duration)
    else:
        raise KeyError(effect_name)


def create_app(
    *,
    config_manager: ConfigManager = None,
    gpio_service: GPIOService = None,
    led_controller: LEDStripLightController = None,
    profile_manager: ProfileManager = None,
    effect_runner: EffectRunner = None,
) -> Flask:
    # CSRF protection is not required: this API has no session cookies or
    # authentication, and all mutation endpoints consume JSON (not form data),
    # so cross-origin requests are blocked by browser CORS preflight.
    app = Flask(__name__, static_folder="static", static_url_path="")  # NOSONAR

    _, led_controller, _, effect_runner = _resolve_dependencies(
        config_manager, gpio_service, led_controller, profile_manager, effect_runner
    )

    active_effect = {"name": None}

    def _stop_active_effect() -> None:
        """Interrupt any running effect thread and clear active effect state."""
        if not led_controller.is_sequence_running():
            active_effect["name"] = None
            return

        try:
            led_controller.stop_current_sequence(timeout=2)
            active_effect["name"] = None
        except Exception:
            pass

    def _is_led_active() -> bool:
        return led_controller.is_on() or led_controller.is_sequence_running()

    def _get_active_effect_name():
        if not led_controller.is_sequence_running():
            active_effect["name"] = None
        return active_effect["name"]

    # --- Static controller file serving --------------------------------------
    @app.route("/", methods=["GET"])
    def index():
        return send_from_directory("static", "index.html")

    # --- Basic LED control endpoints -----------------------------------------
    @app.route("/on", methods=["POST"])
    def turn_on():
        if not _is_led_active():
            led_controller.switch_on()
        return Response(status=200)

    @app.route("/off", methods=["POST"])
    def turn_off():
        _stop_active_effect()
        led_controller.switch_off()
        return Response(status=200)

    @app.route("/status", methods=["GET"])
    def get_status():
        return Response("1" if _is_led_active() else "0", status=200)

    @app.route("/color", methods=["GET"])
    def get_color():
        hex_color = led_controller.get_color().to_hex_with_hash()
        return Response(hex_color, status=200)

    @app.route("/color/<value>", methods=["POST"])
    def set_color(value):
        _stop_active_effect()
        color = Color.from_hex(value)
        led_controller.set_color(color)
        return Response(status=200)

    @app.route("/brightness", methods=["GET"])
    def get_brightness():
        brightness = led_controller.get_brightness_percentage()
        return Response(str(brightness), status=200)

    @app.route("/brightness/<int:value>", methods=["POST"])
    def set_brightness(value):
        _stop_active_effect()
        led_controller.set_brightness(value)
        return Response(status=200)

    # --- Effect management ----------------------------------------------------
    @app.route("/effects", methods=["GET"])
    def list_effects():
        return jsonify(
            {
                "active": _get_active_effect_name(),
                "available": [
                    "breathing",
                    "campfire",
                    "candle",
                    "random",
                    "cycle",
                    "fade",
                    "profile",
                ],
            }
        )

    @app.route("/effects/stop", methods=["POST"])
    def stop_effect():
        _stop_active_effect()
        return jsonify({"status": "stopped"})

    @app.route("/effects/<effect_name>", methods=["POST"])
    def start_effect(effect_name: str):
        data = request.get_json(silent=True) or {}
        try:
            _dispatch_effect(effect_name, data, effect_runner)
        except KeyError:
            return jsonify({"error": f"unknown effect '{effect_name}'"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        active_effect["name"] = effect_name
        return jsonify({"status": "started", "effect": effect_name, "params": data})

    app.config["LED_CONTROLLER"] = led_controller
    app.config["EFFECT_RUNNER"] = effect_runner

    return app


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    create_app().run(host=host, port=port)

#!/usr/bin/env python3
"""Flask REST API entry point for the LED strip light controller.

Exposes endpoints for on/off, color, brightness, and named effects.
Use ``create_app()`` to get a configured Flask application instance;
all dependencies can be injected for testing without real hardware.
"""

import contextlib
import os
import signal
import threading
from collections.abc import Callable

from flask import Flask, Response, jsonify, request, send_from_directory
from waitress import serve

from config.config_manager import ConfigManager
from led.color import Color
from led.effect_runner import EffectRunner
from led.gpio_service import GPIOService
from led.led_strip_light_controller import LEDStripLightController
from led.profile_manager import ProfileManager

_FLAME_COERCERS = {
    "duration": int,
    "update_hz": int,
    "tau_ms": int,
    "min_brightness": float,
    "max_brightness": float,
    "hue_jitter": float,
    "saturation": float,
    "spark_chance": float,
    "spark_gain": float,
    "gamma": float,
}

_AURORA_COERCERS = {
    "duration": int,
    "update_hz": int,
    "tau_ms": int,
    "hue_min": float,
    "hue_max": float,
    "saturation": float,
    "min_brightness": float,
    "max_brightness": float,
    "hue_step": float,
    "brightness_step": float,
    "gamma": float,
}

_RAINBOW_COERCERS = {
    "period_ms": int,
    "duration": int,
    "update_hz": int,
    "saturation": float,
    "brightness": float,
    "gamma": float,
}

_LIGHTNING_COERCERS = {
    "min_gap_ms": int,
    "max_gap_ms": int,
    "flash_ms": int,
    "intensity_min": float,
    "intensity_max": float,
    "aftershock_chance": float,
    "max_aftershocks": int,
    "duration": int,
    "gamma": float,
}


def _is_led_active(led_controller) -> bool:
    return led_controller.is_on() or led_controller.is_sequence_running()


def _parse_flame_kwargs(data: dict) -> dict:
    return {k: coerce(data[k]) for k, coerce in _FLAME_COERCERS.items() if k in data}


def _parse_aurora_kwargs(data: dict) -> dict:
    return {k: coerce(data[k]) for k, coerce in _AURORA_COERCERS.items() if k in data}


def _parse_rainbow_kwargs(data: dict) -> dict:
    return {k: coerce(data[k]) for k, coerce in _RAINBOW_COERCERS.items() if k in data}


def _handle_lightning(runner: EffectRunner, data: dict) -> None:
    kwargs: dict = {
        k: coerce(data[k]) for k, coerce in _LIGHTNING_COERCERS.items() if k in data
    }
    if "flash_color" in data:
        kwargs["flash_color"] = Color.parse(data["flash_color"])
    if "background_color" in data:
        kwargs["background_color"] = Color.parse(data["background_color"])
    runner.run_lightning_effect(**kwargs)


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


def _handle_breathing(runner: EffectRunner, data: dict) -> None:
    runner.run_breathing_effect(
        color=Color.parse(data.get("color", "FF0000")),
        duration=int(data.get("duration", 2000)),
    )


def _handle_heartbeat(runner: EffectRunner, data: dict) -> None:
    kwargs: dict = {"color": Color.parse(data.get("color", "FF0000"))}
    if "beat_ms" in data:
        kwargs["beat_ms"] = int(data["beat_ms"])
    if "gap_ms" in data:
        kwargs["gap_ms"] = int(data["gap_ms"])
    if "rest_ms" in data:
        kwargs["rest_ms"] = int(data["rest_ms"])
    if "second_beat_scale" in data:
        kwargs["second_beat_scale"] = float(data["second_beat_scale"])
    runner.run_heartbeat_effect(**kwargs)


def _handle_random(runner: EffectRunner, data: dict) -> None:
    runner.run_random_effect(interval=int(data.get("interval", 2000)))


def _handle_cycle(runner: EffectRunner, data: dict) -> None:
    colors_raw = data.get("colors")
    colors = None
    if colors_raw:
        if not isinstance(colors_raw, list):
            raise ValueError("colors must be a list of hex strings")
        colors = [Color.parse(c) for c in colors_raw]
    runner.run_cycle_effect(colors=colors, duration=int(data.get("duration", 2000)))


def _handle_fade(runner: EffectRunner, data: dict) -> None:
    runner.run_fade_effect(
        from_color=Color.parse(data.get("from", "000000")),
        to_color=Color.parse(data.get("to", "FFFFFF")),
        duration=int(data.get("duration", 5000)),
    )


def _handle_profile(runner: EffectRunner, data: dict) -> None:
    runner.run_profile_effect(duration=int(data.get("duration", 10000)))


_EFFECT_HANDLERS: dict[str, Callable[[EffectRunner, dict], None]] = {
    "aurora": lambda r, d: r.run_aurora_effect(**_parse_aurora_kwargs(d)),
    "breathing": _handle_breathing,
    "campfire": lambda r, d: r.run_campfire_effect(**_parse_flame_kwargs(d)),
    "candle": lambda r, d: r.run_candle_effect(**_parse_flame_kwargs(d)),
    "cycle": _handle_cycle,
    "fade": _handle_fade,
    "heartbeat": _handle_heartbeat,
    "lightning": _handle_lightning,
    "profile": _handle_profile,
    "rainbow": lambda r, d: r.run_rainbow_effect(**_parse_rainbow_kwargs(d)),
    "random": _handle_random,
}


def _dispatch_effect(effect_name: str, data: dict, effect_runner: EffectRunner) -> None:
    try:
        handler = _EFFECT_HANDLERS[effect_name]
    except KeyError:
        raise KeyError(effect_name) from None
    handler(effect_runner, data)


def create_app(
    *,
    config_manager: ConfigManager | None = None,
    gpio_service: GPIOService | None = None,
    led_controller: LEDStripLightController | None = None,
    profile_manager: ProfileManager | None = None,
    effect_runner: EffectRunner | None = None,
) -> Flask:
    # Security posture: this API has no authentication or session cookies, so
    # classic credential-stealing CSRF does not apply. Note that CORS preflight
    # does NOT protect the mutating endpoints: POSTs without a body (/on, /off,
    # /color/<v>, /effects/<name>) are "simple" cross-origin requests, so any
    # web page the operator visits could trigger them (it cannot read the
    # response). The API is intended for a trusted LAN only — keep it behind
    # the firewall rules in deploy/ufw and never expose it to the internet.
    app = Flask(__name__, static_folder="static", static_url_path="")  # NOSONAR

    _, led_controller, _, effect_runner = _resolve_dependencies(
        config_manager, gpio_service, led_controller, profile_manager, effect_runner
    )

    active_effect = {"name": None}
    # Serializes (dispatch, name-write) and (stop, name-clear) so the
    # "currently active effect name" stays consistent with what the
    # controller is actually running when requests arrive concurrently.
    state_lock = threading.Lock()

    def _stop_active_effect() -> None:
        """Interrupt any running effect thread and clear active effect state."""
        with state_lock:
            active_effect["name"] = None
            if not led_controller.is_sequence_running():
                return
            # Interrupt is set; on timeout the worker stops on its own poll.
            with contextlib.suppress(TimeoutError):
                led_controller.stop_current_sequence(timeout=2)

    def _get_active_effect_name():
        with state_lock:
            if not led_controller.is_sequence_running():
                active_effect["name"] = None
            return active_effect["name"]

    # --- Static controller file serving --------------------------------------
    @app.route("/", methods=["GET"])
    def index():
        """Serve the web UI."""
        return send_from_directory("static", "index.html")

    # --- Basic LED control endpoints -----------------------------------------
    @app.route("/on", methods=["POST"])
    def turn_on():
        """Turn the strip on (restores last color). 200 on success."""
        if not _is_led_active(led_controller):
            led_controller.switch_on()
        return Response(status=200)

    @app.route("/off", methods=["POST"])
    def turn_off():
        """Stop any active effect and turn the strip off. 200 on success."""
        _stop_active_effect()
        led_controller.switch_off()
        return Response(status=200)

    @app.route("/status", methods=["GET"])
    def get_status():
        """Return '1' if the strip is on or an effect is running, '0' otherwise."""
        return Response("1" if _is_led_active(led_controller) else "0", status=200)

    @app.route("/color", methods=["GET"])
    def get_color():
        """Return the current color as a '#RRGGBB' hex string."""
        hex_color = led_controller.get_display_color().to_hex_with_hash()
        return Response(hex_color, status=200)

    @app.route("/color/<value>", methods=["POST"])
    def set_color(value):
        """Set the strip to a color (name or hex RRGGBB, with or without '#').

        200 on success, 400 for an unknown name or malformed hex value.
        """
        try:
            color = Color.parse(value)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        _stop_active_effect()
        led_controller.set_color(color)
        return Response(status=200)

    @app.route("/brightness", methods=["GET"])
    def get_brightness():
        """Return current brightness as an integer percentage (0–100)."""
        brightness = led_controller.get_brightness_percentage()
        return Response(str(brightness), status=200)

    @app.route("/brightness/<int:value>", methods=["POST"])
    def set_brightness(value):
        """Set brightness percentage (0–100), preserving hue. 400 if out of range."""
        _stop_active_effect()
        try:
            led_controller.set_brightness(value)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return Response(status=200)

    # --- Effect management ----------------------------------------------------
    @app.route("/effects", methods=["GET"])
    def list_effects():
        """Return active effect name and list of available effect names."""
        return jsonify(
            {
                "active": _get_active_effect_name(),
                "available": sorted(_EFFECT_HANDLERS),
            }
        )

    @app.route("/effects/stop", methods=["POST"])
    def stop_effect():
        """Stop any running effect. Returns {"status": "stopped"}."""
        _stop_active_effect()
        return jsonify({"status": "stopped"})

    @app.route("/effects/<effect_name>", methods=["POST"])
    def start_effect(effect_name: str):
        """Start a named effect with optional JSON body params.

        Returns {"status": "started", "effect": ..., "params": ...} on success.
        Returns 404 {"error": ...} for unknown effect names.
        Returns 400 {"error": ...} for invalid parameters.
        Returns 503 {"error": ...} if the previous effect refuses to stop.
        """
        data = request.get_json(silent=True) or {}
        with state_lock:
            try:
                _dispatch_effect(effect_name, data, effect_runner)
            except KeyError:
                return jsonify({"error": f"unknown effect '{effect_name}'"}), 404
            except (ValueError, TypeError) as e:
                return jsonify({"error": str(e)}), 400
            except TimeoutError:
                # The running effect did not stop in time; its interrupt flag
                # stays set, so it will exit on its next poll. Tell the client
                # to retry rather than reporting a server bug.
                return jsonify(
                    {"error": "previous effect is still stopping, retry shortly"}
                ), 503
            active_effect["name"] = effect_name
        return jsonify({"status": "started", "effect": effect_name, "params": data})

    app.config["LED_CONTROLLER"] = led_controller
    app.config["EFFECT_RUNNER"] = effect_runner

    return app


def _run_server(app: Flask, host: str, port: int) -> None:
    """Serve ``app`` with waitress until SIGTERM/SIGINT, then turn the strip off.

    waitress is a production WSGI server; Flask's built-in dev server is
    single-purpose debug tooling and warns against production use.

    systemd stops the unit with SIGTERM; without cleanup the pigpio daemon
    keeps the last PWM duty cycles and the LEDs stay lit after the service
    exits. Convert the signal to SystemExit so the finally-block runs.
    """

    def _terminate(signum: int, frame: object) -> None:
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _terminate)
    signal.signal(signal.SIGINT, _terminate)
    try:
        serve(app, host=host, port=port)
    finally:
        app.config["LED_CONTROLLER"].shutdown()


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    _run_server(create_app(), host, port)

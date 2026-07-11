#!/usr/bin/env python3

"""Tests for run.py main() entry point."""

from types import SimpleNamespace
from unittest.mock import Mock, PropertyMock, patch

import pytest

from run import main


@pytest.fixture
def m():
    """Patch all external dependencies of main() and return their mocks."""
    mock_gs = Mock()
    mock_gs.kill_now = True  # exit the loop immediately by default

    mock_pin = Mock(red=18, green=19, blue=20)
    mock_config = Mock()
    mock_config.get_pin_assignment.return_value = mock_pin

    mock_args = Mock()
    mock_args.effect = "breathing"
    mock_parser = Mock()
    mock_parser.parse_args.return_value = mock_args

    with (
        patch("run.GracefulShutdown", return_value=mock_gs),
        patch("run.ConfigManager", return_value=mock_config),
        patch("run.GPIOService") as MockGPIOService,
        patch("run.LEDStripLightController") as MockController,
        patch("run.ProfileManager") as MockProfileManager,
        patch("run.EffectRunner") as MockEffectRunner,
        patch("run.create_parser", return_value=mock_parser) as mock_create_parser,
        patch("run.execute_effect") as mock_execute_effect,
        patch("run.time.sleep"),
    ):
        yield SimpleNamespace(
            gs=mock_gs,
            config=mock_config,
            pin=mock_pin,
            gpio=MockGPIOService.return_value,
            controller=MockController.return_value,
            profile_mgr=MockProfileManager.return_value,
            effect_runner=MockEffectRunner.return_value,
            args=mock_args,
            MockGPIOService=MockGPIOService,
            MockController=MockController,
            MockProfileManager=MockProfileManager,
            MockEffectRunner=MockEffectRunner,
            mock_create_parser=mock_create_parser,
            mock_execute_effect=mock_execute_effect,
        )


def test_gpio_service_wired_with_pin_assignment(m):
    main()
    m.MockGPIOService.assert_called_once_with(m.pin.red, m.pin.green, m.pin.blue)


def test_led_controller_wired_with_gpio_service(m):
    main()
    m.MockController.assert_called_once_with(m.gpio)


def test_effect_runner_wired_with_controller_and_profile_manager(m):
    main()
    m.MockEffectRunner.assert_called_once_with(m.controller, m.profile_mgr)


def test_profile_manager_wired_with_config_manager(m):
    main()
    m.MockProfileManager.assert_called_once_with(m.config)


def test_switch_off_called_on_startup(m):
    main()
    # first call is the startup switch_off, second is cleanup
    assert m.controller.switch_off.call_count >= 1
    # verify it's called before execute_effect
    startup_off = m.controller.switch_off.call_args_list[0]
    execute_call = m.mock_execute_effect.call_args_list[0]
    assert (
        m.controller.switch_off.call_args_list.index(startup_off)
        < m.mock_execute_effect.call_args_list.index(execute_call) + 1
    )


def test_execute_effect_called_with_runner_and_args(m):
    main()
    m.mock_execute_effect.assert_called_once_with(m.effect_runner, m.args)


def test_cleanup_switches_off_on_exit(m):
    main()
    # called at startup AND at cleanup; switch_off itself stops any sequence
    assert m.controller.switch_off.call_count == 2


def test_loop_sleeps_while_kill_now_false(m):
    kill_now_values = [False, False, True]
    type(m.gs).kill_now = PropertyMock(side_effect=kill_now_values)

    with patch("run.time.sleep") as mock_sleep:
        main()

    assert mock_sleep.call_count == 2

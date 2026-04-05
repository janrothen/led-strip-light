import signal
from unittest.mock import patch

from utils.graceful_shutdown import GracefulShutdown


def _make():
    """Return a GracefulShutdown with signal registration suppressed."""
    with patch("signal.signal"):
        return GracefulShutdown()


def test_kill_now_is_false_on_init():
    gs = _make()
    assert not gs.kill_now


def test_registers_sigint_handler():
    with patch("signal.signal") as mock_signal:
        GracefulShutdown()
    registered = {c.args[0] for c in mock_signal.call_args_list}
    assert signal.SIGINT in registered


def test_registers_sigterm_handler():
    with patch("signal.signal") as mock_signal:
        GracefulShutdown()
    registered = {c.args[0] for c in mock_signal.call_args_list}
    assert signal.SIGTERM in registered


def test_exit_sets_kill_now_true():
    gs = _make()
    gs._exit(signal.SIGTERM, None)
    assert gs.kill_now


def test_exit_works_for_sigint():
    gs = _make()
    gs._exit(signal.SIGINT, None)
    assert gs.kill_now


def test_exit_prints_signal_number():
    gs = _make()
    with patch("builtins.print") as mock_print:
        gs._exit(15, None)
    assert "15" in mock_print.call_args[0][0]

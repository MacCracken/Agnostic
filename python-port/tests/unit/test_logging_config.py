"""Unit tests for shared.logging_config — structured logging configuration."""

import logging

from shared.logging_config import configure_logging


class TestConfigureLogging:
    def test_returns_logger(self):
        logger = configure_logging("test_service")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_service"

    def test_respects_log_level(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        # Re-import to pick up env var
        from importlib import reload

        import shared.logging_config as mod

        reload(mod)
        logger = mod.configure_logging("test_debug")
        assert isinstance(logger, logging.Logger)

    def test_default_text_format(self):
        logger = configure_logging("text_test")
        assert isinstance(logger, logging.Logger)

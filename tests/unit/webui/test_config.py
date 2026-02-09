"""Tests for webui config module."""

import json
import os
import tempfile
from unittest.mock import patch

from mcpbridge_wrapper.webui.config import _DEFAULTS, WebUIConfig


class TestWebUIConfig:
    """Test WebUIConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = WebUIConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 8080
        assert config.auth_enabled is False
        assert config.auth_username == "admin"
        assert config.auth_password == "changeme"
        assert config.metrics_window_seconds == 3600
        assert config.metrics_max_datapoints == 3600
        assert config.audit_enabled is True
        assert config.audit_log_dir == "logs/audit"
        assert config.audit_max_file_size_mb == 10.0
        assert config.audit_max_files == 10
        assert config.dashboard_refresh_interval_ms == 1000
        assert config.chart_history_seconds == 300

    def test_config_from_file(self):
        """Test loading configuration from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"port": 9090, "host": "0.0.0.0"}, f)
            temp_path = f.name

        try:
            config = WebUIConfig(config_path=temp_path)
            assert config.port == 9090
            assert config.host == "0.0.0.0"
            # Other values should be defaults
            assert config.auth_enabled is False
        finally:
            os.unlink(temp_path)

    def test_config_merge_nested(self):
        """Test nested dictionary merging."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"auth": {"enabled": True, "username": "testuser"}}, f)
            temp_path = f.name

        try:
            config = WebUIConfig(config_path=temp_path)
            assert config.auth_enabled is True
            assert config.auth_username == "testuser"
            # Password should remain default
            assert config.auth_password == "changeme"
        finally:
            os.unlink(temp_path)

    def test_env_override_host(self):
        """Test environment variable override for host."""
        with patch.dict(os.environ, {"WEBUI_HOST": "192.168.1.1"}):
            config = WebUIConfig()
            assert config.host == "192.168.1.1"

    def test_env_override_port(self):
        """Test environment variable override for port."""
        with patch.dict(os.environ, {"WEBUI_PORT": "9000"}):
            config = WebUIConfig()
            assert config.port == 9000

    def test_env_override_auth_enabled(self):
        """Test environment variable override for auth enabled."""
        with patch.dict(os.environ, {"WEBUI_AUTH_ENABLED": "true"}):
            config = WebUIConfig()
            assert config.auth_enabled is True

        with patch.dict(os.environ, {"WEBUI_AUTH_ENABLED": "1"}):
            config = WebUIConfig()
            assert config.auth_enabled is True

        with patch.dict(os.environ, {"WEBUI_AUTH_ENABLED": "yes"}):
            config = WebUIConfig()
            assert config.auth_enabled is True

    def test_env_override_auth_credentials(self):
        """Test environment variable override for auth credentials."""
        env = {"WEBUI_AUTH_USERNAME": "admin2", "WEBUI_AUTH_PASSWORD": "secret"}
        with patch.dict(os.environ, env):
            config = WebUIConfig()
            assert config.auth_username == "admin2"
            assert config.auth_password == "secret"

    def test_to_dict_masks_password(self):
        """Test that to_dict masks the password."""
        config = WebUIConfig()
        data = config.to_dict()
        assert data["auth"]["password"] == "********"

    def test_invalid_config_file_ignored(self):
        """Test that invalid config file is ignored."""
        config = WebUIConfig(config_path="/nonexistent/path/config.json")
        # Should use defaults
        assert config.port == 8080

    def test_merge_does_not_affect_original_defaults(self):
        """Test that merging doesn't modify original defaults."""
        original_defaults = json.loads(json.dumps(_DEFAULTS))
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"port": 9999}, f)
            temp_path = f.name

        try:
            _ = WebUIConfig(config_path=temp_path)
            # Original defaults should be unchanged
            assert _DEFAULTS["port"] == original_defaults["port"]
        finally:
            os.unlink(temp_path)

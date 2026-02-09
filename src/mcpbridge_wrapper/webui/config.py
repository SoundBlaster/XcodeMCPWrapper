"""Configuration management for the XcodeMCPWrapper web dashboard.

Handles loading, validation, and defaults for all web UI settings
including server, authentication, metrics, and audit configuration.
"""

import json
import os
from typing import Any, Dict, Optional

_DEFAULTS: Dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 8080,
    "auth": {
        "enabled": False,
        "username": "admin",
        "password": "changeme",
    },
    "metrics": {
        "window_seconds": 3600,
        "max_datapoints": 3600,
    },
    "audit": {
        "enabled": True,
        "log_dir": "logs/audit",
        "max_file_size_mb": 10.0,
        "max_files": 10,
    },
    "dashboard": {
        "refresh_interval_ms": 1000,
        "chart_history_seconds": 300,
    },
}


class WebUIConfig:
    """Configuration container for the web dashboard.

    Loads settings from a JSON file with fallback to defaults.
    Supports environment variable overrides for host, port, and auth.

    Args:
        config_path: Path to a JSON configuration file.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize configuration from file and/or defaults.

        Args:
            config_path: Optional path to JSON config file.
        """
        self._data: Dict[str, Any] = json.loads(json.dumps(_DEFAULTS))

        if config_path and os.path.isfile(config_path):
            with open(config_path, encoding="utf-8") as f:
                user_config = json.load(f)
            self._merge(self._data, user_config)

        # Environment variable overrides
        env_host = os.environ.get("WEBUI_HOST")
        if env_host:
            self._data["host"] = env_host

        env_port = os.environ.get("WEBUI_PORT")
        if env_port:
            self._data["port"] = int(env_port)

        env_auth = os.environ.get("WEBUI_AUTH_ENABLED")
        if env_auth is not None:
            self._data["auth"]["enabled"] = env_auth.lower() in ("1", "true", "yes")

        env_user = os.environ.get("WEBUI_AUTH_USERNAME")
        if env_user:
            self._data["auth"]["username"] = env_user

        env_pass = os.environ.get("WEBUI_AUTH_PASSWORD")
        if env_pass:
            self._data["auth"]["password"] = env_pass

    @staticmethod
    def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge override dict into base dict.

        Args:
            base: Base dictionary (modified in place).
            override: Override dictionary.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                WebUIConfig._merge(base[key], value)
            else:
                base[key] = value

    @property
    def host(self) -> str:
        """Server bind host address."""
        return str(self._data["host"])

    @property
    def port(self) -> int:
        """Server bind port."""
        return int(self._data["port"])

    @property
    def auth_enabled(self) -> bool:
        """Whether authentication is required."""
        return bool(self._data["auth"]["enabled"])

    @property
    def auth_username(self) -> str:
        """Authentication username."""
        return str(self._data["auth"]["username"])

    @property
    def auth_password(self) -> str:
        """Authentication password."""
        return str(self._data["auth"]["password"])

    @property
    def metrics_window_seconds(self) -> int:
        """Metrics rolling window duration in seconds."""
        return int(self._data["metrics"]["window_seconds"])

    @property
    def metrics_max_datapoints(self) -> int:
        """Maximum metrics data points per time-series."""
        return int(self._data["metrics"]["max_datapoints"])

    @property
    def audit_enabled(self) -> bool:
        """Whether audit logging is enabled."""
        return bool(self._data["audit"]["enabled"])

    @property
    def audit_log_dir(self) -> str:
        """Directory for audit log files."""
        return str(self._data["audit"]["log_dir"])

    @property
    def audit_max_file_size_mb(self) -> float:
        """Maximum audit log file size in megabytes."""
        return float(self._data["audit"]["max_file_size_mb"])

    @property
    def audit_max_files(self) -> int:
        """Maximum number of audit log files to retain."""
        return int(self._data["audit"]["max_files"])

    @property
    def dashboard_refresh_interval_ms(self) -> int:
        """Dashboard refresh interval in milliseconds."""
        return int(self._data["dashboard"]["refresh_interval_ms"])

    @property
    def chart_history_seconds(self) -> int:
        """Number of seconds of chart history to display."""
        return int(self._data["dashboard"]["chart_history_seconds"])

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary (with password masked).

        Returns:
            Configuration dictionary with sensitive values masked.
        """
        result: Dict[str, Any] = json.loads(json.dumps(self._data))
        if result.get("auth", {}).get("password"):
            result["auth"]["password"] = "********"
        return result

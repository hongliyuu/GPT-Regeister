import os
import random
from pathlib import Path
from typing import Any

import yaml

from config.browser import (
    IMPERSONATE as DEFAULT_IMPERSONATE,
    REQUEST_TIMEOUT as DEFAULT_REQUEST_TIMEOUT,
    SEC_CH_UA as DEFAULT_SEC_CH_UA,
    SEC_CH_UA_MOBILE as DEFAULT_SEC_CH_UA_MOBILE,
    SEC_CH_UA_PLATFORM as DEFAULT_SEC_CH_UA_PLATFORM,
    USER_AGENT as DEFAULT_USER_AGENT,
)
from config.openai_protocol import (
    OPENAI_AUDIENCE as DEFAULT_OPENAI_AUDIENCE,
    OPENAI_CLIENT_ID as DEFAULT_OPENAI_CLIENT_ID,
    OPENAI_REDIRECT_URI as DEFAULT_OPENAI_REDIRECT_URI,
    OPENAI_SCOPE as DEFAULT_OPENAI_SCOPE,
    SENTINEL_SV as DEFAULT_SENTINEL_SV,
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"

_config_cache: dict | None = None
_config_mtime: float = 0

_DEFAULT_CONFIG = {
    "register": {
        "email": "",
        "password": "",
        "name": "",
        "birthday": "2000-01-01",
        "runs": 1,
        "workers": 1,
        "continue_on_fail": False,
    },
    "email": {
        "provider": "imap",
        "use_email_service": True,
        "email_source": "imap",
        "outlook": {
            "api_base": "https://mail.chatai.codes",
            "accounts": [],
        },
        "imap": {
            "login_email": "",
            "login_password": "",
            "accounts": [],
            "host": "imap.2925.com",
            "port": 993,
            "ssl": True,
            "mailbox": "INBOX",
            "alias_mode": "append_random",
            "alias_domain_mode": "default",
            "alias_domain": "",
            "alias_random_length": 6,
            "alias_separator": "",
        },
        "otp": {
            "poll_interval": 3,
            "max_wait": 90,
            "settle_seconds": 5,
        },
    },
    "proxy": {
        "pool": [],
    },
    "twofa": {
        "enabled": False,
    },
    "flow_trigger": {
        "enabled": True,
        "url": "",
        "bearer": "",
        "cookie": "",
        "payload": {
            "action": "chat",
        },
        "timeout": 30,
    },
}


def _write_default_config() -> dict:
    data = yaml.safe_load(yaml.dump(_DEFAULT_CONFIG, allow_unicode=True, sort_keys=False)) or {}
    _CONFIG_PATH.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return data



def _load_yaml() -> dict:
    global _config_cache, _config_mtime
    if not _CONFIG_PATH.exists():
        _config_cache = _write_default_config()
        _config_mtime = _CONFIG_PATH.stat().st_mtime
        return _config_cache

    mtime = _CONFIG_PATH.stat().st_mtime
    if _config_cache is not None and mtime == _config_mtime:
        return _config_cache

    raw = _CONFIG_PATH.read_text(encoding="utf-8")
    _config_cache = yaml.safe_load(raw) or {}
    _config_mtime = mtime
    return _config_cache


def _env(key: str, default: Any = None) -> Any:
    return os.environ.get(key, default)


def invalidate_cache() -> None:
    global _config_cache, _config_mtime
    _config_cache = None
    _config_mtime = 0


def save_yaml(data: dict) -> None:
    global _config_cache, _config_mtime
    _CONFIG_PATH.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    _config_cache = data
    _config_mtime = _CONFIG_PATH.stat().st_mtime


def get_full_config() -> dict:
    return _load_yaml()


# ============================================================
# 浏览器配置
# ============================================================

USER_AGENT: str = _env("USER_AGENT", DEFAULT_USER_AGENT)
SEC_CH_UA: str = _env("SEC_CH_UA", DEFAULT_SEC_CH_UA)
SEC_CH_UA_PLATFORM: str = _env("SEC_CH_UA_PLATFORM", DEFAULT_SEC_CH_UA_PLATFORM)
SEC_CH_UA_MOBILE: str = _env("SEC_CH_UA_MOBILE", DEFAULT_SEC_CH_UA_MOBILE)
IMPERSONATE: str = _env("IMPERSONATE", DEFAULT_IMPERSONATE)
REQUEST_TIMEOUT: int = int(_env("REQUEST_TIMEOUT", _load_yaml().get("network", {}).get("request_timeout", DEFAULT_REQUEST_TIMEOUT)))

# ============================================================
# OpenAI 协议配置
# ============================================================

OPENAI_CLIENT_ID: str = _env("OPENAI_CLIENT_ID", DEFAULT_OPENAI_CLIENT_ID)
OPENAI_SCOPE: str = _env("OPENAI_SCOPE", DEFAULT_OPENAI_SCOPE)
OPENAI_AUDIENCE: str = _env("OPENAI_AUDIENCE", DEFAULT_OPENAI_AUDIENCE)
OPENAI_REDIRECT_URI: str = _env("OPENAI_REDIRECT_URI", DEFAULT_OPENAI_REDIRECT_URI)
SENTINEL_SV: str = _env("SENTINEL_SV", DEFAULT_SENTINEL_SV)

# ============================================================
# 代理池
# ============================================================

PROXY_POOL: list = _load_yaml().get("proxy", {}).get("pool", [])


def pick_proxy() -> str:
    return random.choice(PROXY_POOL) if PROXY_POOL else ""


PROXY: str = pick_proxy()

# ============================================================
# 注册默认信息
# ============================================================

REGISTER_EMAIL: str = _env("REGISTER_EMAIL", _load_yaml().get("register", {}).get("email", ""))
REGISTER_PASSWORD: str = _env("REGISTER_PASSWORD", _load_yaml().get("register", {}).get("password", ""))
REGISTER_NAME: str = _env("REGISTER_NAME", _load_yaml().get("register", {}).get("name", ""))
REGISTER_BIRTHDAY: str = _env("REGISTER_BIRTHDAY", _load_yaml().get("register", {}).get("birthday", "2000-01-01"))

# ============================================================
# 邮箱配置
# ============================================================

EMAIL_PROVIDER: str = _env("EMAIL_PROVIDER", _load_yaml().get("email", {}).get("provider", "imap"))
USE_EMAIL_SERVICE: bool = EMAIL_PROVIDER != "manual"
EMAIL_SOURCE: str = EMAIL_PROVIDER

OUTLOOK_API_BASE: str = _load_yaml().get("email", {}).get("outlook", {}).get("api_base", "")
OUTLOOK_ACCOUNTS: list = _load_yaml().get("email", {}).get("outlook", {}).get("accounts", [])

IMAP_LOGIN_EMAIL: str = _load_yaml().get("email", {}).get("imap", {}).get("login_email", "")
IMAP_LOGIN_PASSWORD: str = _load_yaml().get("email", {}).get("imap", {}).get("login_password", "")
IMAP_DEFAULT_HOST: str = _load_yaml().get("email", {}).get("imap", {}).get("host", "imap.2925.com")
IMAP_DEFAULT_PORT: int = _load_yaml().get("email", {}).get("imap", {}).get("port", 993)
IMAP_DEFAULT_SSL: bool = _load_yaml().get("email", {}).get("imap", {}).get("ssl", True)
IMAP_MAILBOX: str = _load_yaml().get("email", {}).get("imap", {}).get("mailbox", "INBOX")
IMAP_ALIAS_ENABLED: bool = True
IMAP_ALIAS_MODE: str = _load_yaml().get("email", {}).get("imap", {}).get("alias_mode", "append_random")
IMAP_ALIAS_DOMAIN_MODE: str = _load_yaml().get("email", {}).get("imap", {}).get("alias_domain_mode", "default")
IMAP_ALIAS_DOMAIN: str = _load_yaml().get("email", {}).get("imap", {}).get("alias_domain", "")
IMAP_ALIAS_RANDOM_LENGTH: int = _load_yaml().get("email", {}).get("imap", {}).get("alias_random_length", 6)
IMAP_ALIAS_SEPARATOR: str = _load_yaml().get("email", {}).get("imap", {}).get("alias_separator", "")
IMAP_ACCOUNTS: list = _load_yaml().get("email", {}).get("imap", {}).get("accounts", [])

OTP_POLL_INTERVAL: int = _load_yaml().get("email", {}).get("otp", {}).get("poll_interval", 3)
OTP_MAX_WAIT: int = _load_yaml().get("email", {}).get("otp", {}).get("max_wait", 90)
OTP_SETTLE_SECONDS: int = _load_yaml().get("email", {}).get("otp", {}).get("settle_seconds", 5)

# ============================================================
# 2FA 配置
# ============================================================

ENABLE_2FA: bool = _load_yaml().get("twofa", {}).get("enabled", False)

# ============================================================
# Flow Trigger 配置
# ============================================================

ENABLE_FLOW_TRIGGER: bool = _load_yaml().get("flow_trigger", {}).get("enabled", True)
FLOW_TRIGGER_URL: str = _load_yaml().get("flow_trigger", {}).get("url", "")
FLOW_TRIGGER_BEARER: str = _load_yaml().get("flow_trigger", {}).get("bearer", "")
FLOW_TRIGGER_COOKIE: str = _load_yaml().get("flow_trigger", {}).get("cookie", "")
FLOW_TRIGGER_PAYLOAD: dict = _load_yaml().get("flow_trigger", {}).get("payload", {})
FLOW_TRIGGER_TIMEOUT: int = _load_yaml().get("flow_trigger", {}).get("timeout", 30)

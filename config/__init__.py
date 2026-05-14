# -*- coding: utf-8 -*-
"""
config 包的统一入口。

所有配置项统一由 config.yaml 驱动，通过 config.loader 加载。
支持环境变量覆盖（前缀同名大写变量，如 USER_AGENT）。

旧用法完全兼容：
    from config import USER_AGENT
    from config.proxy import pick_proxy
    from config.email import EMAIL_SOURCE

子模块（保留原有文件内容仅供参考，实际加载已转向 loader）：
    config.loader             YAML 加载器 + 环境变量覆盖 + 自动类型推断
    config.browser           浏览器指纹 / curl_cffi impersonate / HTTP 超时
    config.openai_protocol   OpenAI OAuth 固定参数 / Sentinel 版本
    config.proxy             代理池 + 随机抽取
    config.register          注册默认信息（邮箱、密码、名称、生日）
    config.email             Outlook 邮箱账号池 + OTP 轮询
    config.twofa             2FA 开关
"""

from config.loader import (
    USER_AGENT,
    SEC_CH_UA,
    SEC_CH_UA_PLATFORM,
    SEC_CH_UA_MOBILE,
    IMPERSONATE,
    REQUEST_TIMEOUT,
    OPENAI_CLIENT_ID,
    OPENAI_SCOPE,
    OPENAI_AUDIENCE,
    OPENAI_REDIRECT_URI,
    SENTINEL_SV,
    PROXY_POOL,
    pick_proxy,
    PROXY,
    REGISTER_EMAIL,
    REGISTER_PASSWORD,
    REGISTER_NAME,
    REGISTER_BIRTHDAY,
    EMAIL_PROVIDER,
    USE_EMAIL_SERVICE,
    EMAIL_SOURCE,
    OUTLOOK_API_BASE,
    OUTLOOK_ACCOUNTS,
    IMAP_LOGIN_EMAIL,
    IMAP_LOGIN_PASSWORD,
    IMAP_STATE_FILE,
    IMAP_DEFAULT_HOST,
    IMAP_DEFAULT_PORT,
    IMAP_DEFAULT_SSL,
    IMAP_MAILBOX,
    IMAP_ALIAS_ENABLED, IMAP_ALIAS_MODE, IMAP_ALIAS_DOMAIN_MODE, IMAP_ALIAS_DOMAIN, IMAP_ALIAS_RANDOM_LENGTH, IMAP_ALIAS_SEPARATOR, IMAP_ACCOUNTS,
    OTP_POLL_INTERVAL,
    OTP_MAX_WAIT,
    OTP_SETTLE_SECONDS,
    ENABLE_2FA,
    ENABLE_FLOW_TRIGGER,
    FLOW_TRIGGER_URL,
    FLOW_TRIGGER_BEARER,
    FLOW_TRIGGER_COOKIE,
    FLOW_TRIGGER_PAYLOAD,
    FLOW_TRIGGER_TIMEOUT,
    get_full_config,
    save_yaml,
    invalidate_cache,
)


__all__ = [
    "USER_AGENT", "SEC_CH_UA", "SEC_CH_UA_PLATFORM", "SEC_CH_UA_MOBILE",
    "IMPERSONATE", "REQUEST_TIMEOUT",
    "OPENAI_CLIENT_ID", "OPENAI_SCOPE", "OPENAI_AUDIENCE", "OPENAI_REDIRECT_URI",
    "SENTINEL_SV",
    "PROXY_POOL", "pick_proxy", "PROXY",
    "REGISTER_EMAIL", "REGISTER_PASSWORD", "REGISTER_NAME", "REGISTER_BIRTHDAY",
    "EMAIL_PROVIDER", "USE_EMAIL_SERVICE", "EMAIL_SOURCE",
    "OUTLOOK_API_BASE", "OUTLOOK_ACCOUNTS",
    "IMAP_LOGIN_EMAIL", "IMAP_LOGIN_PASSWORD",
    "IMAP_STATE_FILE",
    "IMAP_DEFAULT_HOST", "IMAP_DEFAULT_PORT", "IMAP_DEFAULT_SSL", "IMAP_MAILBOX",
    "IMAP_ALIAS_ENABLED", "IMAP_ALIAS_MODE", "IMAP_ALIAS_DOMAIN_MODE", "IMAP_ALIAS_DOMAIN", "IMAP_ALIAS_RANDOM_LENGTH", "IMAP_ALIAS_SEPARATOR", "IMAP_ACCOUNTS",
    "OTP_POLL_INTERVAL", "OTP_MAX_WAIT", "OTP_SETTLE_SECONDS",
    "ENABLE_2FA",
    "ENABLE_FLOW_TRIGGER", "FLOW_TRIGGER_URL", "FLOW_TRIGGER_BEARER",
    "FLOW_TRIGGER_COOKIE", "FLOW_TRIGGER_PAYLOAD", "FLOW_TRIGGER_TIMEOUT",
    "get_full_config", "save_yaml", "invalidate_cache",
]

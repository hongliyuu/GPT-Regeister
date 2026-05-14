# -*- coding: utf-8 -*-
"""
邮箱 Provider 总配置。

EMAIL_PROVIDER 可选值：
    - outlook_oauth：Outlook clientId + refreshToken 模式
    - imap：通用 IMAP 邮箱模式，适合 2925 / 企业邮箱 / 自建邮箱
    - manual：手动输入邮箱和验证码

通用 IMAP 邮箱素材格式：
    email----password
    email----password----imap_host
    email----password----imap_host----imap_port
    email----password----imap_host----imap_port----ssl

2925 示例：
    user@2925.com----邮箱密码
    user@2925.com----邮箱密码----imap.2925.com----993----true
"""

EMAIL_PROVIDER = "imap"
USE_EMAIL_SERVICE = EMAIL_PROVIDER != "manual"
EMAIL_SOURCE = EMAIL_PROVIDER


# ============================================================
# Outlook OAuth 模式（外购账号池 + 取信服务）
# ============================================================

OUTLOOK_API_BASE = "https://mail.chatai.codes"


# ============================================================
# 通用 IMAP 模式（默认按 2925 邮箱配置）
# ============================================================

IMAP_DEFAULT_HOST = "imap.2925.com"
IMAP_DEFAULT_PORT = 993
IMAP_DEFAULT_SSL = True
IMAP_MAILBOX = "INBOX"

IMAP_ALIAS_ENABLED = True
IMAP_ALIAS_MODE = "append_random"
IMAP_ALIAS_DOMAIN_MODE = "default"
IMAP_ALIAS_DOMAIN = ""
IMAP_ALIAS_RANDOM_LENGTH = 6
IMAP_ALIAS_SEPARATOR = ""


# ============================================================
# OTP 轮询参数
# ============================================================

OTP_POLL_INTERVAL = 3
OTP_MAX_WAIT = 90
OTP_SETTLE_SECONDS = 5

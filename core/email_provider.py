# -*- coding: utf-8 -*-
"""
邮箱来源调度层。

根据 config.EMAIL_PROVIDER 分发到不同邮箱实现：
    - outlook_oauth：Outlook clientId + refreshToken
    - imap：通用 IMAP 邮箱，默认适配 2925
    - manual：手动模式，不自动领取和取码
"""
import logging

from config import EMAIL_PROVIDER

logger = logging.getLogger(__name__)


def acquire_email() -> str:
    """按当前邮箱 Provider 领取一个用于注册的邮箱地址。"""
    if EMAIL_PROVIDER == "outlook_oauth":
        from core.outlook_client import pick_account
        account = pick_account()
        return account.email

    if EMAIL_PROVIDER == "imap":
        from core.imap_client import pick_account
        account = pick_account()
        return account.email

    raise RuntimeError(f"当前 EMAIL_PROVIDER={EMAIL_PROVIDER!r} 不支持自动领取邮箱")


def wait_for_otp(
    email: str,
    after_ts: float,
    settle_seconds: int | None = None,
    poll_interval: int | None = None,
) -> str:
    """
    等待并返回该邮箱最新的 ChatGPT OTP（6 位数字字符串）。

    Args:
        email: 目标邮箱
        after_ts: UTC 时间戳，只看比这更新的邮件，避免取到旧 OTP
    """
    if EMAIL_PROVIDER == "outlook_oauth":
        from core.outlook_client import fetch_latest_otp
        return fetch_latest_otp(
            email,
            after_ts=after_ts,
            settle_seconds=settle_seconds,
            poll_interval=poll_interval,
        )

    if EMAIL_PROVIDER == "imap":
        from core.imap_client import fetch_latest_otp
        return fetch_latest_otp(
            email,
            after_ts=after_ts,
            settle_seconds=settle_seconds,
            poll_interval=poll_interval,
        )

    raise RuntimeError(f"当前 EMAIL_PROVIDER={EMAIL_PROVIDER!r} 不支持自动读取验证码")

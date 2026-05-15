# -*- coding: utf-8 -*-
"""
OpenAI auth helpers used by the OTP-only registration flow.
"""
import json
import logging
import time

from core.sentinel import (
    build_sentinel_request_body,
    generate_requirements_token,
)
from core.sentinel_runner import generate_sentinel_token
from core.session import BrowserSession

logger = logging.getLogger(__name__)

_FOLLOW_AUTH_MAX_ATTEMPTS = 3
_FOLLOW_AUTH_BACKOFF_BASE = 2.0


class OtpSessionExpiredError(RuntimeError):
    """Raised when the email OTP is submitted after the auth session expired."""


def _is_transient_network_error(exc: Exception) -> bool:
    name = type(exc).__name__
    msg = str(exc).lower()
    transient_classes = ("SSLError", "ConnectionError", "Timeout", "CurlError", "ProxyError")
    if any(item.lower() in name.lower() for item in transient_classes):
        return True

    transient_keywords = (
        "wrong_version_number",
        "tls connect",
        "ssl",
        "connection reset",
        "connection refused",
        "timed out",
        "proxy",
        "curl: (35)",
        "curl: (52)",
        "curl: (56)",
    )
    return any(keyword in msg for keyword in transient_keywords)


def follow_authorize(session: BrowserSession, authorize_url: str) -> None:
    headers = session.get_auth_navigate_headers(referer="https://chatgpt.com/")

    last_exc: Exception | None = None
    for attempt in range(1, _FOLLOW_AUTH_MAX_ATTEMPTS + 1):
        try:
            logger.info(
                f"[步骤4] 跟随 authorize URL 重定向 (尝试 {attempt}/{_FOLLOW_AUTH_MAX_ATTEMPTS})..."
            )
            resp = session.get(authorize_url, headers=headers, allow_redirects=True)
            resp.raise_for_status()
            logger.info(f"[步骤4] 重定向完成, 最终URL: {resp.url}")
            return
        except Exception as exc:
            last_exc = exc
            if not _is_transient_network_error(exc):
                raise
            if attempt >= _FOLLOW_AUTH_MAX_ATTEMPTS:
                break
            backoff = _FOLLOW_AUTH_BACKOFF_BASE ** (attempt - 1)
            logger.warning(
                f"[步骤4] 临时网络错误 ({type(exc).__name__}: {str(exc)[:120]})，"
                f"{backoff:.1f}s 后重试..."
            )
            time.sleep(backoff)

    raise last_exc if last_exc else RuntimeError("步骤4 重试耗尽但没有捕获到异常")


def request_sentinel_token(session: BrowserSession, flow: str) -> dict:
    url = "https://sentinel.openai.com/backend-api/sentinel/req"
    p_value = generate_requirements_token(session.device_id)
    body = build_sentinel_request_body(p_value, session.device_id, flow)
    headers = session.get_sentinel_headers()

    last_exc: Exception | None = None
    for attempt in range(1, _FOLLOW_AUTH_MAX_ATTEMPTS + 1):
        try:
            logger.info(
                f"[Sentinel] 请求 sentinel token, flow={flow} "
                f"(尝试 {attempt}/{_FOLLOW_AUTH_MAX_ATTEMPTS})"
            )
            resp = session.post(url, headers=headers, data=body)
            resp.raise_for_status()

            data = resp.json()
            logger.info(f"[Sentinel] 获取 sentinel token 成功, persona={data.get('persona')}")

            if data.get("proofofwork", {}).get("required"):
                seed = data["proofofwork"]["seed"]
                difficulty = data["proofofwork"]["difficulty"]
                logger.info(f"[Sentinel] 需要 PoW: seed={seed}, difficulty={difficulty}")

            requires = []
            if data.get("turnstile", {}).get("required"):
                requires.append("turnstile")
            if data.get("so", {}).get("required"):
                requires.append("so")
            if data.get("proofofwork", {}).get("required"):
                requires.append("pow")
            logger.info(f"[Sentinel] 服务端要求项: {requires or '无'}")
            return data
        except Exception as exc:
            last_exc = exc
            if not _is_transient_network_error(exc):
                raise
            if attempt >= _FOLLOW_AUTH_MAX_ATTEMPTS:
                break
            backoff = _FOLLOW_AUTH_BACKOFF_BASE ** (attempt - 1)
            logger.warning(
                f"[Sentinel] 临时网络错误 ({type(exc).__name__}: {str(exc)[:120]})，"
                f"{backoff:.1f}s 后重试..."
            )
            time.sleep(backoff)

    raise last_exc if last_exc else RuntimeError("Sentinel 请求重试耗尽")


def build_sentinel_header(session: BrowserSession, sentinel_resp: dict, flow: str) -> tuple[str, str | None]:
    from config import USER_AGENT

    header_value = generate_sentinel_token(
        challenge=sentinel_resp,
        flow=flow,
        device_id=session.device_id,
        user_agent=USER_AGENT,
    )

    so_header = None
    try:
        parsed = json.loads(header_value)
        so_value = parsed.get("so")
        if so_value:
            so_header = json.dumps(
                {
                    "so": so_value,
                    "c": parsed.get("c", sentinel_resp.get("token", "")),
                    "id": session.device_id,
                    "flow": flow,
                },
                separators=(",", ":"),
            )
            logger.info("[Sentinel] 检测到 SO 字段，已构建 so-token 头")
    except (ValueError, TypeError) as exc:
        logger.warning(f"[Sentinel] runner 输出解析失败: {exc}")

    return header_value, so_header


def validate_email_otp(session: BrowserSession, code: str) -> dict:
    dump_url = "https://auth.openai.com/api/accounts/client_auth_session_dump"
    dump_headers = session.get_auth_headers(referer="https://auth.openai.com/email-verification")
    dump_headers.pop("content-type", None)
    dump_headers["accept"] = "application/json"
    logger.info("[步骤7] 预取 client_auth_session_dump...")
    dump_resp = session.get(dump_url, headers=dump_headers)
    logger.info(f"[步骤7] client_auth_session_dump 状态码: {dump_resp.status_code}")
    if dump_resp.status_code != 200:
        logger.debug(f"[步骤7] client_auth_session_dump 响应: {dump_resp.text[:500]}")

    url = "https://auth.openai.com/api/accounts/email-otp/validate"
    headers = session.get_auth_headers(referer="https://auth.openai.com/email-verification")

    body = json.dumps({"code": code})
    logger.info(f"[步骤7] 提交邮箱验证码: {code}")
    resp = session.post(url, headers=headers, data=body)

    if resp.status_code != 200:
        logger.error(f"[步骤7] 请求失败, 状态码: {resp.status_code}")
        logger.error(f"[步骤7] 响应内容: {resp.text}")
        try:
            error_payload = resp.json().get("error") or {}
        except Exception:
            error_payload = {}
        if resp.status_code == 409 and error_payload.get("code") == "invalid_state":
            raise OtpSessionExpiredError(
                error_payload.get("message") or "sign-in session expired before OTP validation"
            )
        resp.raise_for_status()

    data = resp.json()
    logger.info(f"[步骤7] 验证码验证成功: {data.get('page', {}).get('type')}")
    return data


def create_account(
    session: BrowserSession,
    name: str,
    birthday: str,
    sentinel_header: str,
    so_header: str | None = None,
) -> dict:
    url = "https://auth.openai.com/api/accounts/create_account"
    headers = session.get_auth_headers(referer="https://auth.openai.com/about-you")
    headers["openai-sentinel-token"] = sentinel_header
    if so_header:
        headers["openai-sentinel-so-token"] = so_header
        logger.info("[步骤9] 已添加 openai-sentinel-so-token 头")

    body = json.dumps(
        {
            "name": name,
            "birthdate": birthday,
        }
    )

    logger.info(f"[步骤9] 提交用户信息, 名称: {name}, 生日: {birthday}")
    resp = session.post(url, headers=headers, data=body)

    if resp.status_code != 200:
        logger.error(f"[步骤9] 请求失败, 状态码: {resp.status_code}")
        logger.error(f"[步骤9] 响应内容: {resp.text}")
        resp.raise_for_status()

    data = resp.json()
    logger.info("[步骤9] 创建接口返回成功，等待 OAuth 回调建立登录态")
    return data

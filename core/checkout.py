# -*- coding: utf-8 -*-
"""
ChatGPT checkout 链接生成。

注册成功后复用当前 BrowserSession 和 accessToken 调用官方 checkout 接口，
只把生成的 chatgpt.com/checkout/... 过渡链接打印到日志，不写入账号归档。
"""
import json
import logging
import re
from typing import Any

from core.session import BrowserSession

logger = logging.getLogger(__name__)

CHECKOUT_URL = "https://chatgpt.com/backend-api/payments/checkout"
CHECKOUT_SESSION_RE = re.compile(r"(cs_(?:live|test)_[A-Za-z0-9]+)")
PROCESSOR_ENTITY_RE = re.compile(r"(?:/checkout/|processor_entity=)([A-Za-z0-9_]+)")

# 目前只生成美国区 Plus 短链接，因此 processor_entity 默认会落到 openai_llc。
REGION_BILLING = {
    "US": {"country": "US", "currency": "USD"},
}


def build_checkout_payload() -> dict[str, Any]:
    """构造 ChatGPT Plus checkout 请求体，custom 模式会返回可拼短链接的 session id。"""
    return {
        "entry_point": "all_plans_pricing_modal",
        "plan_name": "chatgptplusplan",
        "billing_details": REGION_BILLING["US"],
        "cancel_url": "https://chatgpt.com/#pricing",
        "checkout_ui_mode": "custom",
        "promo_campaign": {
            "promo_campaign_id": "plus-1-month-free",
            "is_coupon_from_query_param": False,
        },
    }


def create_checkout_link(session: BrowserSession, access_token: str) -> dict[str, Any]:
    """使用注册流程刚拿到的 accessToken 创建一次 Plus checkout session。"""
    if not access_token:
        return _result(ok=False, status="skipped", message="access_token 为空")

    headers = session.get_chatgpt_headers(referer="https://chatgpt.com/")
    headers["accept"] = "application/json"
    headers["authorization"] = f"Bearer {access_token}"
    headers["origin"] = "https://chatgpt.com"

    # 复用同一会话/代理/UA，降低注册刚完成后再次请求 backend-api 的状态不一致风险。
    payload = build_checkout_payload()
    try:
        resp = session.post(CHECKOUT_URL, headers=headers, data=json.dumps(payload))
    except Exception as exc:
        return _result(ok=False, status="failed", message=f"{type(exc).__name__}: {exc}")

    text = resp.text or ""
    try:
        data = resp.json()
    except Exception:
        data = {}

    if resp.status_code >= 400:
        return _result(
            ok=False,
            status="failed",
            http_status=resp.status_code,
            message=_extract_error_message(data, text),
            raw=data if isinstance(data, dict) else {},
        )

    if not isinstance(data, dict):
        return _result(ok=False, status="failed", http_status=resp.status_code, message="checkout 响应不是 JSON 对象")

    link_info = _extract_link(data)
    link = link_info.get("link") or ""
    if not link:
        return _result(
            ok=False,
            status="failed",
            http_status=resp.status_code,
            message=f"未解析到 checkout 链接，响应字段: {list(data.keys())[:20]}",
            raw=data,
        )

    return _result(
        ok=True,
        status="success",
        http_status=resp.status_code,
        message="checkout 链接生成成功",
        link=link,
        short_url=link_info.get("short_url") or "",
        provider_url=link_info.get("provider_url") or "",
        checkout_session_id=link_info.get("checkout_session_id") or "",
        processor_entity=link_info.get("processor_entity") or "",
        billing_details=payload["billing_details"],
        plan_name=payload["plan_name"],
        raw=data,
    )


def _extract_link(data: dict[str, Any]) -> dict[str, str]:
    """兼容 hosted/custom 两类响应，优先输出 chatgpt.com/checkout/... 短链接。"""
    provider_url = _first_str(data, "url", "stripe_hosted_url", "checkout_url")
    session_id = _first_str(data, "checkout_session_id", "session_id")
    if not session_id:
        session_id = _extract_checkout_session(" ".join([
            provider_url,
            _str(data.get("success_url")),
            _str(data.get("cancel_url")),
            _str(data.get("return_url")),
            _str(data.get("client_secret")),
        ]))

    processor_entity = _str(data.get("processor_entity"))
    if not processor_entity:
        processor_entity = _extract_processor_entity(" ".join([
            provider_url,
            _str(data.get("success_url")),
            _str(data.get("cancel_url")),
            _str(data.get("return_url")),
        ])) or "openai_llc"

    short_url = f"https://chatgpt.com/checkout/{processor_entity}/{session_id}" if session_id else ""
    return {
        "link": short_url or provider_url,
        "short_url": short_url,
        "provider_url": provider_url,
        "checkout_session_id": session_id,
        "processor_entity": processor_entity,
    }


def _extract_checkout_session(value: str) -> str:
    match = CHECKOUT_SESSION_RE.search(value or "")
    return match.group(1) if match else ""


def _extract_processor_entity(value: str) -> str:
    match = PROCESSOR_ENTITY_RE.search(value or "")
    return match.group(1) if match else ""


def _first_str(data: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = _str(data.get(key))
        if value:
            return value
    return ""


def _str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _extract_error_message(data: Any, text: str) -> str:
    if isinstance(data, dict):
        for key in ("detail", "error", "message"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:800]
            if isinstance(value, dict):
                nested = _extract_error_message(value, "")
                if nested:
                    return nested
    return (text or "checkout 请求失败").replace("\n", " ")[:800]


def _result(**kwargs: Any) -> dict[str, Any]:
    return kwargs

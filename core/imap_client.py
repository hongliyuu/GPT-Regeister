# -*- coding: utf-8 -*-
import email
import imaplib
import json
import logging
import random
import socket
import ssl
import string
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime
from pathlib import Path

from config import (
    IMAP_ACCOUNTS,
    IMAP_ACCOUNTS_FILE,
    IMAP_ALIAS_DOMAIN,
    IMAP_ALIAS_DOMAIN_MODE,
    IMAP_ALIAS_MODE,
    IMAP_ALIAS_RANDOM_LENGTH,
    IMAP_ALIAS_SEPARATOR,
    IMAP_DEFAULT_HOST,
    IMAP_DEFAULT_PORT,
    IMAP_DEFAULT_SSL,
    IMAP_LOGIN_EMAIL,
    IMAP_LOGIN_PASSWORD,
    IMAP_MAILBOX,
    IMAP_STATE_FILE,
    OTP_MAX_WAIT,
    OTP_POLL_INTERVAL,
    OTP_SETTLE_SECONDS,
)
from core.otp_utils import extract_otp, looks_like_openai_email

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOCK = threading.RLock()
_CONTEXT_CACHE: dict[str, "ImapAccount"] = {}


@dataclass
class ImapAccount:
    email: str
    password: str
    host: str = IMAP_DEFAULT_HOST
    port: int = IMAP_DEFAULT_PORT
    ssl: bool = IMAP_DEFAULT_SSL
    login_email: str | None = None

    @property
    def imap_user(self) -> str:
        return self.login_email or self.email


class ImapClientError(RuntimeError):
    pass


def _path(value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else _PROJECT_ROOT / p


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _parse_bool(value: str) -> bool:
    return value.strip().lower() not in {"0", "false", "no", "off", "否"}


def _random_suffix(length: int) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=length))


def _make_alias(login_email: str) -> str:
    local, sep, domain = login_email.partition("@")
    if not sep:
        raise ImapClientError(f"邮箱格式错误，无法生成别名: {login_email}")
    suffix = _random_suffix(IMAP_ALIAS_RANDOM_LENGTH)

    if IMAP_ALIAS_DOMAIN_MODE == "forward" and IMAP_ALIAS_DOMAIN:
        target_domain = IMAP_ALIAS_DOMAIN
    else:
        target_domain = domain

    if IMAP_ALIAS_MODE == "full_random":
        return f"{suffix}@{target_domain}"
    if IMAP_ALIAS_MODE == "append_random":
        return f"{local}{IMAP_ALIAS_SEPARATOR}{suffix}@{target_domain}"
    if IMAP_ALIAS_MODE == "prefix_random":
        return f"{suffix}{IMAP_ALIAS_SEPARATOR}{local}@{target_domain}"
    if IMAP_ALIAS_MODE == "plus_random":
        return f"{local}+{suffix}@{target_domain}"
    raise ImapClientError(f"不支持的 IMAP_ALIAS_MODE: {IMAP_ALIAS_MODE}")


def _parse_account_line(line: str) -> ImapAccount:
    parts = [p.strip() for p in line.split("----")]
    if len(parts) not in {2, 3, 4, 5}:
        raise ImapClientError(f"IMAP 邮箱行格式错误，期望 2-5 段，实际 {len(parts)} 段")
    login_email = parts[0]
    password = parts[1]
    host = parts[2] if len(parts) >= 3 and parts[2] else IMAP_DEFAULT_HOST
    port = int(parts[3]) if len(parts) >= 4 and parts[3] else IMAP_DEFAULT_PORT
    use_ssl = _parse_bool(parts[4]) if len(parts) >= 5 and parts[4] else IMAP_DEFAULT_SSL
    if not login_email or not password:
        raise ImapClientError("IMAP 登录邮箱和密码不能为空")
    return ImapAccount(
        email=login_email,
        login_email=login_email,
        password=password,
        host=host,
        port=port,
        ssl=use_ssl,
    )


def _read_source_accounts() -> list[ImapAccount]:
    accounts: list[ImapAccount] = []

    if IMAP_LOGIN_EMAIL and IMAP_LOGIN_PASSWORD:
        accounts.append(ImapAccount(
            email=IMAP_LOGIN_EMAIL,
            login_email=IMAP_LOGIN_EMAIL,
            password=IMAP_LOGIN_PASSWORD,
            host=IMAP_DEFAULT_HOST,
            port=IMAP_DEFAULT_PORT,
            ssl=IMAP_DEFAULT_SSL,
        ))

    for item in IMAP_ACCOUNTS:
        if isinstance(item, dict):
            try:
                accounts.append(ImapAccount(
                    email=item.get("email", ""),
                    login_email=item.get("login_email") or item.get("email", ""),
                    password=item.get("password", ""),
                    host=item.get("host") or IMAP_DEFAULT_HOST,
                    port=int(item.get("port") or IMAP_DEFAULT_PORT),
                    ssl=bool(item.get("ssl", IMAP_DEFAULT_SSL)),
                ))
            except Exception as exc:
                logger.warning(f"[IMAP] 配置行跳过: {exc}")
        elif isinstance(item, str) and item.strip():
            try:
                accounts.append(_parse_account_line(item))
            except Exception as exc:
                logger.warning(f"[IMAP] 配置行跳过: {exc}")

    if accounts:
        return accounts

    source = _path(IMAP_ACCOUNTS_FILE)
    if not source.exists():
        return []
    for lineno, raw in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            accounts.append(_parse_account_line(line))
        except Exception as exc:
            logger.warning(f"[IMAP] {source.name} 第 {lineno} 行跳过: {exc}")
    return accounts


def _load_state() -> list[dict]:
    state = _path(IMAP_STATE_FILE)
    if not state.exists():
        return []
    try:
        data = json.loads(state.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _save_state(rows: list[dict]) -> None:
    state = _path(IMAP_STATE_FILE)
    state.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _row_to_account(row: dict) -> ImapAccount:
    return ImapAccount(
        email=row["email"],
        login_email=row.get("login_email") or row["email"],
        password=row["password"],
        host=row.get("host") or IMAP_DEFAULT_HOST,
        port=int(row.get("port") or IMAP_DEFAULT_PORT),
        ssl=bool(row.get("ssl", IMAP_DEFAULT_SSL)),
    )


def sync_accounts_from_file() -> tuple[int, int]:
    with _LOCK:
        rows = _load_state()
        existing = {str(row.get("login_email") or row.get("email", "")).lower() for row in rows}
        inserted = 0
        skipped = 0
        next_id = max((int(row.get("id", 0) or 0) for row in rows), default=0) + 1
        for account in _read_source_accounts():
            key = account.imap_user.lower()
            if key in existing:
                skipped += 1
                continue
            row = asdict(account)
            row.update({
                "email": account.imap_user,
                "login_email": account.imap_user,
                "id": next_id,
                "status": "available",
                "used_at": None,
                "note": "",
                "imported_at": _now(),
                "last_alias": None,
                "aliases": [],
            })
            rows.append(row)
            existing.add(key)
            inserted += 1
            next_id += 1
        if inserted:
            _save_state(rows)
        return inserted, skipped


def pick_account() -> ImapAccount:
    inserted, skipped = sync_accounts_from_file()
    if inserted:
        logger.info(f"[IMAP] 已从 {IMAP_ACCOUNTS_FILE} 导入 {inserted} 个新登录邮箱（跳过 {skipped} 个）")
    with _LOCK:
        rows = _load_state()
        for row in rows:
            if row.get("status") == "available":
                alias_email = _make_alias(row.get("login_email") or row["email"])
                aliases = row.get("aliases") if isinstance(row.get("aliases"), list) else []
                aliases.append({"email": alias_email, "created_at": _now(), "status": "used"})
                row["email"] = alias_email
                row["last_alias"] = alias_email
                row["aliases"] = aliases
                row["status"] = "used"
                row["used_at"] = _now()
                row["note"] = ""
                _save_state(rows)
                account = _row_to_account(row)
                _CONTEXT_CACHE[account.email] = account
                logger.info(f"[IMAP] 选中注册地址: {account.email}，登录邮箱: {account.imap_user}（id={row.get('id')}）")
                return account
    summary = pool_summary()
    raise ImapClientError(f"IMAP 邮箱池没有可用账号: {summary}. 请在 config.yaml 的 email.imap 中配置 login_email 和 login_password")


def release_account(email_addr: str, status: str = "available", note: str | None = None) -> None:
    with _LOCK:
        rows = _load_state()
        for row in rows:
            if str(row.get("email", "")).lower() == email_addr.lower() or str(row.get("last_alias", "")).lower() == email_addr.lower():
                row["status"] = status
                row["note"] = note or ""
                if status == "available":
                    row["used_at"] = None
                aliases = row.get("aliases") if isinstance(row.get("aliases"), list) else []
                for item in aliases:
                    if str(item.get("email", "")).lower() == email_addr.lower():
                        item["status"] = status
                        item["note"] = note or ""
                _save_state(rows)
                break
    _CONTEXT_CACHE.pop(email_addr, None)


def pool_summary() -> dict:
    rows = _load_state()
    result = {"available": 0, "used": 0, "failed": 0, "total": len(rows)}
    for row in rows:
        status = row.get("status")
        if status in result:
            result[status] += 1
    return result


def get_account_context(email_addr: str) -> ImapAccount | None:
    if email_addr in _CONTEXT_CACHE:
        return _CONTEXT_CACHE[email_addr]
    sync_accounts_from_file()
    rows = _load_state()
    for row in rows:
        if str(row.get("email", "")).lower() == email_addr.lower() or str(row.get("last_alias", "")).lower() == email_addr.lower():
            account = _row_to_account(row)
            _CONTEXT_CACHE[account.email] = account
            return account
    return None


def _connect(account: ImapAccount):
    if account.ssl:
        return imaplib.IMAP4_SSL(account.host, account.port, ssl_context=ssl.create_default_context(), timeout=30)
    return imaplib.IMAP4(account.host, account.port, timeout=30)


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    parts = []
    for payload, charset in decode_header(value):
        if isinstance(payload, bytes):
            parts.append(payload.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(payload)
    return "".join(parts)


def _message_text(msg: Message) -> tuple[str, str]:
    text_parts = []
    html_parts = []
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype not in {"text/plain", "text/html"}:
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            content = payload.decode(charset, errors="replace")
            if ctype == "text/plain":
                text_parts.append(content)
            else:
                html_parts.append(content)
    else:
        payload = msg.get_payload(decode=True)
        if payload is not None:
            charset = msg.get_content_charset() or "utf-8"
            content = payload.decode(charset, errors="replace")
            if msg.get_content_type() == "text/html":
                html_parts.append(content)
            else:
                text_parts.append(content)
    return "\n".join(text_parts), "\n".join(html_parts)


def _message_to_item(msg: Message) -> dict:
    text, html = _message_text(msg)
    sender = _decode_header_value(msg.get("From"))
    subject = _decode_header_value(msg.get("Subject"))
    to_value = _decode_header_value(msg.get("To"))
    cc_value = _decode_header_value(msg.get("Cc"))
    delivered_to = _decode_header_value(msg.get("Delivered-To"))
    x_original_to = _decode_header_value(msg.get("X-Original-To"))
    envelope_to = _decode_header_value(msg.get("Envelope-To"))
    date_value = _decode_header_value(msg.get("Date"))
    return {
        "from": sender,
        "subject": subject,
        "text": text,
        "html": html,
        "content": html,
        "bodyText": text,
        "bodyHtml": html,
        "to": to_value,
        "cc": cc_value,
        "deliveredTo": delivered_to,
        "xOriginalTo": x_original_to,
        "envelopeTo": envelope_to,
        "date": date_value,
    }


def _parse_ts(item: dict) -> float:
    raw = item.get("date") or ""
    if raw:
        try:
            parsed = parsedate_to_datetime(raw)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.timestamp()
        except Exception:
            pass
    return 0.0


def _is_after(item: dict, after_ts: float | None) -> bool:
    if after_ts is None:
        return True
    ts = _parse_ts(item)
    return ts == 0.0 or ts >= after_ts - 30


def _recipient_matches(item: dict, target_email: str) -> bool:
    target = target_email.lower()
    fields = (
        item.get("to") or "",
        item.get("cc") or "",
        item.get("deliveredTo") or "",
        item.get("xOriginalTo") or "",
        item.get("envelopeTo") or "",
        item.get("text") or "",
        item.get("html") or "",
    )
    return any(target in str(field).lower() for field in fields)


def _fetch_emails_via_client(client, limit: int = 20) -> list[dict]:

    typ, data = client.select(IMAP_MAILBOX)
    if typ != "OK":
        raise ImapClientError(f"选择邮箱目录失败: {IMAP_MAILBOX}")

    total = 0
    if data and data[0]:
        try:
            total = int(data[0])
        except Exception:
            total = 0
    if total <= 0:
        return []

    start = max(1, total - limit + 1)
    ids = range(total, start - 1, -1)
    items = []
    for msg_no in ids:
        typ, msg_data = client.fetch(str(msg_no), "(RFC822)")
        if typ != "OK" or not msg_data:
            continue
        for part in msg_data:
            if not isinstance(part, tuple):
                continue
            msg = email.message_from_bytes(part[1])
            items.append(_message_to_item(msg))
            break
    return items


def fetch_recent_emails(account: ImapAccount, limit: int = 20) -> list[dict]:
    client = None
    try:
        client = _connect(account)
        client.login(account.imap_user, account.password)
        return _fetch_emails_via_client(client, limit=limit)
    finally:
        if client is not None:
            try:
                client.logout()
            except Exception:
                pass


def fetch_latest_otp(
    email_addr: str,
    after_ts: float | None = None,
    max_wait: int | None = None,
    poll_interval: int | None = None,
    settle_seconds: int | None = None,
) -> str:
    account = get_account_context(email_addr)
    if account is None:
        raise ImapClientError(f"未找到 {email_addr} 的 IMAP 账号上下文")

    deadline = time.time() + (max_wait or OTP_MAX_WAIT)
    interval = poll_interval or OTP_POLL_INTERVAL
    settle = OTP_SETTLE_SECONDS if settle_seconds is None else settle_seconds
    best_otp = None
    best_ts = 0.0
    best_subject = ""
    settle_until = None

    logger.info(f"[IMAP] 开始轮询注册别名 {email_addr}，登录邮箱 {account.imap_user}，host={account.host}:{account.port}, 最长 {max_wait or OTP_MAX_WAIT}s")

    imap_client = None
    try:
        while time.time() < deadline:
            if imap_client is None:
                try:
                    imap_client = _connect(account)
                    imap_client.login(account.imap_user, account.password)
                except (imaplib.IMAP4.error, socket.error, OSError) as exc:
                    logger.warning(f"[IMAP] 连接/登录失败: {type(exc).__name__}: {exc}，{interval}s 后重试")
                    time.sleep(interval)
                    continue

            try:
                emails = _fetch_emails_via_client(imap_client, limit=20)
            except (imaplib.IMAP4.error, socket.error, OSError) as exc:
                logger.warning(f"[IMAP] 取信失败: {type(exc).__name__}: {exc}，将重新连接")
                try:
                    imap_client.logout()
                except Exception:
                    pass
                imap_client = None
                emails = []
                time.sleep(interval)
                continue

            emails.sort(key=_parse_ts, reverse=True)
            for item in emails:
                if not _is_after(item, after_ts):
                    continue
                if not _recipient_matches(item, email_addr):
                    continue
                if not looks_like_openai_email(item):
                    continue
                otp = extract_otp(item)
                if not otp:
                    continue
                ts = _parse_ts(item)
                if ts >= best_ts:
                    best_otp = otp
                    best_ts = ts
                    best_subject = item.get("subject") or ""
                    settle_until = time.time() + settle
                    logger.info(f"[IMAP] 锁定 OTP={otp}, subject={best_subject!r}, 等 {settle}s 看是否有更新邮件")
                break

            now = time.time()
            if best_otp and settle_until is not None and now >= settle_until:
                logger.info(f"[IMAP] settle 完成，返回 OTP={best_otp}, subject={best_subject!r}")
                return best_otp

            remaining = int(deadline - now)
            if best_otp:
                logger.info(f"[IMAP] 已锁定候选 OTP={best_otp}，等待 settle（总剩余 {remaining}s）")
            else:
                logger.info(f"[IMAP] 暂未收到发给 {email_addr} 的 OpenAI 邮件，{interval}s 后重试（剩余 {remaining}s）")
            time.sleep(interval)

        if best_otp:
            logger.warning(f"[IMAP] 总超时但已有候选，返回 OTP={best_otp}")
            return best_otp
        raise ImapClientError(f"等待 {email_addr} 的 OTP 超时（>{max_wait or OTP_MAX_WAIT}s）")
    finally:
        if imap_client is not None:
            try:
                imap_client.logout()
            except Exception:
                pass

# -*- coding: utf-8 -*-
import sys
import time
from pathlib import Path

from config import (
    IMAP_ACCOUNTS,
    IMAP_ACCOUNTS_FILE,
    IMAP_DEFAULT_HOST,
    IMAP_DEFAULT_PORT,
    IMAP_DEFAULT_SSL,
    IMAP_LOGIN_EMAIL,
    IMAP_LOGIN_PASSWORD,
)
from core.imap_client import ImapAccount, _make_alias, _parse_ts, _parse_account_line, _recipient_matches, fetch_recent_emails
from core.otp_utils import extract_otp, looks_like_openai_email


POLL_INTERVAL = 3
MAX_WAIT = 300


def load_account() -> ImapAccount:
    if len(sys.argv) >= 2:
        return _parse_account_line(sys.argv[1].strip())

    if IMAP_LOGIN_EMAIL and IMAP_LOGIN_PASSWORD:
        return ImapAccount(
            email=IMAP_LOGIN_EMAIL,
            login_email=IMAP_LOGIN_EMAIL,
            password=IMAP_LOGIN_PASSWORD,
            host=IMAP_DEFAULT_HOST,
            port=IMAP_DEFAULT_PORT,
            ssl=IMAP_DEFAULT_SSL,
        )

    for item in IMAP_ACCOUNTS:
        if isinstance(item, dict):
            return ImapAccount(
                email=item.get("email", ""),
                login_email=item.get("login_email") or item.get("email", ""),
                password=item.get("password", ""),
                host=item.get("host") or IMAP_DEFAULT_HOST,
                port=int(item.get("port") or IMAP_DEFAULT_PORT),
                ssl=bool(item.get("ssl", IMAP_DEFAULT_SSL)),
            )
        elif isinstance(item, str) and item.strip():
            return _parse_account_line(item)

    source = _path(IMAP_ACCOUNTS_FILE)
    if source.exists():
        for raw in source.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                return _parse_account_line(line)

    raise RuntimeError("请在 config.yaml 的 email.imap 中配置 login_email 和 login_password")


def _path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else Path(__file__).resolve().parent.parent / p


def fingerprint(item: dict) -> str:
    return "|".join([
        item.get("date") or "",
        item.get("from") or "",
        item.get("to") or "",
        item.get("subject") or "",
    ])


def print_email(item: dict, alias_email: str) -> None:
    subject = item.get("subject") or ""
    sender = item.get("from") or ""
    to_value = item.get("to") or ""
    cc_value = item.get("cc") or ""
    delivered_to = item.get("deliveredTo") or ""
    x_original_to = item.get("xOriginalTo") or ""
    envelope_to = item.get("envelopeTo") or ""
    date = item.get("date") or ""
    text = (item.get("text") or "").strip().replace("\r", " ").replace("\n", " ")
    html = (item.get("html") or "").strip().replace("\r", " ").replace("\n", " ")
    preview = text or html
    is_openai = looks_like_openai_email(item)
    otp = extract_otp(item) if is_openai else ""
    matched = _recipient_matches(item, alias_email)
    print("检测到新邮件:")
    print(f"  alias_matched={matched}")
    print(f"  subject={subject!r}")
    print(f"  from={sender!r}")
    print(f"  to={to_value!r}")
    print(f"  cc={cc_value!r}")
    print(f"  delivered_to={delivered_to!r}")
    print(f"  x_original_to={x_original_to!r}")
    print(f"  envelope_to={envelope_to!r}")
    print(f"  date={date!r}")
    print(f"  openai={is_openai}, otp={otp or '-'}")
    if preview:
        print(f"  preview={preview[:300]!r}")


def main() -> int:
    account = load_account()
    alias_email = _make_alias(account.imap_user)
    started_at = time.time()

    print(f"登录邮箱: {account.imap_user}")
    print(f"测试收件别名: {alias_email}")
    print(f"IMAP: {account.host}:{account.port}, ssl={account.ssl}")
    print(f"默认配置: {IMAP_DEFAULT_HOST}:{IMAP_DEFAULT_PORT}, ssl={IMAP_DEFAULT_SSL}")
    print("-" * 60)
    print(f"请现在手动发送一封邮件到: {alias_email}")
    print(f"脚本会持续检测 {MAX_WAIT}s，每 {POLL_INTERVAL}s 检查一次。")
    print("检测规则：优先匹配别名；如果发现启动后新邮件，即使收件人字段不含别名也会打印，避免误认为卡死。")
    print("-" * 60)

    seen = set()
    first_round = True
    deadline = started_at + MAX_WAIT
    while time.time() < deadline:
        try:
            emails = fetch_recent_emails(account, limit=30)
        except Exception as exc:
            print(f"IMAP 检测失败: {type(exc).__name__}: {exc}")
            time.sleep(POLL_INTERVAL)
            continue

        emails.sort(key=_parse_ts, reverse=True)
        if first_round:
            for item in emails:
                seen.add(fingerprint(item))
            first_round = False
            print(f"已记录当前收件箱最近 {len(emails)} 封邮件，开始等待新邮件...")
            time.sleep(POLL_INTERVAL)
            continue

        new_items = []
        for item in emails:
            fp = fingerprint(item)
            if fp in seen:
                continue
            seen.add(fp)
            ts = _parse_ts(item)
            if ts and ts < started_at - 30:
                continue
            new_items.append(item)

        if new_items:
            new_items.sort(key=lambda item: (not _recipient_matches(item, alias_email), -_parse_ts(item)))
            item = new_items[0]
            print_email(item, alias_email)
            print("-" * 60)
            if _recipient_matches(item, alias_email):
                print("别名收件测试通过")
                return 0
            print("收到新邮件，但邮件头/正文里没有匹配到测试别名。请检查是否发到了上面打印的别名，或 2925 是否改写了收件人字段。")
            return 2

        remaining = int(deadline - time.time())
        print(f"暂未收到新邮件，{POLL_INTERVAL}s 后继续检测（剩余 {remaining}s）...")
        time.sleep(POLL_INTERVAL)

    print(f"别名收件测试超时：{MAX_WAIT}s 内没有检测到新邮件")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

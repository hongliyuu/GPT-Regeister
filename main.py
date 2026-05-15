# -*- coding: utf-8 -*-
import argparse
import logging
import random
import string
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from config import (
    ENABLE_2FA,
    REGISTER_BIRTHDAY,
    REGISTER_EMAIL,
    REGISTER_NAME,
    USE_EMAIL_SERVICE,
)
from core.account_export import (
    create_batch_archive_dir,
    fetch_session,
    follow_oauth_callback,
    save_account_data,
    setup_2fa,
)
from core.chatgpt_auth import get_csrf_token, get_providers, signin_openai
from core.email_provider import acquire_email, wait_for_otp
from core.openai_auth import (
    OtpSessionExpiredError,
    build_sentinel_header,
    create_account,
    follow_authorize,
    request_sentinel_token,
    validate_email_otp,
)
from core.session import BrowserSession

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_FINALIZE_SESSION_MAX_ATTEMPTS = 5
_FINALIZE_SESSION_BACKOFF_BASE = 2.0
_OTP_SETTLE_SECONDS_FAST = 0
_OTP_POLL_INTERVAL_FAST = 1
_OTP_SESSION_RESTARTS = 0


def configure_logging(verbose: bool = False) -> None:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    for handler in root.handlers:
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    logging.getLogger("core").setLevel(logging.DEBUG if verbose else logging.WARNING)
    if not verbose:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)


def _is_success(result: dict) -> bool:
    return isinstance(result, dict) and bool(result.get("success"))


def generate_display_name() -> str:
    first = random.choice(string.ascii_uppercase) + "".join(
        random.choices(string.ascii_lowercase, k=random.randint(3, 6))
    )
    last = random.choice(string.ascii_uppercase) + "".join(
        random.choices(string.ascii_lowercase, k=random.randint(3, 6))
    )
    return f"{first} {last}"


def prepare_registration_inputs() -> tuple[str, str, str]:
    email = REGISTER_EMAIL
    name = REGISTER_NAME
    birthday = REGISTER_BIRTHDAY

    if not email:
        if USE_EMAIL_SERVICE:
            email = acquire_email()
            logger.debug(f"自动获取邮箱: {email}")
        else:
            email = input("请输入注册邮箱: ").strip()

    if not name:
        if USE_EMAIL_SERVICE:
            name = generate_display_name()
            logger.info(f"[注册] 自动生成用户名: {name}")
        else:
            name = input("请输入姓名: ").strip()

    if not all([email, name]):
        raise RuntimeError("邮箱和姓名不能为空")
    return email, name, birthday


def _format_proxy_label(session: BrowserSession) -> str:
    if not session.proxy:
        return "无"
    try:
        sid_part = next((seg for seg in session.proxy.split("@")[0].split("-") if len(seg) == 8), "***")
        return f"{session.proxy.split('://')[0]}://...sid-{sid_part}...@{session.proxy.split('@')[-1]}"
    except Exception:
        return "已配置"


def _finalize_registration_session(
    session: BrowserSession,
    continue_url: str,
    email: str,
) -> tuple[dict, str]:
    if not continue_url:
        raise RuntimeError("create_account 响应缺少 continue_url，无法完成 OAuth 回调")

    last_exc: Exception | None = None
    for attempt in range(1, _FINALIZE_SESSION_MAX_ATTEMPTS + 1):
        try:
            logger.info(f"[登录态] 完成 OAuth 回调并拉取 Token: {email} (尝试 {attempt}/{_FINALIZE_SESSION_MAX_ATTEMPTS})")
            follow_oauth_callback(session, continue_url)
            time.sleep(1)
            session_info = fetch_session(session)
            access_token = session_info.get("accessToken")
            if not access_token:
                raise RuntimeError("session 响应缺少 accessToken")
            logger.info(f"[登录态] 已拿到 accessToken: {email}")
            return session_info, access_token
        except Exception as exc:
            last_exc = exc
            if attempt >= _FINALIZE_SESSION_MAX_ATTEMPTS:
                break
            backoff = _FINALIZE_SESSION_BACKOFF_BASE ** (attempt - 1)
            logger.warning(
                f"[登录态] 回调或拉取 Token 失败: {type(exc).__name__}: {str(exc)[:180]}，"
                f"{backoff:.1f}s 后重试"
            )
            time.sleep(backoff)

    raise RuntimeError(
        f"OAuth 回调/获取 Token 重试耗尽: {email}; last={type(last_exc).__name__ if last_exc else 'Unknown'}: {last_exc}"
    ) from last_exc


def _run_registration_once(
    *,
    session: BrowserSession,
    email: str,
    name: str,
    birthday: str,
    otp_code: str | None,
    otp_provider,
    batch_dir,
) -> dict:
    get_providers(session)
    time.sleep(0.5)
    csrf_token = get_csrf_token(session)
    time.sleep(0.5)
    authorize_url = signin_openai(session, csrf_token, email)
    time.sleep(0.5)

    otp_after_ts = time.time()
    follow_authorize(session, authorize_url)

    current_otp = otp_code
    if current_otp is None:
        if USE_EMAIL_SERVICE:
            logger.info(f"[OTP] 等待验证码：{email}")
            current_otp = wait_for_otp(
                email,
                after_ts=otp_after_ts,
                settle_seconds=_OTP_SETTLE_SECONDS_FAST,
                poll_interval=_OTP_POLL_INTERVAL_FAST,
            )
        else:
            logger.info("")
            logger.info("[OTP] 验证码已触发发送，请检查邮箱并输入收到的 6 位验证码")
            if otp_provider is not None:
                current_otp = otp_provider(email).strip()
            else:
                current_otp = input(">>> 验证码: ").strip()

    validate_email_otp(session, current_otp)
    time.sleep(0.5)

    sentinel_resp_8 = request_sentinel_token(session, "oauth_create_account")
    sentinel_header_8, so_header_8 = build_sentinel_header(session, sentinel_resp_8, "oauth_create_account")
    time.sleep(0.3)
    create_result = create_account(session, name, birthday, sentinel_header_8, so_header_8)
    logger.info(f"[注册] 创建接口已通过：{email}，继续完成 OAuth 回调")
    time.sleep(1)

    continue_url = create_result.get("continue_url")
    if not continue_url:
        raise RuntimeError(f"create_account 响应缺少 continue_url，无法继续: {create_result}")

    session_info, access_token = _finalize_registration_session(session, continue_url, email)
    time.sleep(1)

    totp_secret = None
    if ENABLE_2FA:
        try:
            totp_secret = setup_2fa(session, email)
        except Exception as exc:
            logger.error(f"2FA 设置失败: {exc}")
            logger.debug("2FA 错误详情:", exc_info=True)
            logger.warning("将继续保存账号信息（不含 TOTP secret）")
    else:
        logger.debug("已跳过 2FA 设置 (config.ENABLE_2FA=False)")

    from config import EMAIL_SOURCE

    account_id = save_account_data(
        email=email,
        access_token=access_token,
        totp_secret=totp_secret,
        email_source=EMAIL_SOURCE,
        proxy_used=session.proxy or None,
        batch_dir=batch_dir,
        extra={
            "user": session_info.get("user"),
            "account": session_info.get("account"),
            "expires": session_info.get("expires"),
            "device_id": session.device_id,
        },
    )
    logger.info(f"[完成] {email}，账号ID={account_id}，Token={access_token[:16]}...")

    flow_result = {"status": "skipped", "ok": False, "message": "未触发"}
    try:
        from core.flow_trigger import trigger_flow
        flow_result = trigger_flow(access_token)
    except Exception as exc:
        flow_result = {"status": "failed", "ok": False, "message": f"{type(exc).__name__}: {exc}"}

    if flow_result.get("ok"):
        logger.info(
            f"[Flow] 成功：{email}，HTTP={flow_result.get('http_status')}, "
            f"flow_id={flow_result.get('flow_id') or '未解析'}"
        )
    elif flow_result.get("status") == "skipped":
        logger.info(f"[Flow] 跳过：{email}，原因={flow_result.get('message')}")
    else:
        logger.warning(
            f"[Flow] 失败：{email}，HTTP={flow_result.get('http_status') or '无'}, "
            f"原因={flow_result.get('message')}"
        )

    logger.debug(f"[完成] TOTP Secret: {totp_secret or '(未设置)'}")
    return {
        "success": True,
        "email": email,
        "account_id": account_id,
        "access_token": access_token,
        "totp_secret": totp_secret,
        "flow": flow_result,
    }


def run_registration(
    email: str,
    name: str,
    birthday: str = "2000-01-01",
    proxy: str = None,
    otp_code: str = None,
    otp_provider=None,
    batch_dir=None,
):
    create_acknowledged = False
    last_exc: Exception | None = None

    for attempt in range(1, _OTP_SESSION_RESTARTS + 2):
        session = BrowserSession(proxy=proxy)
        logger.info(f"[注册] 开始：{email}，代理={_format_proxy_label(session)}")
        logger.debug(f"[注册] 设备ID={session.device_id}，会话日志ID={session.auth_session_logging_id}")
        try:
            result = _run_registration_once(
                session=session,
                email=email,
                name=name,
                birthday=birthday,
                otp_code=otp_code if attempt == 1 else None,
                otp_provider=otp_provider,
                batch_dir=batch_dir,
            )
            return result
        except OtpSessionExpiredError as exc:
            last_exc = exc
            if attempt > _OTP_SESSION_RESTARTS:
                break
            logger.warning(f"[OTP] 会话已过期，准备重开当前注册会话并重新获取验证码: {exc}")
            time.sleep(1)
            continue
        except Exception as e:
            last_exc = e
            logger.error(f"[失败] {email}: {type(e).__name__}: {e}")
            logger.debug("详细错误信息:", exc_info=True)
            try:
                from config import EMAIL_PROVIDER as _provider
                release_account = None
                if _provider == "outlook_oauth":
                    from core.outlook_client import release_account as release_account
                elif _provider == "imap":
                    from core.imap_client import release_account as release_account
                if release_account and email:
                    if create_acknowledged:
                        release_account(
                            email,
                            status="failed",
                            note=f"创建接口已通过但后续失败，已废弃: {str(e)[:180]}",
                        )
                        logger.warning(f"[邮箱] {email} 已创建但后续失败，标记为 failed，不再重新注册")
                    else:
                        release_account(email, status="available", note=f"上次失败: {str(e)[:180]}")
            except Exception:
                pass
            return {"success": False, "email": email, "error": str(e)}

    if last_exc is not None:
        return {"success": False, "email": email, "error": str(last_exc)}
    return {"success": False, "email": email, "error": "unknown"}


def run_one_batch_item(index: int, total: int, batch_dir=None) -> dict:
    logger.info(f"[批量] 开始第 {index + 1}/{total} 个注册")
    try:
        email, name, birthday = prepare_registration_inputs()
        return run_registration(
            email=email,
            name=name,
            birthday=birthday,
            batch_dir=batch_dir,
        )
    except Exception as exc:
        logger.error(f"[批量] 第 {index + 1} 个注册准备阶段失败: {type(exc).__name__}: {exc}")
        logger.debug("准备阶段错误详情:", exc_info=True)
        return {"success": False, "error": str(exc)}


def run_serial_batch(count: int, delay: float, continue_on_fail: bool, batch_dir=None) -> list[dict]:
    results = []
    for index in range(count):
        result = run_one_batch_item(index, count, batch_dir)
        results.append(result)
        if not _is_success(result) and not continue_on_fail:
            logger.error("[批量] 当前账号失败，已停止。需要继续跑可加 --continue-on-fail")
            break
        if delay > 0 and index < count - 1:
            logger.info(f"[批量] 等待 {delay} 秒后继续")
            time.sleep(delay)
    return results


def run_parallel_batch(
    count: int,
    workers: int,
    delay: float,
    continue_on_fail: bool,
    batch_dir=None,
) -> list[dict]:
    logger.info(f"[批量] 启用多线程注册：目标 {count}，并发 {workers}")
    if delay > 0:
        logger.info(f"[批量] 并发模式下 --delay={delay} 表示提交任务之间的间隔")

    results: list[dict] = []
    future_to_index = {}
    next_index = 0
    stop_submitting = False

    def submit_next(executor: ThreadPoolExecutor) -> bool:
        nonlocal next_index
        if stop_submitting or next_index >= count:
            return False
        future = executor.submit(run_one_batch_item, next_index, count, batch_dir)
        future_to_index[future] = next_index
        next_index += 1
        if delay > 0 and next_index < count:
            time.sleep(delay)
        return True

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="reg-cli") as executor:
        while len(future_to_index) < workers and submit_next(executor):
            pass

        while future_to_index:
            done, _ = wait(future_to_index, return_when=FIRST_COMPLETED)
            for future in done:
                index = future_to_index.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    logger.error(f"[批量] 第 {index + 1}/{count} 个注册线程异常: {type(exc).__name__}: {exc}")
                    logger.debug("线程错误详情:", exc_info=True)
                    result = {"success": False, "error": str(exc)}
                results.append(result)

                if not _is_success(result) and not continue_on_fail:
                    stop_submitting = True
                    logger.error("[批量] 当前账号失败，已停止提交新任务。已开始的任务会继续跑完。")

            while len(future_to_index) < workers and submit_next(executor):
                pass

    return results


def main():
    parser = argparse.ArgumentParser(description="ChatGPT 协议注册 CLI")
    parser.add_argument("-n", "--count", type=int, default=1, help="连续注册数量，默认 1")
    parser.add_argument("--workers", type=int, default=1, help="并发注册线程数，默认 1（串行）")
    parser.add_argument("--delay", type=float, default=0, help="每次注册结束后的间隔秒数")
    parser.add_argument("--continue-on-fail", action="store_true", help="单个账号失败后继续注册下一个")
    parser.add_argument("--verbose", action="store_true", help="显示详细步骤日志和错误堆栈")
    args = parser.parse_args()
    configure_logging(args.verbose)

    if args.count < 1:
        logger.error("注册数量必须大于 0")
        sys.exit(1)
    if args.workers < 1:
        logger.error("并发线程数必须大于 0")
        sys.exit(1)
    if args.count > 1 and REGISTER_EMAIL:
        logger.error("config.REGISTER_EMAIL 已固定邮箱，不适合批量注册；请留空后再使用 --count")
        sys.exit(1)
    if args.workers > 1 and not USE_EMAIL_SERVICE:
        logger.error("多线程注册需要启用 Outlook 自动取件；请开启 USE_EMAIL_SERVICE 或改用 --workers 1")
        sys.exit(1)
    if args.workers > args.count:
        logger.info(f"[批量] 并发线程数 {args.workers} 大于目标数量，已按 {args.count} 个任务执行")
        args.workers = args.count

    batch_dir = create_batch_archive_dir(args.count, args.workers)
    logger.info(f"[批量] 本批次归档目录：{batch_dir}")
    if args.workers > 1:
        results = run_parallel_batch(args.count, args.workers, args.delay, args.continue_on_fail, batch_dir)
    else:
        results = run_serial_batch(args.count, args.delay, args.continue_on_fail, batch_dir)

    success_count = sum(1 for r in results if _is_success(r))
    flow_success_count = sum(1 for r in results if _is_success(r) and isinstance(r.get("flow"), dict) and r["flow"].get("ok"))
    flow_failed_count = sum(1 for r in results if _is_success(r) and isinstance(r.get("flow"), dict) and r["flow"].get("status") == "failed")
    flow_skipped_count = sum(1 for r in results if _is_success(r) and isinstance(r.get("flow"), dict) and r["flow"].get("status") == "skipped")
    logger.info(f"[批量] 完成：成功 {success_count} / 尝试 {len(results)} / 目标 {args.count}")
    if success_count:
        logger.info(f"[批量] Flow：成功 {flow_success_count} / 失败 {flow_failed_count} / 跳过 {flow_skipped_count}")
    sys.exit(0 if success_count == args.count else 1)


if __name__ == "__main__":
    main()

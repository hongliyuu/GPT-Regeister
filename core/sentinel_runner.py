# -*- coding: utf-8 -*-
"""
Sentinel Runner 适配层
通过 subprocess 调用项目根目录的 sentinel-runner.js，
让 Node.js 在 vm 沙箱中真实运行 sdk.js，生成可通过校验的 sentinel-token。

工作原理：
1. Python 端先调用 sentinel.openai.com/backend-api/sentinel/req 拿到 challenge JSON
2. 把 challenge 写入临时文件
3. 调用 node sentinel-runner.js --challenge-file <临时文件> ...
4. 捕获 stdout 即为 openai-sentinel-token 的 value
"""
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from config import (
    USER_AGENT,
    SEC_CH_UA_PLATFORM,  # noqa: F401（保留给后续扩展）
)

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_APP_ROOT = Path(getattr(sys, "_MEIPASS", _PROJECT_ROOT))
_RUNTIME_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else _PROJECT_ROOT
_SENTINEL_DIR = _APP_ROOT / "sentinel"
_RUNNER_PATH = _SENTINEL_DIR / "sentinel-runner.js"
_SDK_PATH = _SENTINEL_DIR / "sdk.js"

# 各 flow 对应的 page-url（与浏览器实际页面一致，影响 sdk.js 指纹生成）
_FLOW_PAGE_URL = {
    "username_password_create": "https://auth.openai.com/create-account/password",
    "authorize_continue": "https://auth.openai.com/email-verification",
    "oauth_create_account": "https://auth.openai.com/about-you",
}

# Node 子进程超时（秒）。sdk.js 内部可能要做 PoW，留充裕一点
_RUNNER_TIMEOUT = 60


def _candidate_node_paths() -> list[str]:
    binary_name = "node.exe" if sys.platform.startswith("win") else "node"
    candidates = [
        str(_RUNTIME_ROOT / "node" / binary_name),
        str(_APP_ROOT / "node" / binary_name),
        str(_PROJECT_ROOT / "node" / binary_name),
    ]

    if not sys.platform.startswith("win"):
        return candidates

    for key in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        root = os.environ.get(key)
        if root:
            candidates.append(str(Path(root) / "nodejs" / "node.exe"))
    candidates.extend([
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
    ])
    return candidates


def _resolve_node_executable() -> str:
    override = os.environ.get("NODE_EXECUTABLE")
    if override:
        return override

    for candidate in _candidate_node_paths():
        if Path(candidate).exists():
            return candidate

    names = ["node.exe", "node"] if sys.platform.startswith("win") else ["node"]
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved

    return "node.exe" if sys.platform.startswith("win") else "node"


def check_node_available() -> tuple[bool, str]:
    node = _resolve_node_executable()
    try:
        proc = subprocess.run(
            [node, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
    except FileNotFoundError:
        return False, _node_missing_message()
    except Exception as exc:
        return False, f"Node 环境检测失败：{type(exc).__name__}: {exc}"

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        return False, f"Node 环境检测失败：{detail or f'退出码 {proc.returncode}'}"

    return True, (proc.stdout or "").strip() or node


def _node_missing_message() -> str:
    return (
        "未找到 Node 可执行文件。打包版本请将 node/node.exe 放在程序目录或资源目录；"
        "开发环境请安装 Node.js LTS，或通过 NODE_EXECUTABLE 环境变量指定绝对路径。"
    )


def _ensure_runner_environment() -> None:
    """启动前的强制检查：runner.js / sdk.js 必须存在。"""
    if not _RUNNER_PATH.exists():
        raise FileNotFoundError(f"找不到 sentinel-runner.js: {_RUNNER_PATH}")
    if not _SDK_PATH.exists():
        raise FileNotFoundError(f"找不到 sdk.js: {_SDK_PATH}")


def generate_sentinel_token(
    challenge: dict,
    flow: str,
    device_id: str,
    user_agent: str | None = None,
    page_url: str | None = None,
) -> str:
    """
    把 sentinel.openai.com 返回的 challenge 喂给 sdk.js，生成最终 sentinel-token 字符串。

    Args:
        challenge: sentinel/req 返回的完整 JSON（含 token / proofofwork / turnstile / so 字段）
        flow: 流程标识，例如 username_password_create / authorize_continue / oauth_create_account
        device_id: oai-did，必须与 Python 端 BrowserSession 持有的同一个值
        user_agent: 必须与 Python 端请求 UA 完全一致；默认读取 config.USER_AGENT
        page_url: 当前所在页面 URL（影响 referer / location 指纹）；默认按 flow 推断

    Returns:
        openai-sentinel-token 头的完整字符串值（runner 的 stdout 原样返回，已是 JSON 字符串）

    Raises:
        FileNotFoundError: runner.js 或 sdk.js 缺失
        RuntimeError: Node 子进程异常或返回非零退出码
    """
    _ensure_runner_environment()

    if not flow:
        raise ValueError("flow 不能为空")
    if not device_id:
        raise ValueError("device_id 不能为空")

    ua = user_agent or USER_AGENT
    page = page_url or _FLOW_PAGE_URL.get(
        flow, "https://auth.openai.com/create-account/password"
    )

    # 把 challenge 写入临时文件，避免命令行长度 / 转义问题
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        prefix=f"sentinel-challenge-{flow}-",
        delete=False,
        encoding="utf-8",
    )
    try:
        json.dump(challenge, tmp, ensure_ascii=False)
        tmp.flush()
        tmp.close()

        cmd = [
            _resolve_node_executable(),
            str(_RUNNER_PATH),
            "--challenge-file", tmp.name,
            "--flow", flow,
            "--device-id", device_id,
            "--page-url", page,
            "--user-agent", ua,
            "--sdk", str(_SDK_PATH),
            # 与 core/sentinel.py 中的指纹默认值保持一致
            "--width", "1920",
            "--height", "1080",
            "--cores", "32",
            "--language", "en-US",
            "--languages", "en-US,en",
            "--no-cookie",
        ]

        logger.info(f"[SentinelRunner] 调用 Node 生成 token, flow={flow}")
        logger.debug(f"[SentinelRunner] 命令: {' '.join(cmd)}")

        # 关键：禁用 sentinel.config.json 自动发现（避免外部配置干扰）
        env = os.environ.copy()
        env.pop("SENTINEL_CONFIG", None)
        env["SENTINEL_CONFIG"] = "__none__"  # 故意指向不存在的文件，跳过 fallback 列表

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=str(_PROJECT_ROOT),
                timeout=_RUNNER_TIMEOUT,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"sentinel-runner.js 执行超时（>{_RUNNER_TIMEOUT}s），flow={flow}"
            ) from exc
        except FileNotFoundError as exc:
            raise RuntimeError(_node_missing_message()) from exc

        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            stdout = (proc.stdout or "").strip()
            raise RuntimeError(
                f"sentinel-runner.js 退出码 {proc.returncode}\n"
                f"stderr: {stderr}\n"
                f"stdout: {stdout}"
            )

        token_text = (proc.stdout or "").strip()
        if not token_text:
            raise RuntimeError(
                f"sentinel-runner.js 输出为空, stderr: {(proc.stderr or '').strip()}"
            )

        # 简单合法性校验：必须是合法 JSON 且包含关键字段
        try:
            parsed = json.loads(token_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"runner 输出不是合法 JSON: {token_text[:200]}"
            ) from exc

        for required_key in ("p", "c", "id", "flow"):
            if required_key not in parsed:
                raise RuntimeError(
                    f"runner 输出缺少字段 {required_key}: {token_text[:200]}"
                )

        # 详细诊断：打印输出 JSON 的所有顶层字段名 + 值长度
        field_summary = {
            k: (len(v) if isinstance(v, str) else type(v).__name__)
            for k, v in parsed.items()
        }
        logger.info(
            f"[SentinelRunner] token 生成成功, flow={flow}, "
            f"包含 turnstile={'t' in parsed and bool(parsed.get('t'))}, "
            f"包含 so={bool(parsed.get('so'))}, "
            f"字段: {field_summary}"
        )
        return token_text

    finally:
        # 清理临时文件
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

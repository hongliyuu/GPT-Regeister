# -*- coding: utf-8 -*-

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.widgets import multi_line_edit, section_label


class ProxyTestWorker(QThread):
    result_signal = Signal(int, int, list, bool)
    progress_signal = Signal(int, int)
    log_signal = Signal(str)

    def __init__(self, proxy_urls: list[str], max_workers: int = 10):
        super().__init__()
        self._proxy_urls = proxy_urls
        self._max_workers = max_workers
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        from curl_cffi.requests import Session as CurlSession
        from config import IMPERSONATE, REQUEST_TIMEOUT, USER_AGENT, SEC_CH_UA, SEC_CH_UA_PLATFORM, SEC_CH_UA_MOBILE

        headers = {
            "User-Agent": USER_AGENT,
            "sec-ch-ua": SEC_CH_UA,
            "sec-ch-ua-platform": SEC_CH_UA_PLATFORM,
            "sec-ch-ua-mobile": SEC_CH_UA_MOBILE,
            "accept": "*/*",
            "accept-language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://chatgpt.com/login",
            "priority": "u=1, i",
        }

        def _log(msg):
            self.log_signal.emit(f"[代理测试] {msg}")

        def _get_ip(url, session=None, **kwargs):
            s = session or CurlSession(impersonate=IMPERSONATE)
            s.timeout = kwargs.pop("timeout", REQUEST_TIMEOUT)
            return s.get(url, **kwargs)

        total = len(self._proxy_urls)
        finished = 0
        failed = []
        success_count = 0
        max_workers = min(self._max_workers, total)
        _log(f"开始并发测试全部代理，共 {total} 个，并发 {max_workers}")

        try:
            resp = _get_ip("https://httpbin.org/ip", timeout=15)
            _log(f"直连正常，本地出口 IP: {resp.json().get('origin', 'unknown')}")
        except Exception as e:
            _log(f"直连失败: {type(e).__name__}，本地网络可能异常")
            self.result_signal.emit(0, total, list(self._proxy_urls), False)
            return

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._test_proxy, proxy_url, headers, CurlSession, IMPERSONATE, REQUEST_TIMEOUT, _get_ip): proxy_url
                for proxy_url in self._proxy_urls
            }
            for future in as_completed(futures):
                proxy_url = futures[future]
                if self._stop_event.is_set():
                    for pending in futures:
                        pending.cancel()
                    break
                finished += 1
                self.progress_signal.emit(finished, total)
                try:
                    ok, message = future.result()
                except Exception as e:
                    ok = False
                    message = f"测试异常 ({type(e).__name__})"
                if ok:
                    success_count += 1
                    _log(f"[{finished}/{total}] 可用: `{proxy_url}`，{message}")
                else:
                    failed.append(proxy_url)
                    _log(f"[{finished}/{total}] 不可用: `{proxy_url}`，{message}")

        stopped = self._stop_event.is_set()
        if stopped:
            _log(f"测试已停止，已完成 {finished}/{total}")
        self.result_signal.emit(success_count, total, failed, stopped)

    def _test_proxy(self, proxy_url, headers, curl_session_cls, impersonate, request_timeout, get_ip):
        if self._stop_event.is_set():
            return False, "已停止"

        session = curl_session_cls(impersonate=impersonate)
        session.timeout = request_timeout
        session.proxies = {"http": proxy_url, "https": proxy_url}

        resp = None
        try:
            resp = get_ip("http://httpbin.org/ip", session=session, timeout=15)
            http_ip = resp.json().get("origin", "unknown")
        except Exception as e:
            hint = f"{type(e).__name__}"
            if hasattr(e, "response") and e.response is not None:
                hint = f"HTTP {e.response.status_code}"
            elif resp is not None and hasattr(resp, "status_code"):
                hint = f"HTTP {resp.status_code}"
            return False, f"HTTP 测试失败 ({hint})"

        if self._stop_event.is_set():
            return False, "已停止"

        resp = None
        try:
            resp = get_ip("https://chatgpt.com/api/auth/providers", session=session, headers=headers, timeout=15)
            providers = list(resp.json().keys())
            return True, f"chatgpt.com HTTPS 正常，HTTP 出口 IP: {http_ip}，providers: {providers}"
        except Exception:
            pass

        if self._stop_event.is_set():
            return False, "已停止"

        resp = None
        try:
            resp = get_ip("https://httpbin.org/ip", session=session, timeout=15)
            https_ip = resp.json().get("origin", "unknown")
            return True, f"HTTPS 可用，出口 IP: {https_ip}，但 chatgpt.com 可能被限制"
        except Exception:
            status = f"HTTP {resp.status_code}" if resp is not None and hasattr(resp, "status_code") else "连接失败"
            return False, f"HTTPS 测试失败 ({status})"


class ProxyTab(QWidget):
    test_log_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._test_worker: ProxyTestWorker | None = None

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(12)
        l.setContentsMargins(12, 16, 24, 16)

        l.addWidget(section_label("代理池"))
        hint = QLabel("每行一个代理 URL，支持 http / https / socks5 / socks5h；留空不使用代理")
        hint.setStyleSheet("color: #606080; font-size: 12px; margin-bottom: 4px;")
        l.addWidget(hint)

        hint2 = QLabel("也可直接粘贴 host:port:user:pass 格式，自动转换为标准格式")
        hint2.setStyleSheet("color: #808099; font-size: 11px; margin-bottom: 8px;")
        l.addWidget(hint2)

        remark = QLabel("V2Ray 代理请开启 TUN 模式，Clash 代理请开启虚拟网卡模式")
        remark.setStyleSheet("color: #808099; font-size: 11px; margin-bottom: 8px;")
        l.addWidget(remark)

        self.proxy_edit = multi_line_edit(
            placeholder="http://user:pass@host:port", max_h=99999
        )
        l.addWidget(self.proxy_edit)

        btn_row = QHBoxLayout()
        self.test_btn = QPushButton("测试全部代理")
        self.test_btn.setObjectName("PrimaryBtn")
        self.test_btn.setToolTip("依次测试代理池中的全部代理")

        self.stop_btn = QPushButton("停止测试")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setToolTip("停止当前代理测试任务")

        self.format_btn = QPushButton("格式转换")
        self.format_btn.setToolTip("将 host:port:user:pass 转换为标准 http://user:pass@host:port")

        self.test_status = QLabel("")
        self.test_status.setStyleSheet("color: #34d399; font-size: 12px;")

        btn_row.addWidget(self.test_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.format_btn)
        btn_row.addWidget(self.test_status)
        btn_row.addStretch()
        l.addLayout(btn_row)

        scroll.setWidget(w)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self.setLayout(layout)

        self.test_btn.clicked.connect(self._run_test)
        self.stop_btn.clicked.connect(self._stop_test)
        self.format_btn.clicked.connect(self._format_lines)

    @staticmethod
    def _normalize_line(line: str) -> str:
        line = line.strip()
        if not line or "://" in line:
            return line
        parts = line.split(":")
        if len(parts) == 4:
            host, port, user, pwd = parts
            return f"http://{user}:{pwd}@{host}:{port}"
        return line

    def _format_lines(self):
        lines = self.proxy_edit.toPlainText().splitlines()
        converted = [self._normalize_line(l) for l in lines]
        self.proxy_edit.setPlainText("\n".join(converted))
        self.test_status.setText("格式转换完成")
        self.test_status.setStyleSheet("color: #34d399; font-size: 12px;")

    def load_config(self, cfg: dict):
        p = cfg.get("proxy", {})
        lines = p.get("pool", [])
        self.proxy_edit.setPlainText("\n".join(self._normalize_line(l) for l in lines))

    def collect_config(self, cfg: dict):
        cfg["proxy"] = {
            "pool": [
                self._normalize_line(line)
                for line in self.proxy_edit.toPlainText().strip().splitlines()
                if line.strip()
            ]
        }

    def _run_test(self):
        proxies = [
            self._normalize_line(line)
            for line in self.proxy_edit.toPlainText().splitlines()
            if line.strip()
        ]
        if not proxies:
            QMessageBox.information(self, "提示", "请在代理池中至少输入一行代理 URL")
            return

        self.proxy_edit.setPlainText("\n".join(proxies))
        self.test_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.format_btn.setEnabled(False)
        self.test_status.setText(f"正在测试 0/{len(proxies)}...")
        self.test_status.setStyleSheet("color: #f59e0b; font-size: 12px;")

        self._test_worker = ProxyTestWorker(proxies)
        self._test_worker.log_signal.connect(self.test_log_signal)
        self._test_worker.progress_signal.connect(self._on_test_progress)
        self._test_worker.result_signal.connect(self._on_test_result)
        self._test_worker.start()

    def _stop_test(self):
        if self._test_worker and self._test_worker.isRunning():
            self._test_worker.stop()
            self.stop_btn.setEnabled(False)
            self.test_status.setText("正在停止...")
            self.test_status.setStyleSheet("color: #f59e0b; font-size: 12px;")

    def _on_test_progress(self, current: int, total: int):
        self.test_status.setText(f"正在测试 {current}/{total}...")

    def _on_test_result(self, success_count: int, total: int, failed: list, stopped: bool):
        self.test_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.format_btn.setEnabled(True)
        failed_count = len(failed)
        success = failed_count == 0 and not stopped
        color = "#34d399" if success else "#ef4444"
        message = f"测试完成：可用 {success_count}/{total}"
        if stopped:
            message = f"测试已停止：已测 {success_count + failed_count}/{total}，可用 {success_count}"
        elif failed_count:
            message += f"，无用 {failed_count} 个"
        self.test_status.setText(message)
        self.test_status.setStyleSheet(f"color: {color}; font-size: 12px;")

        if stopped:
            return

        if not failed_count:
            QMessageBox.information(self, "代理测试完成", "全部代理测试通过")
            return

        answer = QMessageBox.question(
            self,
            "删除无用代理",
            f"检测到 {failed_count} 个代理不可用，是否从代理池中删除？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if answer != QMessageBox.Yes:
            return

        failed_set = set(failed)
        kept = [
            self._normalize_line(line)
            for line in self.proxy_edit.toPlainText().splitlines()
            if line.strip() and self._normalize_line(line) not in failed_set
        ]
        self.proxy_edit.setPlainText("\n".join(kept))
        self.test_status.setText(f"已删除 {failed_count} 个无用代理，剩余 {len(kept)} 个")
        self.test_status.setStyleSheet("color: #34d399; font-size: 12px;")

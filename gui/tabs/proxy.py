# -*- coding: utf-8 -*-
import logging

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
    result_signal = Signal(bool, str)

    def __init__(self, proxy_url: str):
        super().__init__()
        self._proxy_url = proxy_url

    def run(self):
        try:
            import urllib.request
            proxy_handler = urllib.request.ProxyHandler({
                "http": self._proxy_url,
                "https": self._proxy_url,
            })
            opener = urllib.request.build_opener(proxy_handler, urllib.request.ProxyHandler({}))
            req = urllib.request.Request("https://httpbin.org/ip", method="GET")
            req.timeout = 15
            resp = opener.open(req)
            data = resp.read().decode()
            import json
            ip = json.loads(data).get("origin", "unknown")
            self.result_signal.emit(True, f"代理可用，出口 IP: {ip}")
        except Exception as e:
            self.result_signal.emit(False, f"代理测试失败: {type(e).__name__}: {e}")


class ProxyTab(QWidget):
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
        hint = QLabel("每行一个代理 URL，支持 http / https / socks5 / socks5h")
        hint.setStyleSheet("color: #606080; font-size: 12px; margin-bottom: 8px;")
        l.addWidget(hint)

        self.proxy_edit = multi_line_edit(
            placeholder="http://user:pass@host:port", max_h=99999
        )
        l.addWidget(self.proxy_edit)

        # 测试按钮
        test_row = QHBoxLayout()
        self.test_btn = QPushButton("测试所选代理")
        self.test_btn.setObjectName("PrimaryBtn")
        self.test_btn.setToolTip("使用首行代理测试网络连通性")
        self.test_status = QLabel("")
        self.test_status.setStyleSheet("color: #34d399; font-size: 12px;")
        test_row.addWidget(self.test_btn)
        test_row.addWidget(self.test_status)
        test_row.addStretch()
        l.addLayout(test_row)

        scroll.setWidget(w)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self.setLayout(layout)

        self.test_btn.clicked.connect(self._run_test)

    def load_config(self, cfg: dict):
        p = cfg.get("proxy", {})
        self.proxy_edit.setPlainText("\n".join(p.get("pool", [])))

    def collect_config(self, cfg: dict):
        cfg["proxy"] = {
            "pool": [
                line.strip()
                for line in self.proxy_edit.toPlainText().strip().splitlines()
                if line.strip()
            ]
        }

    def _run_test(self):
        raw = self.proxy_edit.toPlainText().strip()
        if not raw:
            QMessageBox.information(self, "提示", "请在代理池中至少输入一行代理 URL")
            return
        first = raw.splitlines()[0].strip()
        if not first:
            QMessageBox.information(self, "提示", "请输入有效的代理 URL")
            return

        self.test_btn.setEnabled(False)
        self.test_status.setText("正在测试...")
        self.test_status.setStyleSheet("color: #f59e0b; font-size: 12px;")

        self._test_worker = ProxyTestWorker(first)
        self._test_worker.result_signal.connect(self._on_test_result)
        self._test_worker.start()

    def _on_test_result(self, success: bool, message: str):
        self.test_btn.setEnabled(True)
        color = "#34d399" if success else "#ef4444"
        self.test_status.setText(message)
        self.test_status.setStyleSheet(f"color: {color}; font-size: 12px;")

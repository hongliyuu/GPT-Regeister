# -*- coding: utf-8 -*-
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.widgets import check, combo, line_edit, multi_line_edit, spin

_ALIAS_MODES = [
    ("后缀追加", "append_random"),
    ("前缀追加", "prefix_random"),
    ("完全随机", "full_random"),
]

_DOMAIN_MODES = [
    ("使用登录邮箱域名", "default"),
    ("域名转发", "forward"),
]


def _chinese_to_mode(chinese: str) -> str:
    for cn, en in _ALIAS_MODES:
        if cn == chinese:
            return en
    return "append_random"


def _mode_to_chinese(mode: str) -> str:
    for cn, en in _ALIAS_MODES:
        if en == mode:
            return cn
    return "后缀追加"


def _chinese_to_domain_mode(chinese: str) -> str:
    for cn, en in _DOMAIN_MODES:
        if cn == chinese:
            return en
    return "default"


def _domain_mode_to_chinese(mode: str) -> str:
    for cn, en in _DOMAIN_MODES:
        if en == mode:
            return cn
    return "使用登录邮箱域名"


class TestIMAPWorker(QThread):
    result_signal = Signal(bool, str)

    def __init__(self, email: str, password: str, host: str, port: int, use_ssl: bool):
        super().__init__()
        self._email = email
        self._password = password
        self._host = host
        self._port = port
        self._ssl = use_ssl

    def run(self):
        import imaplib
        import ssl as ssl_mod
        try:
            if self._ssl:
                ctx = ssl_mod.create_default_context()
                conn = imaplib.IMAP4_SSL(self._host, self._port, ssl_context=ctx, timeout=15)
            else:
                conn = imaplib.IMAP4(self._host, self._port, timeout=15)
            conn.login(self._email, self._password)
            conn.select("INBOX")
            status, data = conn.search(None, "ALL")
            count = len(data[0].split()) if data[0] else 0
            conn.logout()
            self.result_signal.emit(True, f"连接成功！{self._email}，收件箱共 {count} 封邮件")
        except Exception as e:
            self.result_signal.emit(False, f"连接失败: {e}")


class EmailTab(QWidget):
    provider_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._test_worker: TestIMAPWorker | None = None
        self._all_groups: dict[str, QWidget] = {}
        self._alias_signals_connected = False

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        self._root_layout = QVBoxLayout(w)
        self._root_layout.setSpacing(12)
        self._root_layout.setContentsMargins(12, 16, 24, 16)

        self._build_provider()
        self._build_imap()
        self._build_outlook()
        self._build_manual_hint()
        self._build_otp()
        self._root_layout.addStretch()

        scroll.setWidget(w)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self.setLayout(layout)

        self.email_provider_combo.currentTextChanged.connect(self._on_provider_changed)
        self.imap_alias_mode_combo.currentTextChanged.connect(self._on_alias_mode_changed)
        self.imap_domain_mode_combo.currentTextChanged.connect(self._on_domain_mode_changed)
        self.imap_alias_domain_edit.textChanged.connect(self._update_alias_preview)
        self.imap_email_edit.textChanged.connect(self._update_alias_preview)
        self.test_btn.clicked.connect(self._run_imap_test)

        self._on_provider_changed("imap")
        self._on_alias_mode_changed("append_random")
        self._on_domain_mode_changed("使用登录邮箱域名")

    # ── Provider ──

    def _build_provider(self):
        pg = QGroupBox("Provider")
        pf = QFormLayout(pg)
        pf.setSpacing(10)
        pf.setContentsMargins(16, 24, 16, 16)
        self.email_provider_combo = combo(["imap", "outlook_oauth", "manual"])
        pf.addRow("Provider 类型", self.email_provider_combo)
        self._root_layout.addWidget(pg)

    # ── IMAP ──

    def _build_imap(self):
        self._imap_group = QGroupBox("IMAP 配置")
        self._imap_group.hide()
        l = QVBoxLayout(self._imap_group)
        l.setSpacing(10)
        l.setContentsMargins(16, 24, 16, 16)

        # 登录凭据
        cred_g = self._make_sub_group("登录邮箱")
        cred_f = QFormLayout(cred_g)
        cred_f.setSpacing(8)
        self.imap_email_edit = line_edit(placeholder="user@2925.com")
        self.imap_password_edit = line_edit(placeholder="邮箱密码或授权码")
        self.imap_password_edit.setEchoMode(line_edit().EchoMode.Password)
        cred_f.addRow("邮箱", self.imap_email_edit)
        cred_f.addRow("密码", self.imap_password_edit)

        test_row = QHBoxLayout()
        self.test_btn = QPushButton("测试连接")
        self.test_btn.setObjectName("PrimaryBtn")
        self.test_status = QLabel("")
        self.test_status.setStyleSheet("color: #34d399; font-size: 12px;")
        test_row.addWidget(self.test_btn)
        test_row.addWidget(self.test_status)
        test_row.addStretch()
        cred_f.addRow("", test_row)
        l.addWidget(cred_g)

        # 服务器配置
        srv_g = self._make_sub_group("服务器")
        srv_f = QFormLayout(srv_g)
        srv_f.setSpacing(8)
        self.imap_host_edit = line_edit(placeholder="imap.2925.com")
        self.imap_port_spin = spin(1, 65535, 993)
        self.imap_ssl_check = check("SSL 加密")
        self.imap_mailbox_edit = line_edit(placeholder="INBOX")
        srv_f.addRow("IMAP 主机", self.imap_host_edit)
        srv_f.addRow("端口", self.imap_port_spin)
        srv_f.addRow("", self.imap_ssl_check)
        srv_f.addRow("邮箱目录", self.imap_mailbox_edit)
        l.addWidget(srv_g)

        # 注册地址配置
        alias_g = QGroupBox("注册地址规则")
        alias_g.setObjectName("AliasGroup")
        alias_l = QVBoxLayout(alias_g)
        alias_l.setContentsMargins(12, 20, 12, 12)
        alias_l.setSpacing(8)

        alias_hint = QLabel("注册时始终生成随机地址：支持别名的邮箱可用前后缀追加，域名转发邮箱建议使用完全随机。")
        alias_hint.setWordWrap(True)
        alias_hint.setStyleSheet("color: #808090; font-size: 12px;")
        alias_l.addWidget(alias_hint)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("地址生成方式："))
        self.imap_alias_mode_combo = combo([c for c, _ in _ALIAS_MODES])
        mode_row.addWidget(self.imap_alias_mode_combo)
        mode_row.addStretch()
        alias_l.addLayout(mode_row)

        # 域名方式
        domain_mode_row = QHBoxLayout()
        domain_mode_row.addWidget(QLabel("收件方式："))
        self.imap_domain_mode_combo = combo([c for c, _ in _DOMAIN_MODES])
        domain_mode_row.addWidget(self.imap_domain_mode_combo)
        domain_mode_row.addStretch()
        alias_l.addLayout(domain_mode_row)

        # 域名转发输入（仅域名转发时显示）
        self._domain_forward_row = self._wrap_widget(QHBoxLayout())
        _df = self._domain_forward_row.layout()
        _df.addWidget(QLabel("转发域名："))
        self.imap_alias_domain_edit = line_edit(placeholder="catchall.com")
        self.imap_alias_domain_edit.setMaximumWidth(280)
        _df.addWidget(self.imap_alias_domain_edit)
        _df.addStretch()
        self._domain_forward_row.hide()
        alias_l.addWidget(self._domain_forward_row)

        # 分隔符
        sep_row = QHBoxLayout()
        sep_row.addWidget(QLabel("分隔符："))
        self.imap_alias_sep_edit = line_edit(placeholder=".")
        self.imap_alias_sep_edit.setMaximumWidth(80)
        sep_row.addWidget(self.imap_alias_sep_edit)
        sep_row.addStretch()
        self._alias_sep_row = self._wrap_widget(sep_row)
        alias_l.addWidget(self._alias_sep_row)

        # 随机长度
        len_row = QHBoxLayout()
        len_row.addWidget(QLabel("随机串长度："))
        self.imap_alias_len_spin = spin(3, 32, 6)
        len_row.addWidget(self.imap_alias_len_spin)
        len_row.addStretch()
        self._alias_len_row = self._wrap_widget(len_row)
        alias_l.addWidget(self._alias_len_row)

        # 预览
        self._alias_preview = QLabel("")
        self._alias_preview.setStyleSheet("color: #6366f1; font-size: 12px; font-weight: 600;")
        alias_l.addWidget(self._alias_preview)

        l.addWidget(alias_g)
        self._root_layout.addWidget(self._imap_group)
        self._all_groups["imap"] = self._imap_group

    @staticmethod
    def _wrap_widget(layout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    @staticmethod
    def _make_sub_group(title: str) -> QGroupBox:
        g = QGroupBox(title)
        g.setStyleSheet("QGroupBox { font-weight: 500; color: #a0a0c0; }")
        return g

    # ── Outlook ──

    def _build_outlook(self):
        self._outlook_group = QGroupBox("Outlook 配置")
        self._outlook_group.hide()
        l = QVBoxLayout(self._outlook_group)
        l.setSpacing(10)
        l.setContentsMargins(16, 24, 16, 16)

        self.outlook_api_base_edit = line_edit(placeholder="https://mail.chatai.codes")

        l.addWidget(QLabel("API Base URL："))
        l.addWidget(self.outlook_api_base_edit)
        l.addWidget(QLabel("账号列表（每行一个，格式：邮箱----密码----clientId----refreshToken）："))
        self.outlook_accounts_edit = multi_line_edit(
            placeholder="user@outlook.com----password----9e5f94bc-...----M.C529_...",
            max_h=99999,
        )
        l.addWidget(self.outlook_accounts_edit)

        self._root_layout.addWidget(self._outlook_group)
        self._all_groups["outlook_oauth"] = self._outlook_group

    # ── Manual ──

    def _build_manual_hint(self):
        self._manual_group = QGroupBox("手动模式")
        self._manual_group.hide()
        l = QVBoxLayout(self._manual_group)
        l.setContentsMargins(16, 24, 16, 20)
        hint = QLabel("手动模式下需要手动填写注册邮箱、姓名，并在注册过程中手动输入验证码。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #808090; font-size: 13px;")
        l.addWidget(hint)
        self._root_layout.addWidget(self._manual_group)
        self._all_groups["manual"] = self._manual_group

    # ── OTP ──

    def _build_otp(self):
        self._otp_group = QGroupBox("OTP 轮询参数")
        otf = QFormLayout(self._otp_group)
        otf.setSpacing(10)
        otf.setContentsMargins(16, 24, 16, 16)
        self.otp_interval_spin = spin(1, 60, 3)
        self.otp_max_wait_spin = spin(10, 600, 90)
        self.otp_settle_spin = spin(1, 30, 5)
        otf.addRow("轮询间隔 (秒)", self.otp_interval_spin)
        otf.addRow("最大等待 (秒)", self.otp_max_wait_spin)
        otf.addRow("沉降时间 (秒)", self.otp_settle_spin)
        self._root_layout.addWidget(self._otp_group)
        self._all_groups["otp"] = self._otp_group

    # ── Provider 切换 ──

    def _on_provider_changed(self, provider: str):
        for key, group in self._all_groups.items():
            if key == "otp":
                group.setVisible(provider != "manual")
            else:
                group.setVisible(key == provider)
        self.provider_changed.emit(provider)

    # ── 别名模式切换 ──

    def _on_domain_mode_changed(self, chinese: str):
        mode = _chinese_to_domain_mode(chinese)
        is_forward = mode == "forward"

        self._domain_forward_row.setVisible(is_forward)

        if is_forward:
            self.imap_alias_mode_combo.setCurrentText("完全随机")
            self.imap_alias_mode_combo.setEnabled(False)
            self.imap_alias_sep_edit.setEnabled(False)
        else:
            self.imap_alias_mode_combo.setEnabled(True)
            self.imap_alias_sep_edit.setEnabled(True)

        self._update_alias_preview()

    def _on_alias_mode_changed(self, chinese: str):
        mode = _chinese_to_mode(chinese)
        is_full = mode == "full_random"

        self._alias_sep_row.setVisible(not is_full)
        self._alias_len_row.setVisible(True)

        if self._alias_signals_connected:
            self.imap_alias_sep_edit.textChanged.disconnect(self._update_alias_preview)
            self.imap_alias_len_spin.valueChanged.disconnect(self._update_alias_preview)

        self.imap_alias_sep_edit.textChanged.connect(self._update_alias_preview)
        self.imap_alias_len_spin.valueChanged.connect(self._update_alias_preview)
        self._alias_signals_connected = True
        self._update_alias_preview()

    def _update_alias_preview(self):
        import random, string
        chinese = self.imap_alias_mode_combo.currentText()
        mode = _chinese_to_mode(chinese)
        domain_chinese = self.imap_domain_mode_combo.currentText()
        domain_mode = _chinese_to_domain_mode(domain_chinese)
        length = self.imap_alias_len_spin.value()
        separator = self.imap_alias_sep_edit.text()

        email = self.imap_email_edit.text() or "user@example.com"
        local, sep, domain = email.partition("@")
        if not sep:
            self._alias_preview.setText("（请先输入邮箱）")
            return

        if domain_mode == "forward":
            alias_domain = self.imap_alias_domain_edit.text().strip()
            if alias_domain:
                target_domain = alias_domain
            else:
                target_domain = domain + " (未设置转发域名)"
        else:
            target_domain = domain

        demo_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

        if mode == "full_random":
            alias = f"{demo_suffix}@{target_domain}"
        elif mode == "append_random":
            alias = f"{local}{separator}{demo_suffix}@{target_domain}"
        else:
            alias = f"{demo_suffix}{separator}{local}@{target_domain}"
        self._alias_preview.setText(f"示例注册地址：{alias}")

    # ── 配置加载 ──

    def load_config(self, cfg: dict):
        e = cfg.get("email", {})
        self.email_provider_combo.setCurrentText(e.get("provider", "imap"))

        imap = e.get("imap", {})
        self.imap_email_edit.setText(imap.get("login_email", ""))
        self.imap_password_edit.setText(imap.get("login_password", ""))
        self.imap_host_edit.setText(imap.get("host", ""))
        self.imap_port_spin.setValue(imap.get("port", 993))
        self.imap_ssl_check.setChecked(imap.get("ssl", True))
        self.imap_mailbox_edit.setText(imap.get("mailbox", "INBOX"))
        self.imap_alias_mode_combo.setCurrentText(_mode_to_chinese(imap.get("alias_mode", "append_random")))
        self.imap_domain_mode_combo.setCurrentText(_domain_mode_to_chinese(imap.get("alias_domain_mode", "default")))
        self.imap_alias_domain_edit.setText(imap.get("alias_domain", ""))
        self.imap_alias_len_spin.setValue(imap.get("alias_random_length", 6))
        self.imap_alias_sep_edit.setText(imap.get("alias_separator", ""))

        outlook = e.get("outlook", {})
        self.outlook_api_base_edit.setText(outlook.get("api_base", ""))
        outlook_accounts = outlook.get("accounts", [])
        lines = []
        for item in outlook_accounts:
            if isinstance(item, dict) and item.get("email"):
                lines.append("----".join([
                    item.get("email", ""),
                    item.get("password", ""),
                    item.get("client_id", ""),
                    item.get("refresh_token", ""),
                ]))
        self.outlook_accounts_edit.setPlainText("\n".join(lines))

    # ── 配置收集 ──

    def collect_config(self, cfg: dict):
        provider = self.email_provider_combo.currentText()
        mode = _chinese_to_mode(self.imap_alias_mode_combo.currentText())
        domain_mode = _chinese_to_domain_mode(self.imap_domain_mode_combo.currentText())

        outlook_accounts = []
        for raw in self.outlook_accounts_edit.toPlainText().strip().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("----")]
            if len(parts) >= 4:
                outlook_accounts.append({
                    "email": parts[0],
                    "password": parts[1],
                    "client_id": parts[2],
                    "refresh_token": parts[3],
                })

        cfg["email"] = {
            "provider": provider,
            "use_email_service": provider != "manual",
            "email_source": provider,
            "outlook": {
                "api_base": self.outlook_api_base_edit.text(),
                "accounts": outlook_accounts,
            },
            "imap": {
                "login_email": self.imap_email_edit.text(),
                "login_password": self.imap_password_edit.text(),
                "host": self.imap_host_edit.text(),
                "port": self.imap_port_spin.value(),
                "ssl": self.imap_ssl_check.isChecked(),
                "mailbox": self.imap_mailbox_edit.text(),
                "alias_enabled": True,
                "alias_mode": mode,
                "alias_domain_mode": domain_mode,
                "alias_domain": self.imap_alias_domain_edit.text().strip(),
                "alias_random_length": self.imap_alias_len_spin.value(),
                "alias_separator": self.imap_alias_sep_edit.text(),
            },
            "otp": {
                "poll_interval": self.otp_interval_spin.value(),
                "max_wait": self.otp_max_wait_spin.value(),
                "settle_seconds": self.otp_settle_spin.value(),
            },
        }

    # ── IMAP 测试 ──

    def _run_imap_test(self):
        email = self.imap_email_edit.text().strip()
        password = self.imap_password_edit.text()
        if not email or not password:
            QMessageBox.information(self, "提示", "请先输入邮箱和密码")
            return

        host = self.imap_host_edit.text() or "imap.2925.com"
        port = self.imap_port_spin.value()
        use_ssl = self.imap_ssl_check.isChecked()

        self.test_btn.setEnabled(False)
        self.test_status.setText("正在连接...")
        self.test_status.setStyleSheet("color: #f59e0b; font-size: 12px;")

        self._test_worker = TestIMAPWorker(email, password, host, port, use_ssl)
        self._test_worker.result_signal.connect(self._on_imap_test_result)
        self._test_worker.start()

    def _on_imap_test_result(self, success: bool, message: str):
        self.test_btn.setEnabled(True)
        color = "#34d399" if success else "#ef4444"
        self.test_status.setText(message)
        self.test_status.setStyleSheet(f"color: {color}; font-size: 12px;")

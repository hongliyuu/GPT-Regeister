# -*- coding: utf-8 -*-
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.widgets import check, line_edit, spin


class RegisterTab(QWidget):
    run_registration = Signal(int, int, bool)

    def __init__(self):
        super().__init__()
        self._manual_mode = False
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_w = QWidget()
        l = QVBoxLayout(form_w)
        l.setSpacing(12)
        l.setContentsMargins(12, 16, 24, 16)

        # 注册信息
        info_g = QGroupBox("注册默认信息")
        f = QFormLayout(info_g)
        f.setSpacing(10)
        f.setContentsMargins(16, 24, 16, 16)
        self.reg_email_edit = line_edit(placeholder="留空则从邮箱池领取")
        self.reg_name_edit = line_edit(placeholder="留空则随机生成英文姓名")
        self.reg_birthday_edit = line_edit(placeholder="2000-01-01")

        self._register_email_row = QWidget()
        email_row_layout = QVBoxLayout(self._register_email_row)
        email_row_layout.setContentsMargins(0, 0, 0, 0)
        email_row_layout.addWidget(self.reg_email_edit)

        self._register_name_row = QWidget()
        name_row_layout = QVBoxLayout(self._register_name_row)
        name_row_layout.setContentsMargins(0, 0, 0, 0)
        name_row_layout.addWidget(self.reg_name_edit)

        f.addRow("注册邮箱", self._register_email_row)
        f.addRow("姓名", self._register_name_row)
        f.addRow("默认生日", self.reg_birthday_edit)
        self.register_info_group = info_g
        self.register_info_form = f
        l.addWidget(info_g)

        # 运行参数
        run_g = QGroupBox("运行参数")
        rf = QFormLayout(run_g)
        rf.setSpacing(10)
        rf.setContentsMargins(16, 24, 16, 16)
        self.runs_spin = spin(1, 100, 1)
        self.workers_spin = spin(1, 20, 1)
        self.workers_spin.setToolTip("并发注册线程数，需配合邮箱自动取件使用")
        self.continue_on_fail_check = check("单个失败后继续注册下一个", False)
        rf.addRow("注册轮次", self.runs_spin)
        rf.addRow("并发线程数", self.workers_spin)
        rf.addRow("", self.continue_on_fail_check)
        l.addWidget(run_g)

        # 启动按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.start_btn = QPushButton("开始注册")
        self.start_btn.setObjectName("SuccessBtn")
        self.start_btn.setToolTip("保存配置并立即执行注册流程")
        self.start_btn.setMinimumWidth(160)
        btn_row.addWidget(self.start_btn)
        l.addLayout(btn_row)

        l.addStretch()
        scroll.setWidget(form_w)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self.setLayout(layout)

        self.start_btn.clicked.connect(self._on_start)
        self._apply_mode()

    def _apply_mode(self):
        self._set_manual_fields_visible(self._manual_mode)
        if self._manual_mode:
            self.register_info_group.setTitle("手动注册信息")
            self.reg_email_edit.setPlaceholderText("必填：手动输入注册邮箱")
            self.reg_name_edit.setPlaceholderText("必填：手动输入姓名")
            self.runs_spin.setValue(1)
            self.runs_spin.setEnabled(False)
            self.workers_spin.setValue(1)
            self.workers_spin.setEnabled(False)
            self.continue_on_fail_check.setChecked(False)
            self.continue_on_fail_check.setEnabled(False)
        else:
            self.register_info_group.setTitle("注册默认信息")
            self.reg_email_edit.setPlaceholderText("留空则从邮箱池领取")
            self.reg_name_edit.setPlaceholderText("留空则随机生成英文姓名")
            self.runs_spin.setEnabled(True)
            self.workers_spin.setEnabled(True)
            self.continue_on_fail_check.setEnabled(True)

    def _set_manual_fields_visible(self, visible: bool):
        self._register_email_row.setVisible(visible)
        self._register_name_row.setVisible(visible)
        if hasattr(self.register_info_form, "labelForField"):
            email_label = self.register_info_form.labelForField(self._register_email_row)
            name_label = self.register_info_form.labelForField(self._register_name_row)
            if email_label is not None:
                email_label.setVisible(visible)
            if name_label is not None:
                name_label.setVisible(visible)

    def set_manual_mode(self, manual: bool):
        self._manual_mode = manual
        self._apply_mode()

    def _on_start(self):
        self.run_registration.emit(
            self.runs_spin.value(),
            self.workers_spin.value(),
            self.continue_on_fail_check.isChecked(),
        )

    def set_running(self, running: bool):
        self.start_btn.setEnabled(not running)

    def load_config(self, cfg: dict):
        r = cfg.get("register", {})
        self.reg_email_edit.setText(r.get("email", ""))
        self.reg_name_edit.setText(r.get("name", ""))
        self.reg_birthday_edit.setText(r.get("birthday", "2000-01-01"))
        self.runs_spin.setValue(r.get("runs", 1))
        self.workers_spin.setValue(r.get("workers", 1))
        self.continue_on_fail_check.setChecked(r.get("continue_on_fail", False))
        manual = cfg.get("email", {}).get("provider", "imap") == "manual"
        self.set_manual_mode(manual)

    def collect_config(self, cfg: dict):
        cfg["register"] = {
            "email": self.reg_email_edit.text(),
            "password": "",
            "name": self.reg_name_edit.text(),
            "birthday": self.reg_birthday_edit.text(),
            "runs": self.runs_spin.value(),
            "workers": self.workers_spin.value(),
            "continue_on_fail": self.continue_on_fail_check.isChecked(),
        }

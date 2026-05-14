# -*- coding: utf-8 -*-
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.widgets import line_edit, spin


class RegisterTab(QWidget):
    run_registration = Signal(int)

    def __init__(self):
        super().__init__()
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
        self.reg_name_edit = line_edit(placeholder="留空则随机生成英文名")
        self.reg_birthday_edit = line_edit(placeholder="2000-01-01")
        f.addRow("默认邮箱", self.reg_email_edit)
        f.addRow("默认显示名称", self.reg_name_edit)
        f.addRow("默认生日", self.reg_birthday_edit)
        l.addWidget(info_g)

        # 运行参数
        run_g = QGroupBox("运行参数")
        rf = QFormLayout(run_g)
        rf.setSpacing(10)
        rf.setContentsMargins(16, 24, 16, 16)
        self.runs_spin = spin(1, 100, 1)
        rf.addRow("注册轮次", self.runs_spin)
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

    def _on_start(self):
        self.run_registration.emit(self.runs_spin.value())

    def set_running(self, running: bool):
        self.start_btn.setEnabled(not running)

    def load_config(self, cfg: dict):
        r = cfg.get("register", {})
        self.reg_email_edit.setText(r.get("email", ""))
        self.reg_name_edit.setText(r.get("name", ""))
        self.reg_birthday_edit.setText(r.get("birthday", "2000-01-01"))
        self.runs_spin.setValue(r.get("runs", 1))

    def collect_config(self, cfg: dict):
        cfg["register"] = {
            "email": self.reg_email_edit.text(),
            "password": "",
            "name": self.reg_name_edit.text(),
            "birthday": self.reg_birthday_edit.text(),
            "runs": self.runs_spin.value(),
        }

# -*- coding: utf-8 -*-
import sys
import ctypes
import ctypes.wintypes
from pathlib import Path

from PySide6.QtCore import QEvent, QSettings, Qt, QPoint
from PySide6.QtGui import QColor, QCloseEvent, QFont, QGuiApplication, QIcon, QMouseEvent, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.styles import DARK_THEME, LIGHT_THEME
from gui.worker import RegistrationWorker
from gui.tabs.register import RegisterTab
from gui.tabs.email import EmailTab
from gui.tabs.browser import BrowserTab
from gui.tabs.openai import OpenAITab
from gui.tabs.proxy import ProxyTab
from gui.tabs.flow import FlowTab
from gui.tabs.twofa import TwoFATab


_BORDER_WIDTH = 6
_SETTINGS_ORG = "GPT-Regeister"
_SETTINGS_APP = "ConfigEditor"


class NoWheelTabWidget(QTabWidget):
    def wheelEvent(self, event):
        event.ignore()


class TitleBar(QWidget):
    def __init__(self, parent: "ConfigEditor"):
        super().__init__(parent)
        self._window = parent
        self._dragging = False
        self._drag_pos = None
        self.setObjectName("TitleBar")
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 4, 0)
        layout.setSpacing(0)

        title = QLabel("GPT-Regeister")
        title.setObjectName("TitleBarTitle")
        layout.addWidget(title)
        layout.addStretch()

        self._btn_theme = self._make_title_btn("☀", "TitleBarBtn")
        self._btn_theme.setToolTip("切换亮色/暗色主题")
        self._btn_theme.clicked.connect(self._window.toggle_theme)

        self._btn_minimize = self._make_title_btn("—", "TitleBarBtn")
        self._btn_maximize = self._make_title_btn("□", "TitleBarBtn")
        self._btn_close    = self._make_title_btn("✕", "TitleBarBtnClose")

        self._btn_minimize.clicked.connect(self._window.showMinimized)
        self._btn_maximize.clicked.connect(self._toggle_maximize)
        self._btn_close.clicked.connect(self._window.close)
        self._btn_close.installEventFilter(self)
        self._close_shadow_color = QColor(232, 17, 35, 120)

        layout.addWidget(self._btn_theme)
        layout.addWidget(self._btn_minimize)
        layout.addWidget(self._btn_maximize)
        layout.addWidget(self._btn_close)

        self._window.installEventFilter(self)

    def set_dark_icon(self):
        self._btn_theme.setText("☾")

    def set_light_icon(self):
        self._btn_theme.setText("☀")

    def eventFilter(self, obj, event):
        if obj is self._window and event.type() == QEvent.WindowStateChange:
            self._update_maximize_btn()
        elif obj is self._btn_close:
            if event.type() == QEvent.Enter:
                shadow = QGraphicsDropShadowEffect(self._btn_close)
                shadow.setBlurRadius(18)
                shadow.setOffset(0, 3)
                shadow.setColor(self._close_shadow_color)
                self._btn_close.setGraphicsEffect(shadow)
            elif event.type() == QEvent.Leave:
                self._btn_close.setGraphicsEffect(None)
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            point = event.globalPosition().toPoint()
            frame = self._window.frameGeometry()
            if self._window.isMaximized() and self._window._normal_geometry is not None:
                normal_width = max(1, self._window._normal_geometry.width())
                self._drag_pos = QPoint(int(normal_width * 0.5), max(1, point.y() - frame.y()))
            else:
                self._drag_pos = point - frame.topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and event.buttons() == Qt.LeftButton:
            point = event.globalPosition().toPoint()
            if self._window.isMaximized():
                self._window._restore_from_title_drag(point)
            self._window.move(point - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._window._snap_to_top_if_needed(event.globalPosition().toPoint())
        self._dragging = False

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._toggle_maximize()

    @staticmethod
    def _make_title_btn(text: str, obj_name: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName(obj_name)
        btn.setFlat(True)
        btn.setFocusPolicy(Qt.NoFocus)
        return btn

    def _toggle_maximize(self):
        if self._window.isMaximized():
            self._window.showNormal()
            self._window._title_bar._update_maximize_btn()
            if self._window._normal_geometry is not None:
                self._window.setGeometry(self._window._normal_geometry)
        else:
            self._window._normal_geometry = self._window.geometry()
            self._window.showMaximized()
            self._window._title_bar._update_maximize_btn()

    def _update_maximize_btn(self):
        if self._window.isMaximized():
            self._btn_maximize.setText("❐")
        else:
            self._btn_maximize.setText("□")


class ConfigEditor(QMainWindow):
    _dark_mode: bool = False

    def __init__(self):
        super().__init__()
        self._settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        self._log_visible = True
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setWindowTitle("GPT-Regeister")
        self.resize(980, 780)
        self.setMinimumSize(760, 560)

        self._tabs_list: list = []
        self._normal_geometry = None
        self.worker = None
        self._build_ui()

        self._border_width = _BORDER_WIDTH
        self.setMouseTracking(True)
        self.setContentsMargins(0, 0, 0, 0)

        self._restore_window_state()
        self._load_config()

    def _restore_window_state(self):
        geometry = self._settings.value("window/geometry")
        was_maximized = self._settings.value("window/maximized", False, type=bool)
        if geometry is not None and not was_maximized:
            self.restoreGeometry(geometry)
            self._normal_geometry = self.geometry()

        screen = QGuiApplication.screenAt(self.frameGeometry().center())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            frame = self.frameGeometry()
            if not available.intersects(frame):
                width = min(max(self.width(), self.minimumWidth()), available.width())
                height = min(max(self.height(), self.minimumHeight()), available.height())
                self.resize(width, height)
                self.move(available.center() - self.rect().center())

        self._log_visible = self._settings.value("log_panel/visible", True, type=bool)
        if not self._log_visible:
            self._set_log_visible(False)
        else:
            sizes = self._settings.value("log_panel/splitter_sizes")
            if isinstance(sizes, list) and len(sizes) == 2:
                try:
                    self._content_splitter.setSizes([int(sizes[0]), int(sizes[1])])
                except (TypeError, ValueError):
                    pass

        if self._settings.value("window/maximized", False, type=bool):
            self.showMaximized()
            self._title_bar._update_maximize_btn()

    def _snap_to_top_if_needed(self, global_pos):
        if self.isMaximized():
            return
        screen = QGuiApplication.screenAt(global_pos) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        if global_pos.y() <= available.top() + 2:
            self._normal_geometry = self.geometry()
            self.showMaximized()
            self._title_bar._update_maximize_btn()

    def _restore_from_title_drag(self, global_pos):
        if not self.isMaximized():
            return
        restore_geometry = self._normal_geometry if self._normal_geometry is not None else self.geometry()
        screen = QGuiApplication.screenAt(global_pos) or QGuiApplication.primaryScreen()
        self.showNormal()
        self._title_bar._update_maximize_btn()
        self.setGeometry(restore_geometry)
        if screen is None:
            return
        available = screen.availableGeometry()
        frame = self.frameGeometry()
        target_x = global_pos.x() - self._title_bar._drag_pos.x()
        target_y = max(available.top(), global_pos.y() - self._title_bar._drag_pos.y())
        target_x = max(available.left(), min(target_x, available.right() - frame.width() + 1))
        self.move(target_x, target_y)
        self._normal_geometry = self.geometry()

    def closeEvent(self, event: QCloseEvent):
        self._settings.setValue("window/maximized", self.isMaximized())
        if not self.isMaximized():
            self._normal_geometry = self.geometry()
            self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("log_panel/visible", self._log_visible)
        if self._log_visible:
            self._settings.setValue("log_panel/splitter_sizes", self._content_splitter.sizes())
        self._settings.sync()
        super().closeEvent(event)

    def nativeEvent(self, event_type, message):
        if sys.platform != "win32":
            return super().nativeEvent(event_type, message)

        msg = ctypes.wintypes.MSG.from_address(int(message))
        if msg.message == 0x0083 and self.isMaximized():
            return True, 0
        if msg.message != 0x0084:
            return super().nativeEvent(event_type, message)

        if self.isMaximized():
            return super().nativeEvent(event_type, message)

        x = msg.pt.x - self.frameGeometry().x()
        y = msg.pt.y - self.frameGeometry().y()
        w = self.frameGeometry().width()
        h = self.frameGeometry().height()

        on_left = x < self._border_width
        on_right = x > w - self._border_width
        on_top = y < self._border_width
        on_bottom = y > h - self._border_width

        result = 0
        if on_left and on_top:
            result = 13
        elif on_right and on_top:
            result = 14
        elif on_right and on_bottom:
            result = 17
        elif on_left and on_bottom:
            result = 16
        elif on_left:
            result = 10
        elif on_right:
            result = 11
        elif on_top:
            result = 12
        elif on_bottom:
            result = 15

        if result:
            return True, result

        return super().nativeEvent(event_type, message)

    def toggle_theme(self):
        self._dark_mode = not self._dark_mode
        theme = DARK_THEME if self._dark_mode else LIGHT_THEME
        QApplication.instance().setStyleSheet(theme)
        self._title_bar.set_dark_icon() if self._dark_mode else self._title_bar.set_light_icon()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._title_bar = TitleBar(self)
        root.addWidget(self._title_bar)

        content = QWidget()
        content_l = QVBoxLayout(content)
        content_l.setContentsMargins(20, 16, 20, 16)
        content_l.setSpacing(12)

        self._content_splitter = QSplitter(Qt.Vertical)
        self._content_splitter.setChildrenCollapsible(False)

        main_panel = QWidget()
        main_panel_layout = QVBoxLayout(main_panel)
        main_panel_layout.setContentsMargins(0, 0, 0, 0)
        main_panel_layout.setSpacing(12)

        self.tabs = NoWheelTabWidget()

        self._register_tab = RegisterTab()
        self._email_tab = EmailTab()
        self._proxy_tab = ProxyTab()
        self._proxy_tab.test_log_signal.connect(self._append_log)

        self._tabs_list = [
            ("注册",       self._register_tab),
            ("邮箱",       self._email_tab),
            ("浏览器指纹", BrowserTab()),
            ("OpenAI 协议",  OpenAITab()),
            ("代理池",     self._proxy_tab),
            ("2FA",            TwoFATab()),
            ("Flow 触发",  FlowTab()),
        ]
        for label, widget in self._tabs_list:
            self.tabs.addTab(widget, f"  {label}  ")

        main_panel_layout.addWidget(self.tabs)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.save_btn = QPushButton("保存配置")
        self.save_btn.setObjectName("PrimaryBtn")
        self.save_btn.setToolTip("将当前配置写入 config.yaml")

        self.load_btn = QPushButton("重新加载")
        self.load_btn.setToolTip("从 config.yaml 重新读取配置")

        self.toggle_log_btn = QPushButton("隐藏日志")
        self.toggle_log_btn.setToolTip("隐藏或显示运行日志")

        self.clear_log_btn = QPushButton("清除日志")
        self.clear_log_btn.setToolTip("清空运行日志")

        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.load_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.toggle_log_btn)
        btn_row.addWidget(self.clear_log_btn)

        main_panel_layout.addLayout(btn_row)

        self.log_panel = QWidget()
        log_panel_layout = QVBoxLayout(self.log_panel)
        log_panel_layout.setContentsMargins(0, 0, 0, 0)
        log_panel_layout.setSpacing(8)

        log_label = QLabel("运行日志")
        log_label.setStyleSheet("color: #707088; font-size: 12px; margin-top: 4px;")
        log_panel_layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setObjectName("LogOutput")
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(96)
        self.log_output.setFont(QFont("Consolas", 11))
        log_panel_layout.addWidget(self.log_output)

        self.clear_log_btn.clicked.connect(self.log_output.clear)

        self._content_splitter.addWidget(main_panel)
        self._content_splitter.addWidget(self.log_panel)
        self._content_splitter.setStretchFactor(0, 5)
        self._content_splitter.setStretchFactor(1, 2)
        self._content_splitter.setSizes([560, 180])

        content_l.addWidget(self._content_splitter)

        root.addWidget(content)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.load_btn.clicked.connect(self._load_config)
        self.save_btn.clicked.connect(self._save_config)
        self.toggle_log_btn.clicked.connect(self._toggle_log_panel)
        self._register_tab.run_registration.connect(self._run_registration)
        self._email_tab.provider_changed.connect(self._on_provider_changed)

    def _set_log_visible(self, visible: bool):
        self._log_visible = visible
        self.log_panel.setVisible(visible)
        self.toggle_log_btn.setText("隐藏日志" if visible else "显示日志")
        if visible:
            sizes = self._content_splitter.sizes()
            if len(sizes) != 2 or sizes[1] <= 0:
                total = max(sum(sizes), self.height() - 160)
                self._content_splitter.setSizes([max(total - 180, 360), 180])
        else:
            self._content_splitter.setSizes([max(sum(self._content_splitter.sizes()), 1), 0])

    def _toggle_log_panel(self):
        self._set_log_visible(not self._log_visible)

    def _on_provider_changed(self, provider: str):
        self._register_tab.set_manual_mode(provider == "manual")

    def _load_config(self):
        from config.loader import get_full_config
        cfg = get_full_config()
        for _, tab in self._tabs_list:
            tab.load_config(cfg)
        self.status_bar.showMessage("已从 config.yaml 加载配置")

    def _save_config(self):
        cfg = {}
        for _, tab in self._tabs_list:
            tab.collect_config(cfg)

        from config.loader import save_yaml, invalidate_cache
        save_yaml(cfg)
        invalidate_cache()

        for _, tab in self._tabs_list:
            tab.load_config(cfg)

        self.status_bar.showMessage("配置已保存到 config.yaml")

    def _run_registration(self, runs: int = 1):
        self._save_config()
        self.log_output.clear()

        cfg = {}
        for _, tab in self._tabs_list:
            tab.collect_config(cfg)
        provider = cfg.get("email", {}).get("provider", "imap")
        register_cfg = cfg.get("register", {})
        if provider == "manual":
            if not register_cfg.get("email", "").strip():
                QMessageBox.information(self, "提示", "手动模式下请先填写注册邮箱")
                return
            if not register_cfg.get("name", "").strip():
                QMessageBox.information(self, "提示", "手动模式下请先填写姓名")
                return
            runs = 1

        self.load_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self._register_tab.set_running(True)
        self.status_bar.showMessage(f"正在执行注册（共 {runs} 轮）……")

        self.worker = RegistrationWorker(runs=runs)
        self.worker.log_signal.connect(self._append_log)
        self.worker.finished_signal.connect(self._on_registration_done)
        self.worker.otp_required_signal.connect(self._prompt_manual_otp)
        self.worker.start()

    def _append_log(self, text: str):
        self.log_output.append(text)
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_output.setTextCursor(cursor)

    def _prompt_manual_otp(self, email: str):
        self.status_bar.showMessage(f"请为 {email} 输入验证码")
        self._append_log("")
        self._append_log(f"[OTP] 请在弹窗中输入 {email} 收到的 6 位验证码")
        otp_code, ok = QInputDialog.getText(self, "手动输入验证码", f"请输入 {email} 收到的 6 位验证码：")
        if not ok:
            otp_code = ""
        self.worker.submit_manual_otp(otp_code)

    def _on_registration_done(self, success: bool, message: str):
        self.load_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self._register_tab.set_running(False)
        self.status_bar.showMessage(message)
        if success:
            self._append_log("")
            self._append_log("══════════ 注册成功 ══════════")
            self._append_log(message)
        else:
            self._append_log("")
            self._append_log("[ERROR] " + message)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(LIGHT_THEME)

    _icon_path = Path(__file__).parent / "openai.svg"
    if _icon_path.exists():
        app.setWindowIcon(QIcon(str(_icon_path)))

    window = ConfigEditor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

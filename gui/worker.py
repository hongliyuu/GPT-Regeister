# -*- coding: utf-8 -*-
import logging

from PySide6.QtCore import QThread, Signal


class RegistrationWorker(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, runs: int = 1):
        super().__init__()
        self.runs = max(1, runs)

    def run(self):
        from config.loader import invalidate_cache
        invalidate_cache()

        try:
            from main import configure_logging, prepare_registration_inputs, run_registration
            from core.account_export import create_batch_archive_dir

            configure_logging(verbose=True)

            class _EmitHandler(logging.Handler):
                def __init__(self, worker):
                    super().__init__()
                    self.worker = worker
                    self.setLevel(logging.INFO)
                    self.setFormatter(logging.Formatter(
                        "%(asctime)s  %(levelname)-7s  %(message)s", "%H:%M:%S"
                    ))

                def emit(self, record):
                    msg = self.format(record)
                    self.worker.log_signal.emit(msg)

            handler = _EmitHandler(self)
            logger = logging.getLogger()
            logger.addHandler(handler)

            overall_ok = True
            final_msg = ""

            for r in range(1, self.runs + 1):
                if self.runs > 1:
                    self.log_signal.emit(f"")
                    self.log_signal.emit(f"══════════ 第 {r}/{self.runs} 轮 ══════════")

                email, name, birthday = prepare_registration_inputs()
                batch_dir = create_batch_archive_dir()
                try:
                    result = run_registration(
                        email=email, name=name, birthday=birthday, batch_dir=batch_dir,
                    )
                except Exception as e:
                    self.log_signal.emit(f"[ERROR] 第 {r} 轮异常: {e}")
                    final_msg = f"第 {r}/{self.runs} 轮异常: {e}"
                    overall_ok = False
                    break

                if result.get("success"):
                    token = result.get("access_token", "N/A")
                    self.log_signal.emit(f"第 {r} 轮成功  {email}  Token: {token[:24]}...")
                    final_msg = f"第 {r}/{self.runs} 轮成功  {email}  Token: {token[:24]}..."
                else:
                    self.log_signal.emit(f"第 {r} 轮失败  {email}")
                    final_msg = f"第 {r}/{self.runs} 轮失败  {email}"
                    overall_ok = False
                    break

            logger.removeHandler(handler)
            self.finished_signal.emit(overall_ok, final_msg)

        except Exception as e:
            self.finished_signal.emit(False, f"注册异常: {e}")

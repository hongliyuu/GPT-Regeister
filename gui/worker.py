# -*- coding: utf-8 -*-
import importlib
import logging

from PySide6.QtCore import QThread, Signal


class RegistrationWorker(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)
    otp_required_signal = Signal(str)

    def __init__(self, runs: int = 1, workers: int = 1, continue_on_fail: bool = False):
        super().__init__()
        self.runs = max(1, runs)
        self.workers = max(1, workers)
        self.continue_on_fail = continue_on_fail
        self._pending_otp: str | None = None

    def run(self):
        from config.loader import invalidate_cache
        invalidate_cache()

        try:
            import config.loader as config_loader
            import config
            import main
            importlib.reload(config_loader)
            importlib.reload(config)
            importlib.reload(main)

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
            batch_dir = create_batch_archive_dir(count=self.runs, workers=self.workers)

            if self.workers > 1:
                self._run_parallel_batch(batch_dir)
                return

            for r in range(1, self.runs + 1):
                if self.runs > 1:
                    self.log_signal.emit("")
                    self.log_signal.emit(f"══════════ 第 {r}/{self.runs} 轮 ══════════")

                email, name, birthday = prepare_registration_inputs()
                try:
                    otp_provider = self._request_manual_otp if self._requires_manual_otp() else None
                    result = run_registration(
                        email=email,
                        name=name,
                        birthday=birthday,
                        batch_dir=batch_dir,
                        otp_provider=otp_provider,
                    )
                except Exception as e:
                    message = self._format_error_message(e)
                    self.log_signal.emit(f"[ERROR] 第 {r} 轮异常: {message}")
                    if self.continue_on_fail:
                        final_msg = f"第 {r}/{self.runs} 轮异常(已跳过): {message}"
                        overall_ok = False
                        continue
                    final_msg = f"第 {r}/{self.runs} 轮异常: {message}"
                    overall_ok = False
                    break

                if result.get("success"):
                    token = result.get("access_token", "N/A")
                    self.log_signal.emit(f"第 {r} 轮成功  {email}  Token: {token[:24]}...")
                    final_msg = f"第 {r}/{self.runs} 轮成功  {email}  Token: {token[:24]}..."
                else:
                    error_message = self._format_error_message(result.get("error"))
                    self.log_signal.emit(f"第 {r} 轮失败  {error_message}")
                    if self.continue_on_fail:
                        final_msg = f"第 {r}/{self.runs} 轮失败(已跳过)  {error_message}"
                        overall_ok = False
                        continue
                    final_msg = f"第 {r}/{self.runs} 轮失败  {error_message}"
                    overall_ok = False
                    break

            logger.removeHandler(handler)
            self.finished_signal.emit(overall_ok, final_msg)

        except Exception as e:
            self.finished_signal.emit(False, f"注册异常: {self._format_error_message(e)}")

    @staticmethod
    def _requires_manual_otp() -> bool:
        from config import USE_EMAIL_SERVICE
        return not USE_EMAIL_SERVICE

    @staticmethod
    def _format_error_message(error) -> str:
        if isinstance(error, BaseException):
            message = str(error).strip()
            if not message:
                return type(error).__name__
            return f"{type(error).__name__}: {message}"

        message = str(error or "").strip()
        return message or "注册失败，请检查日志"

    def _run_parallel_batch(self, batch_dir):
        import config
        import main

        if not config.USE_EMAIL_SERVICE:
            self.log_signal.emit("[ERROR] 并发注册需要开启邮箱自动取件，请先配置")
            self.finished_signal.emit(False, "并发注册需要开启邮箱自动取件")
            return

        self.log_signal.emit(f"[批量] 并发注册：目标 {self.runs}，线程 {self.workers}")
        results = main.run_parallel_batch(self.runs, self.workers, delay=0, continue_on_fail=self.continue_on_fail, batch_dir=batch_dir)

        success_count = sum(1 for r in results if main._is_success(r))
        overall_ok = success_count == self.runs
        final_msg = f"并发注册完成：成功 {success_count}/{len(results)}"
        self.finished_signal.emit(overall_ok, final_msg)

    def _request_manual_otp(self, email: str) -> str:
        from PySide6.QtCore import QEventLoop

        self._pending_otp = None
        self.otp_required_signal.emit(email)

        loop = QEventLoop()
        while self._pending_otp is None:
            loop.processEvents()
            self.msleep(100)

        otp = self._pending_otp.strip()
        self._pending_otp = None
        if not otp:
            raise RuntimeError("未输入验证码，已取消注册")
        return otp

    def submit_manual_otp(self, otp_code: str):
        self._pending_otp = otp_code

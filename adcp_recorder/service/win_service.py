import logging
import socket
import sys
from pathlib import Path

# Conditional import to avoid ImportError on non-Windows systems during development/tests
try:
    import servicemanager
    import win32event
    import win32service
    import win32serviceutil
except ImportError:
    win32serviceutil = None
    win32service = None
    win32event = None
    servicemanager = None

from adcp_recorder.config import RecorderConfig
from adcp_recorder.service.supervisor import ServiceSupervisor


class ADCPRecorderService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ADCPRecorder"
    _svc_display_name_ = "ADCP Recorder Service"
    _svc_description_ = "NMEA telemetry recorder data acquisition service."

    def __init__(self, args):
        if not win32serviceutil:
            raise ImportError("pywin32 is not installed or not supported on this platform.")

        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.supervisor = None

    def SvcStop(self):  # noqa: N802
        """Callback for service stop."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

        # Signal supervisor to stop
        if self.supervisor:
            self.supervisor._shutdown()

    def SvcDoRun(self):  # noqa: N802
        """Main service loop."""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )

        # Setup logging to file since stdout/stderr might be lost
        self._setup_logging()

        try:
            config = RecorderConfig.load()
            self.supervisor = ServiceSupervisor(config)

            # We run the supervisor in a way that checks the stop event
            # Supervisor.run is blocking, but check for hWaitStop?
            # Actually Supervisor.run has a loop checking _shutdown_event.
            # We can run supervisor in a thread, or modify supervisor to check a callback?
            # Easiest: The SvcStop calls supervisor._shutdown() which sets the event.
            # Supervisor.run() loop checks that event.
            # So just calling supervisor.run() here should be fine,
            # as long as SvcStop is called from another thread (OS does this).

            self.supervisor.run()

        except Exception as e:
            logging.error(f"Service failed: {e}", exc_info=True)
            servicemanager.LogInfoMsg(f"Service failed: {e}")

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, ""),
        )

    def _setup_logging(self):
        # Determine log path - usually user profile service runs under is SYSTEM?
        # Better to pick specific path or relative to executable
        # For now, let's try a standard location or the configured output dir
        try:
            config = RecorderConfig.load()
            log_dir = Path(config.output_dir) / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "service.log"

            logging.basicConfig(
                filename=str(log_file),
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
        except Exception:
            # Fallback
            pass


if __name__ == "__main__":
    if not win32serviceutil:
        print("pywin32 not installed. Cannot run as Windows Service.")
        sys.exit(1)

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ADCPRecorderService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ADCPRecorderService)

"""
Smart Fence - IoT Hardware Integration Service
Handles communication with physical ESP32 (Buzzer + LED) over Wi-Fi/HTTP,
tracks connection health, and provides a virtual hardware simulator fallback.
"""

import time
import logging
import threading
import requests
from typing import Dict, Any, Optional

from ai.config import (
    ESP32_IP,
    ESP32_PORT,
    ESP32_TIMEOUT_SECONDS,
    USE_VIRTUAL_ESP32
)

logger = logging.getLogger("SmartFence.IoT")


class VirtualESP32Device:
    """
    Simulates physical ESP32 hardware behavior in software
    when physical microcontroller is not plugged in.
    Allows end-to-end testing of Buzzer, LED, and heartbeat states.
    """
    def __init__(self):
        self.connected = True
        self.buzzer_state = False
        self.led_state = False
        self.current_risk = "LOW"
        self.last_command_time = time.time()
        self.alert_count = 0

    def handle_command(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.current_risk = payload.get("risk", "LOW")
        self.buzzer_state = payload.get("buzzer", False)
        self.led_state = payload.get("led", False)
        self.last_command_time = time.time()
        if self.buzzer_state or self.led_state:
            self.alert_count += 1
        logger.info(
            f"[VIRTUAL ESP32] Hardware State Changed -> Risk: {self.current_risk} | "
            f"Buzzer: {'ON [BEEP]' if self.buzzer_state else 'OFF'} | "
            f"LED: {'ON [FLASHING RED]' if self.led_state else 'OFF'}"
        )
        return {
            "status": "OK",
            "device": "VIRTUAL_ESP32",
            "buzzer": self.buzzer_state,
            "led": self.led_state,
            "risk": self.current_risk
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "CONNECTED",
            "type": "VIRTUAL_SIMULATOR",
            "buzzer": self.buzzer_state,
            "led": self.led_state,
            "current_risk": self.current_risk,
            "uptime_seconds": round(time.time() - self.last_command_time, 1)
        }


class IoTService:
    """
    Dispatches alerts to ESP32 hardware, checks heartbeat status,
    and seamlessly falls back to virtual simulator.
    """
    def __init__(
        self,
        ip: str = ESP32_IP,
        port: int = ESP32_PORT,
        timeout: float = ESP32_TIMEOUT_SECONDS,
        use_virtual_fallback: bool = USE_VIRTUAL_ESP32
    ):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.use_virtual_fallback = use_virtual_fallback
        self.base_url = f"http://{self.ip}:{self.port}"
        
        self.is_hardware_connected = False
        self.virtual_device: Optional[VirtualESP32Device] = VirtualESP32Device() if use_virtual_fallback else None
        
        self.last_dispatched_risk = "LOW"
        self.last_dispatched_time = 0.0
        self.buzzer_active = False
        self.led_active = False

        # Periodic health checker thread
        self._stop_health_check = threading.Event()
        self._health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_thread.start()

    def _health_check_loop(self):
        """Periodically pings physical ESP32 /api/status."""
        while not self._stop_health_check.is_set():
            try:
                resp = requests.get(f"{self.base_url}/api/status", timeout=self.timeout)
                if resp.status_code == 200:
                    if not self.is_hardware_connected:
                        logger.info(f"Physical ESP32 detected at {self.base_url}")
                    self.is_hardware_connected = True
                else:
                    self.is_hardware_connected = False
            except Exception:
                self.is_hardware_connected = False
            
            time.sleep(5.0)

    def dispatch_alert(self, command: Dict[str, Any]) -> bool:
        """
        Sends alert command to physical ESP32 or virtual simulator.
        Command format:
        {
            "risk": "HIGH",
            "buzzer": True,
            "led": True,
            "reason": "..."
        }
        """
        self.last_dispatched_risk = command.get("risk", "LOW")
        self.buzzer_active = command.get("buzzer", False)
        self.led_active = command.get("led", False)
        self.last_dispatched_time = time.time()

        # Try physical hardware first
        if self.is_hardware_connected:
            try:
                resp = requests.post(
                    f"{self.base_url}/api/alert",
                    json=command,
                    timeout=self.timeout
                )
                if resp.status_code == 200:
                    logger.info(f"Dispatched alert to physical ESP32 successfully: {command}")
                    return True
                else:
                    logger.warning(f"ESP32 returned error status: {resp.status_code}")
            except Exception as e:
                logger.warning(f"Failed to communicate with physical ESP32: {e}")
                self.is_hardware_connected = False

        # Fallback to virtual simulator
        if self.virtual_device:
            self.virtual_device.handle_command(command)
            return True

        return False

    def get_status(self) -> Dict[str, Any]:
        """Returns the current IoT hardware status for dashboard display."""
        if self.is_hardware_connected:
            return {
                "status": "CONNECTED",
                "mode": "PHYSICAL_HARDWARE",
                "ip": self.ip,
                "buzzer": self.buzzer_active,
                "led": self.led_active,
                "current_risk": self.last_dispatched_risk
            }
        elif self.virtual_device:
            return {
                "status": "CONNECTED",
                "mode": "VIRTUAL_SIMULATOR",
                "ip": "127.0.0.1 (Simulated)",
                "buzzer": self.virtual_device.buzzer_state,
                "led": self.virtual_device.led_state,
                "current_risk": self.virtual_device.current_risk
            }
        else:
            return {
                "status": "DISCONNECTED",
                "mode": "NONE",
                "ip": self.ip,
                "buzzer": False,
                "led": False,
                "current_risk": "UNKNOWN"
            }

    def shutdown(self):
        self._stop_health_check.set()


# Global singleton instance
iot_service = IoTService()

"""Serial communication package for ADCP recorder.

Provides serial port management, producer (reader), and consumer (parser router).
"""

from adcp_recorder.serial.consumer import MessageRouter, SerialConsumer
from adcp_recorder.serial.port_manager import (
    PortInfo,
    SerialConnectionManager,
    list_serial_ports,
)
from adcp_recorder.serial.producer import SerialProducer

__all__ = [
    "PortInfo",
    "SerialConnectionManager",
    "list_serial_ports",
    "SerialProducer",
    "SerialConsumer",
    "MessageRouter",
]

from dataclasses import dataclass


@dataclass
class BinaryChunk:
    """Small wrapper object for streaming binary data through the FIFO queue.

    Attributes:
        data: Raw bytes chunk read from serial port
        start: True for the first chunk of a blob
        end: True for the final chunk of a blob
    """

    data: bytes
    start: bool = False
    end: bool = False

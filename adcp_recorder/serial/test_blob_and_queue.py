import os
import time
from queue import Queue

from adcp_recorder.db.db import DatabaseManager
from adcp_recorder.export.file_writer import FileWriter
from adcp_recorder.serial.consumer import MessageRouter, SerialConsumer
from adcp_recorder.serial.producer import SerialProducer


class FakeConnectionManager:
    def __init__(self, items):
        # items is an iterable of bytes to return from read_line()
        self._items = list(items)
        self._idx = 0

    def is_connected(self):
        return True

    def reconnect(self, max_retries=3):
        return True

    def read_line(self, timeout=1.0):
        # Return next item, or None when exhausted
        if self._idx >= len(self._items):
            time.sleep(0.01)
            return None
        val = self._items[self._idx]
        self._idx += 1
        return val


def drain_queue(q: Queue):
    items = []
    try:
        while True:
            items.append(q.get_nowait())
    except Exception:
        pass
    return items


def test_queue_drop_oldest_behavior():
    # queue maxsize 3, send 5 lines, expect last 3 present
    q = Queue(maxsize=3)
    lines = [f"line{i}\n".encode("ascii") for i in range(1, 6)]

    manager = FakeConnectionManager(lines)
    producer = SerialProducer(connection_manager=manager, queue=q, max_line_length=1024)

    producer.start()
    # allow producer to run briefly
    time.sleep(0.5)
    producer.stop()

    items = drain_queue(q)
    # Convert bytes to strings for comparison
    items_str = [i.decode("ascii").strip() for i in items if isinstance(i, (bytes, bytearray))]

    assert len(items_str) <= 3
    # Expect last three lines
    assert items_str == ["line3", "line4", "line5"]


def test_binary_blob_streaming(tmp_path):
    base = str(tmp_path)
    # create binary chunks (many zero bytes to be detected as binary)
    bin_chunks = [b"\x00" * 100, b"\x01" * 200, b"\x02" * 50]
    # end with an ASCII line to trigger blob end
    ascii_line = b"$PNORI,1,TEST*00\r\n"

    items = []
    # interleave binary chunks as read_line returns
    for c in bin_chunks:
        items.append(c)
    items.append(ascii_line)

    manager = FakeConnectionManager(items)

    q = Queue(maxsize=50)
    db_path = os.path.join(base, "adcp_test.duckdb")
    db = DatabaseManager(db_path)
    file_writer = FileWriter(base)
    router = MessageRouter()

    producer = SerialProducer(connection_manager=manager, queue=q)
    consumer = SerialConsumer(queue=q, db_manager=db, router=router, file_writer=file_writer)

    # start components
    consumer.start()
    producer.start()

    time.sleep(1.0)

    producer.stop()
    consumer.stop()

    # verify errors_binary has a .dat file
    bin_dir = os.path.join(base, "errors_binary")
    files = []
    if os.path.isdir(bin_dir):
        files = [f for f in os.listdir(bin_dir) if f.endswith(".dat")]

    assert len(files) >= 1, f"expected at least one .dat file in {bin_dir}, found {files}"

    # verify size roughly equals total binary bytes
    total_bytes = sum(len(c) for c in bin_chunks)
    # find largest file
    sizes = [os.path.getsize(os.path.join(bin_dir, f)) for f in files]
    assert any(s >= total_bytes for s in sizes)

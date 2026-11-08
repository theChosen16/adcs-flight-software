"""CCSDS Space Packet export of validated ADCS status frames from SIL."""

import struct
from pathlib import Path

# Local SIL-only APID. Reserved idle APID 0x7ff is not used.
STATUS_APID = 0x321
STATUS_FIELDS = (
    ("sil_sequence", "uint", 32, "sequence"),
    ("timestamp_s", "float", 32, "timestamp_s"),
    ("mode", "uint", 8, "mode"),
    ("flags", "uint", 8, "flags"),
    ("tmr_mismatch_count", "uint", 16, "tmr_mismatch_count"),
    ("gyro_bias_degph", "float", 32, "gyro_bias_degph"),
    ("health_flags", "uint", 8, "health_flags"),
    ("last_tc_opcode", "uint", 8, "last_tc_opcode"),
    ("last_tc_arg0", "uint", 8, "last_tc_arg0"),
    ("health_event_count", "uint", 8, "health_event_count"),
)
HEADER = struct.Struct(">HHH")
STATUS = struct.Struct(">IfBBHfBBBB")


class CcsdsStatusCapture:
    """Capture one SIL connection to a new file without changing the socket protocol."""

    def __init__(self, path: Path):
        self.path = path
        self._stream = None
        self._count = 0

    def write(self, status: dict) -> None:
        data = STATUS.pack(*(status[key] for _, _, _, key in STATUS_FIELDS))
        # Version 0, telemetry, no secondary header, unsegmented.
        header = HEADER.pack(STATUS_APID, 0xC000 | (self._count & 0x3FFF), len(data) - 1)
        if self._stream is None:
            self._stream = self.path.open("xb")
        self._stream.write(header + data)
        self._stream.flush()
        self._count += 1

    def close(self) -> None:
        if self._stream is not None:
            self._stream.close()
            self._stream = None

import struct
import tempfile
import unittest
from pathlib import Path

from BasiliskSim.bridge.ccsds_status import CcsdsStatusCapture
from BasiliskSim.bridge.sil_protocol import crc32, unpack_command_packet
from SIL.ccsds_status import decode


class CcsdsTests(unittest.TestCase):
    def test_status_round_trip(self):
        # Construct a SIL status frame in the existing C++ wire layout.
        body = struct.pack("<IHHIfBBHfBBBB", 0x53494C43, 1, 3, 19, 2.5, 2, 7, 513, 1.25, 4, 3, 2, 1)
        status = unpack_command_packet(body + struct.pack("<I", crc32(body)))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "status.ccsds"
            capture = CcsdsStatusCapture(path)
            try:
                capture.write(status)
                capture.write(status)
            finally:
                capture.close()
            self.assertEqual(path.read_bytes()[:6], bytes.fromhex("03 21 c0 00 00 13"))
            rows = list(decode(path))
            self.assertEqual([row["ccsds_sequence"] for row in rows], [0, 1])
            self.assertEqual(rows[1]["sil_sequence"], 19)
            self.assertEqual(rows[1]["mode"], 2)
            self.assertEqual(rows[1]["tmr_mismatch_count"], 513)
            self.assertAlmostEqual(rows[1]["timestamp_s"], 2.5)
            self.assertAlmostEqual(rows[1]["gyro_bias_degph"], 1.25)
            with self.assertRaises(FileExistsError):
                CcsdsStatusCapture(path).write(status)
            path.write_bytes(path.read_bytes()[:-1])
            with self.assertRaisesRegex(ValueError, "Truncated"):
                list(decode(path))

"""Decode an ADCS SIL status capture to JSON Lines with CCSDSPy."""

import argparse
import json
from io import BytesIO
from pathlib import Path

from BasiliskSim.bridge.ccsds_status import HEADER, STATUS, STATUS_APID, STATUS_FIELDS


def decode(path):
    from ccsdspy import FixedLength, PacketField

    packet = FixedLength([PacketField(name, kind, bits) for name, kind, bits, _ in STATUS_FIELDS])
    frame_size = HEADER.size + STATUS.size
    with path.open("rb") as source:
        while frame := source.read(frame_size):
            if len(frame) != frame_size:
                raise ValueError("Truncated CCSDS status packet")
            packet_id, sequence_control, length = HEADER.unpack_from(frame)
            if packet_id != STATUS_APID or sequence_control >> 14 != 3 or length != STATUS.size - 1:
                raise ValueError("Unexpected CCSDS status packet header")
            decoded = packet.load(BytesIO(frame))
            yield {"ccsds_sequence": sequence_control & 0x3FFF,
                   **{name: values[0].item() for name, values in decoded.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()
    try:
        for status in decode(args.capture):
            print(json.dumps(status, allow_nan=False))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()

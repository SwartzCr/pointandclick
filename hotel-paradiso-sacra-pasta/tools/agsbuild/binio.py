"""Little-endian binary writer used by every AGS format writer."""
import struct


class W:
    def __init__(self):
        self.b = bytearray()

    def pos(self):
        return len(self.b)

    def i8(self, v):
        self.b += struct.pack('<B', v & 0xFF)

    def i16(self, v):
        self.b += struct.pack('<H', v & 0xFFFF)

    def i32(self, v):
        self.b += struct.pack('<I', v & 0xFFFFFFFF)

    def i64(self, v):
        self.b += struct.pack('<Q', v & 0xFFFFFFFFFFFFFFFF)

    def raw(self, data):
        self.b += data

    def zeros(self, n):
        self.b += bytes(n)

    def fixed(self, text, length):
        """Text padded with NULs (or truncated) to exactly `length` bytes."""
        data = (text or '').encode('latin-1')[:length]
        self.b += data + bytes(length - len(data))

    def cstr(self, text):
        """NUL-terminated string."""
        self.b += (text or '').encode('latin-1') + b'\0'

    def lstr(self, text):
        """32-bit length followed by the bytes, no terminator."""
        data = (text or '').encode('latin-1')
        self.i32(len(data))
        self.b += data

    def patch32(self, at, v):
        self.b[at:at + 4] = struct.pack('<I', v & 0xFFFFFFFF)

    def patch64(self, at, v):
        self.b[at:at + 8] = struct.pack('<Q', v & 0xFFFFFFFFFFFFFFFF)

    def block(self, block_id, body, ext_id=None):
        """Room-style data block: 8-bit id (0 = string id follows), then a
        64-bit length and the data."""
        self.i8(block_id)
        if block_id == 0:
            self.fixed(ext_id, 16)
        self.i64(len(body))
        self.raw(body)

    def bytes(self):
        return bytes(self.b)

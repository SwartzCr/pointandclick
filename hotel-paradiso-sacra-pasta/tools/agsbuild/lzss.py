"""The LZSS variant AGS calls "LZW" (Common/util/lzw.cpp).

The stream is a sequence of groups: one flag byte, then eight items. A clear
flag bit is a literal byte; a set bit is a little-endian 16-bit back-reference
whose low 12 bits are (distance - 1) into a 4096-byte ring buffer and whose
high 4 bits are (length - 3), so matches are 3..18 bytes long. The decoder's
ring buffer starts out uninitialised, so we only ever refer back to bytes we
have already emitted.
"""

N = 4096
MAX_LEN = 18
MIN_LEN = 3
CANDIDATES = 12


def compress(data: bytes) -> bytes:
    n = len(data)
    out = bytearray()
    heads = {}          # 3-byte key -> list of recent positions (newest last)
    pos = 0
    flag_at = -1
    bit = 8
    flags = 0

    def add(p):
        if p + 3 <= n:
            k = data[p:p + 3]
            lst = heads.get(k)
            if lst is None:
                heads[k] = [p]
            else:
                lst.append(p)
                if len(lst) > CANDIDATES:
                    del lst[0]

    while pos < n:
        if bit == 8:
            if flag_at >= 0:
                out[flag_at] = flags
            flag_at = len(out)
            out.append(0)
            flags = 0
            bit = 0
        best_len = 0
        best_dist = 0
        if pos + MIN_LEN <= n:
            lst = heads.get(data[pos:pos + 3])
            if lst:
                limit = min(MAX_LEN, n - pos)
                for cand in reversed(lst):
                    dist = pos - cand
                    if dist > N - MAX_LEN:
                        break
                    ln = 3
                    while ln < limit and data[cand + ln] == data[pos + ln]:
                        ln += 1
                    if ln > best_len:
                        best_len, best_dist = ln, dist
                        if ln == limit:
                            break
        if best_len >= MIN_LEN:
            flags |= 1 << bit
            v = ((best_len - 3) << 12) | (best_dist - 1)
            out += bytes((v & 0xFF, v >> 8))
            for p in range(pos, pos + best_len):
                add(p)
            pos += best_len
        else:
            out.append(data[pos])
            add(pos)
            pos += 1
        bit += 1
    if flag_at >= 0:
        out[flag_at] = flags
    return bytes(out)


def expand(src: bytes, size: int) -> bytes:
    """Reference decoder, for tests."""
    buf = bytearray(N)
    i = N - MAX_LEN
    out = bytearray()
    p = 0
    while p < len(src) and len(out) < size:
        bits = src[p]; p += 1
        for b in range(8):
            if p >= len(src) or len(out) >= size:
                break
            if bits & (1 << b):
                j = src[p] | (src[p + 1] << 8); p += 2
                ln = ((j >> 12) & 15) + 3
                j = (i - (j & 0xFFF) - 1) & (N - 1)
                for _ in range(ln):
                    c = buf[j]
                    out.append(c); buf[i] = c
                    j = (j + 1) & (N - 1); i = (i + 1) & (N - 1)
            else:
                c = src[p]; p += 1
                out.append(c); buf[i] = c
                i = (i + 1) & (N - 1)
    return bytes(out)

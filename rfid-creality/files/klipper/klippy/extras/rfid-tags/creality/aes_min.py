"""Minimal pure-python AES (FIPS-197), ECB encrypt + decrypt, 128/256-bit keys.

Vendored so the Creality decoder needs no native crypto dependency on the printer. This
is a clean-room implementation of the published FIPS-197 standard (S-box, key schedule,
round transforms) - not derived from any third-party code. Unit-tested against the
FIPS-197 known-answer vectors. ECB only and no padding, which is exactly what Creality's
key derivation (AES-ECB encrypt of the tiled UID) and payload decrypt (AES-ECB of the
filament blocks) need.
"""
BLOCK_SIZE = 16
WORD_SIZE = 4
WORDS_PER_BLOCK = 4
KEY_SIZES = (16, 32)
AES_POLY = 0x1B
HIGH_BIT = 0x80
LOW_BIT = 0x01
GF_BITS = 8
MIX_2 = 2
MIX_3 = 3
INV_MIX_9 = 9
INV_MIX_11 = 11
INV_MIX_13 = 13
INV_MIX_14 = 14
ROUNDS_OFFSET = 6  # Nr = Nk + 6
AES256_NK = 8
AES256_EXTRA_SUB = 4

RCON = (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36, 0x6C, 0xD8, 0xAB, 0x4D)

SBOX = (
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16,
)

INV_SBOX = tuple(SBOX.index(value) for value in range(len(SBOX)))


def _gmul(left: int, right: int) -> int:
    """Multiply two bytes in GF(2^8) with the AES reduction polynomial."""
    product = 0
    factor = left
    multiplier = right
    for _bit in range(GF_BITS):
        if multiplier & LOW_BIT:
            product ^= factor
        high = factor & HIGH_BIT
        factor = (factor << 1) & 0xFF
        if high:
            factor ^= AES_POLY
        multiplier >>= 1
    return product


def _sub_word(word: list[int]) -> list[int]:
    return [SBOX[byte] for byte in word]


def _rot_word(word: list[int]) -> list[int]:
    return word[1:] + word[:1]


def _schedule_word(prev: list[int], index: int, key_words: int) -> list[int]:
    if index % key_words == 0:
        rotated = _sub_word(_rot_word(prev))
        return [rotated[0] ^ RCON[index // key_words - 1], rotated[1], rotated[2], rotated[3]]
    if key_words > ROUNDS_OFFSET and index % key_words == AES256_EXTRA_SUB:
        return _sub_word(prev)
    return prev


def _expand_key(key: bytes) -> tuple[list[list[int]], int]:
    key_words = len(key) // WORD_SIZE
    rounds = key_words + ROUNDS_OFFSET
    words = [list(key[i * WORD_SIZE:(i + 1) * WORD_SIZE]) for i in range(key_words)]
    total = WORDS_PER_BLOCK * (rounds + 1)
    schedule = list(words)
    for index in range(key_words, total):
        temp = _schedule_word(schedule[index - 1], index, key_words)
        schedule.append([a ^ b for a, b in zip(schedule[index - key_words], temp)])
    return schedule, rounds


def _add_round_key(state: list[int], schedule: list[list[int]], rnd: int) -> list[int]:
    base = rnd * WORDS_PER_BLOCK
    return [
        state[WORD_SIZE * col + row] ^ schedule[base + col][row]
        for col in range(WORDS_PER_BLOCK)
        for row in range(WORD_SIZE)
    ]


def _shift_rows(state: list[int], direction: int) -> list[int]:
    return [
        state[WORD_SIZE * ((col + direction * row) % WORDS_PER_BLOCK) + row]
        for col in range(WORDS_PER_BLOCK)
        for row in range(WORD_SIZE)
    ]


def _mix_one(coeffs: tuple[int, int, int, int], column: list[int]) -> int:
    return (
        _gmul(coeffs[0], column[0]) ^ _gmul(coeffs[1], column[1])
        ^ _gmul(coeffs[2], column[2]) ^ _gmul(coeffs[3], column[3])
    )


def _mix_columns(state: list[int], matrix: tuple[tuple[int, int, int, int], ...]) -> list[int]:
    out: list[int] = []
    for col in range(WORDS_PER_BLOCK):
        base = WORD_SIZE * col
        column = state[base:base + WORD_SIZE]
        out.extend(_mix_one(row, column) for row in matrix)
    return out


_MIX_MATRIX = (
    (MIX_2, MIX_3, 1, 1), (1, MIX_2, MIX_3, 1), (1, 1, MIX_2, MIX_3), (MIX_3, 1, 1, MIX_2),
)
_INV_MIX_MATRIX = (
    (INV_MIX_14, INV_MIX_11, INV_MIX_13, INV_MIX_9),
    (INV_MIX_9, INV_MIX_14, INV_MIX_11, INV_MIX_13),
    (INV_MIX_13, INV_MIX_9, INV_MIX_14, INV_MIX_11),
    (INV_MIX_11, INV_MIX_13, INV_MIX_9, INV_MIX_14),
)


class AesEcb:
    """AES in ECB mode (no padding); the only mode the Creality tag scheme uses."""

    def __init__(self, key: bytes) -> None:
        if len(key) not in KEY_SIZES:
            raise ValueError(f"AES key must be {KEY_SIZES} bytes, got {len(key)}")
        self._schedule, self._rounds = _expand_key(key)

    def encrypt_block(self, block: bytes) -> bytes:
        state = _add_round_key(list(block), self._schedule, 0)
        for rnd in range(1, self._rounds):
            state = _shift_rows([SBOX[byte] for byte in state], 1)
            state = _add_round_key(_mix_columns(state, _MIX_MATRIX), self._schedule, rnd)
        state = _shift_rows([SBOX[byte] for byte in state], 1)
        return bytes(_add_round_key(state, self._schedule, self._rounds))

    def decrypt_block(self, block: bytes) -> bytes:
        state = _add_round_key(list(block), self._schedule, self._rounds)
        for rnd in range(self._rounds - 1, 0, -1):
            state = [INV_SBOX[byte] for byte in _shift_rows(state, -1)]
            state = _mix_columns(_add_round_key(state, self._schedule, rnd), _INV_MIX_MATRIX)
        state = [INV_SBOX[byte] for byte in _shift_rows(state, -1)]
        return bytes(_add_round_key(state, self._schedule, 0))

    def decrypt_ecb(self, data: bytes) -> bytes:
        if len(data) % BLOCK_SIZE != 0:
            raise ValueError("ciphertext length must be a multiple of the block size")
        chunks = (self.decrypt_block(data[at:at + BLOCK_SIZE])
                  for at in range(0, len(data), BLOCK_SIZE))
        return b"".join(chunks)

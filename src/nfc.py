"""Verify check-in links produced by our NFC Tag.

Each tap gives a link with two values:
- picc_data: the tag's ID and tap counter, encrypted with our AES key
- cmac: a signature proving the link came from one of our tags

This file only checks that a link is genuine. Checking that the counter
is new (the link wasn't already used) happens in the database code.

Referenced the NXP NTAG 424 DNA Spec for all of this
"""

import hmac
from Crypto.Cipher import AES
from Crypto.Hash import CMAC


def verify_tap(picc_data_hex: str, cmac_hex: str, key: bytes) -> tuple[str, int]:
    """Check that a tap's link is genuine and returns the tag's ID and counter.

    picc_data_hex and cmac_hex come straight from the link. key is our
    16-byte AES key, which never appears in the link.

    Returns (uid, counter), with uid as a hex string.
    Raises ValueError if the link is wrong, forged or from diff tag
    """

    picc_data = bytes.fromhex(picc_data_hex)
    received_cmac = bytes.fromhex(cmac_hex)

    if len(picc_data) != 16 or len(received_cmac) != 8:
        raise ValueError("picc_data or cmac has the wrong length")

    # The tag adds random bytes to the data instead, so every link still looks different.
    plain = AES.new(key, AES.MODE_CBC, iv=bytes(16)).decrypt(picc_data)

    # 0xC7 = "chip ID + counter follow". Anything else means a wrong key.
    if plain[0] != 0xC7:
        raise ValueError("decrypted data has an unexpected format")

    uid = plain[1:8]
    counter_bytes = plain[8:11]
    counter = int.from_bytes(counter_bytes, "little")

    # The tag signs with a one time key made from our key + chip ID +
    # counter. 3CC300010080 is a fixed label.
    sv2 = bytes.fromhex("3CC300010080") + uid + counter_bytes
    mac = CMAC.new(key, ciphermod=AES)
    mac.update(sv2)
    session_key = mac.digest()

    # Sign an empty message with the one time key. The link carries
    # every other byte of the result.
    mac = CMAC.new(session_key, ciphermod=AES)
    expected_cmac = mac.digest()[1::2]

    # Constant-time comparison, so timing can't leak the signature.
    if not hmac.compare_digest(expected_cmac, received_cmac):
        raise ValueError("signature does not match")
    return uid.hex(), counter
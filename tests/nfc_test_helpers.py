"""Helpers for NFC tests: create tap links the way a real tag would."""

import os

from Crypto.Cipher import AES
from Crypto.Hash import CMAC

FACTORY_KEY = bytes(16)
TEST_UID = "0459205abd2390"


def _aes_cmac(key, data):
    mac = CMAC.new(key, ciphermod=AES)
    mac.update(data)
    return mac.digest()


def make_tap(counter, uid=TEST_UID, key=FACTORY_KEY):
    """Return (picc_data, cmac) exactly as a tag would put them in its link."""
    uid_bytes = bytes.fromhex(uid)
    counter_bytes = counter.to_bytes(3, "little")

    plain = bytes([0xC7]) + uid_bytes + counter_bytes + os.urandom(5)
    picc_data = AES.new(key, AES.MODE_CBC, iv=bytes(16)).encrypt(plain)

    sv2 = bytes.fromhex("3CC300010080") + uid_bytes + counter_bytes
    session_key = _aes_cmac(key, sv2)
    cmac = _aes_cmac(session_key, b"")[1::2]

    return picc_data.hex().upper(), cmac.hex().upper()
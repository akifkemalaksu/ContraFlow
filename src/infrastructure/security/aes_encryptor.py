import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.domain.services.key_encryptor import IKeyEncryptor


class AESKeyEncryptor(IKeyEncryptor):
    def __init__(self, key_hex: str) -> None:
        self._key = bytes.fromhex(key_hex)

    def encrypt(self, plaintext: str) -> tuple[str, str]:
        iv = os.urandom(12)
        ciphertext = AESGCM(self._key).encrypt(iv, plaintext.encode(), None)
        return ciphertext.hex(), iv.hex()

    def decrypt(self, ciphertext_hex: str, iv_hex: str) -> str:
        iv = bytes.fromhex(iv_hex)
        ciphertext = bytes.fromhex(ciphertext_hex)
        return AESGCM(self._key).decrypt(iv, ciphertext, None).decode()

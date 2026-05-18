from abc import ABC, abstractmethod


class IKeyEncryptor(ABC):
    @abstractmethod
    def encrypt(self, plaintext: str) -> tuple[str, str]:
        """Returns (ciphertext_hex, iv_hex)."""
        ...

    @abstractmethod
    def decrypt(self, ciphertext_hex: str, iv_hex: str) -> str: ...

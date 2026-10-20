"""Funciones para generar y validar hashes de PIN de administración."""

import hashlib
import hmac
import secrets

PIN_HASH_ALGORITHM = "pbkdf2_sha256"
PIN_HASH_ITERATIONS = 310_000
PIN_SALT_BYTES = 16


def hash_admin_pin(pin: str) -> str:
    """Genera un hash PBKDF2 con sal aleatoria; el PIN original nunca se guarda."""
    salt = secrets.token_bytes(PIN_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", pin.encode("utf-8"), salt, PIN_HASH_ITERATIONS
    )
    return f"{PIN_HASH_ALGORITHM}${PIN_HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_admin_pin(pin: str, encoded_hash: str) -> bool:
    """Compara el PIN con su hash en tiempo constante; un hash inválido falla."""
    try:
        algorithm, iterations_text, salt_hex, digest_hex = encoded_hash.split("$", 3)
        if algorithm != PIN_HASH_ALGORITHM:
            return False
        iterations = int(iterations_text)
        if iterations < 1:
            return False
        expected = bytes.fromhex(digest_hex)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)

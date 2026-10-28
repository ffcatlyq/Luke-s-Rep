#!/usr/bin/env python3
"""cookie-bridge gdrive transport 的加解密信封 —— Python 侧。

信封是浏览器扩展（WebCrypto）与本模块（cryptography）的**共享契约**，两端格式必须一致：

    {
      "v": 1,
      "alg": "AES-256-GCM",
      "kdf": {"name": "PBKDF2", "hash": "SHA-256", "iter": 200000},
      "aad": "cookie-bridge-v1",
      "salt": base64(16B), "iv": base64(12B), "ct": base64(ciphertext||tag)
    }

关键互通点（Spike 1 实测）：WebCrypto AES-GCM 输出 = ciphertext||tag(16B)，
cryptography 的 AESGCM.decrypt(iv, ct, aad) 正好直接吃 ct||tag，无需手动切 tag。

契约改动只改这一处 + 扩展 popup.js 的对应实现，并同步 docs/ARCHITECTURE.md。
"""
from __future__ import annotations

import base64

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DEFAULT_AAD = "cookie-bridge-v1"
DEFAULT_ITER = 200_000


class PassphraseMismatch(Exception):
    """GCM auth tag 校验失败——口令不匹配 / 信封被篡改。明确报错，避免静默 opaque 失败。"""


def _derive_key(passphrase: str, salt: bytes, iterations: int) -> bytes:
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                      salt=salt, iterations=iterations).derive(passphrase.encode())


def decrypt_envelope(envelope: dict, passphrase: str) -> bytes:
    """解开信封返回明文字节。口令错 → PassphraseMismatch。"""
    salt = base64.b64decode(envelope["salt"])
    iv = base64.b64decode(envelope["iv"])
    ct = base64.b64decode(envelope["ct"])
    aad = envelope.get("aad", DEFAULT_AAD).encode()
    iters = envelope.get("kdf", {}).get("iter", DEFAULT_ITER)
    key = _derive_key(passphrase, salt, iters)
    try:
        return AESGCM(key).decrypt(iv, ct, aad)
    except InvalidTag as e:
        raise PassphraseMismatch(
            "GCM auth tag verify failed: passphrase mismatch or envelope tampered"
        ) from e


def encrypt_envelope(plaintext: bytes, passphrase: str, *,
                     aad: str = DEFAULT_AAD, iterations: int = DEFAULT_ITER) -> dict:
    """加密成信封（与扩展 WebCrypto 同格式）。生产里加密由扩展做，这里供测试 round-trip。"""
    import os
    salt = os.urandom(16)
    iv = os.urandom(12)
    key = _derive_key(passphrase, salt, iterations)
    ct = AESGCM(key).encrypt(iv, plaintext, aad.encode())  # 输出 = ciphertext||tag
    b64 = lambda b: base64.b64encode(b).decode()
    return {
        "v": 1, "alg": "AES-256-GCM",
        "kdf": {"name": "PBKDF2", "hash": "SHA-256", "iter": iterations},
        "aad": aad, "salt": b64(salt), "iv": b64(iv), "ct": b64(ct),
    }

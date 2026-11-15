"""用户认证：密码哈希、JWT 签发与校验、请求鉴权依赖。

JWT 采用标准 HS256 结构，仅依赖标准库，避免额外安装依赖。
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional

from fastapi import Header, HTTPException

from backend.config.config import JWT_SECRET, JWT_EXPIRE_HOURS

PBKDF2_ITERATIONS = 210_000
JWT_ALGORITHM = "HS256"

# 未配置密钥时退化为进程内随机密钥：重启后登录态失效，仅适用于本地开发
if not JWT_SECRET:
    JWT_SECRET = secrets.token_urlsafe(32)
    print("[WARN] 未配置 JWT_SECRET，已生成临时密钥（重启后需重新登录）")


def hash_password(password: str) -> str:
    """生成 pbkdf2_sha256$迭代次数$盐$摘要 格式的密码哈希"""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """校验明文密码与存储的哈希是否匹配"""
    try:
        algorithm, iterations, salt, digest = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        expected = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations)
        )
        return hmac.compare_digest(expected.hex(), digest)
    except (ValueError, AttributeError):
        return False


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def create_access_token(user_id: str) -> str:
    """签发访问令牌"""
    now = int(time.time())
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {"sub": str(user_id), "iat": now, "exp": now + JWT_EXPIRE_HOURS * 3600}
    segments = [
        _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
        _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
    ]
    signing_input = ".".join(segments).encode("ascii")
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return ".".join(segments + [_b64encode(signature)])


def decode_access_token(token: str) -> Optional[str]:
    """校验签名、算法与有效期，通过则返回用户 ID"""
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected = hmac.new(JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64decode(signature_b64)):
            return None
        header = json.loads(_b64decode(header_b64))
        if header.get("alg") != JWT_ALGORITHM:
            return None
        payload = json.loads(_b64decode(payload_b64))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload.get("sub")
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def _extract_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """游客可访问的接口使用：带有效令牌返回用户，否则返回 None"""
    token = _extract_token(authorization)
    user_id = decode_access_token(token) if token else None
    if not user_id:
        return None

    # 延迟导入，避免 repository -> db -> auth 的循环依赖
    from backend.app import repository

    return repository.get_user(user_id)


async def require_user(authorization: Optional[str] = Header(None)) -> dict:
    """必须登录的接口使用：未登录或令牌无效返回 401"""
    user = await get_optional_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user

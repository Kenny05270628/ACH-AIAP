import os
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """加载项目根目录的 .env；已存在的环境变量优先（容器注入不会被覆盖）。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(Path(__file__).resolve().parents[2] / ".env")

SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
SILICONFLOW_BASE_URL = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
temperature = float(os.getenv("temperature", "0.7"))

# 登录令牌配置：JWT_SECRET 缺失时由 auth.py 生成临时密钥（重启失效）
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "168"))

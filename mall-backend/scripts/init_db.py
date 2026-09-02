"""初始化脚本：建库、种子数据。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402


def main() -> None:
    print(f"初始化数据库：{settings.database_url}")
    print("提示：请先执行 alembic upgrade head 建表，再导入 docs/sql/seed-data.sql")


if __name__ == "__main__":
    main()

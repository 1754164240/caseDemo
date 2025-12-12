"""脚本目录初始化，确保可以导入后端模块。"""
from pathlib import Path
import sys

# 后端根目录路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 仓库根目录路径
REPO_ROOT = PROJECT_ROOT.parent
# 迁移脚本所在目录
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"

# 确保后端根目录在 sys.path 中，便于直接运行脚本
project_root_str = str(PROJECT_ROOT)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

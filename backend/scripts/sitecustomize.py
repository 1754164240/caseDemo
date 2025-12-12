"""为脚本执行自动注入后端根目录到 sys.path。"""
from pathlib import Path
import sys

# 将后端根目录提前写入 sys.path，保证直接运行单个脚本时也能找到 app 模块
_project_root = Path(__file__).resolve().parent.parent
_project_root_str = str(_project_root)
if _project_root_str not in sys.path:
    sys.path.insert(0, _project_root_str)

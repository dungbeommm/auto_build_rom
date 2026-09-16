from pathlib import Path
import logging
from romauto.toolchain import install_tool_tree

ROOT = Path(__file__).resolve().parents[1]
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
install_tool_tree(ROOT)

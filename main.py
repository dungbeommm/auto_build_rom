import logging
from typing import Sequence
from src.app.bootstrap import setup_logging
from src.app.cli import parse_args
from src.app.workflow import execute_rom_modification
logger=logging.getLogger('main')
def main(argv:Sequence[str]|None=None)->int:
    args=parse_args(argv); setup_logging(logging.DEBUG if args.debug else logging.INFO)
    try: return execute_rom_modification(args,logger)
    except KeyboardInterrupt: logger.warning('Operation cancelled by user'); return 130
    except Exception as exc: logger.error('An error occurred during ROM modification: %s',exc,exc_info=True); return 1
if __name__=='__main__': raise SystemExit(main())

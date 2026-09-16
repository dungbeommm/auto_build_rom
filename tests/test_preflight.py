from argparse import Namespace
from src.app.preflight import run_preflight

def test_preflight_missing_rom(tmp_path):
    args=Namespace(rom=str(tmp_path/'missing.zip'),work_dir=str(tmp_path/'build'),phases=None)
    report=run_preflight(args,__import__('logging').getLogger('test'))
    assert report.has_failures()
    assert report.blockers[0].code=='ROM_NOT_FOUND'

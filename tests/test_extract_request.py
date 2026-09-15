import importlib.util, os, subprocess, tempfile, unittest, json
ROOT=os.path.dirname(os.path.dirname(__file__))
class Tests(unittest.TestCase):
  def test_issue_command(self):
    with tempfile.NamedTemporaryFile('w',delete=False) as f:
      json.dump({'issue':{'body':'/mod-rom https://example.com/a.tgz profile=all'}},f); path=f.name
    try:
      p=subprocess.run(['python3',f'{ROOT}/scripts/extract_request.py'],env={**os.environ,'GITHUB_EVENT_PATH':path},text=True,capture_output=True)
      self.assertEqual(p.returncode,0,p.stderr); self.assertIn('rom_url=https://example.com/a.tgz',p.stdout)
    finally: os.unlink(path)
  def test_reject_http(self):
    p=subprocess.run(['python3',f'{ROOT}/scripts/extract_request.py'],env={**os.environ,'INPUT_ROM_URL':'http://example.com/a.tgz'},text=True,capture_output=True)
    self.assertNotEqual(p.returncode,0)
if __name__=='__main__': unittest.main()

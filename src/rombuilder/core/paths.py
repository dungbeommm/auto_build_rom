from __future__ import annotations
from pathlib import Path

class Paths:
    def __init__(self, root: Path):
        self.root = root
        self.config = root / "config"
        self.workspace = root / "workspace"
        self.input = self.workspace / "input"
        self.source = self.workspace / "source"
        self.partitions = self.workspace / "partitions"
        self.targets = self.workspace / "targets"
        self.decoded = self.workspace / "decoded"
        self.repacked = self.workspace / "repacked"
        self.output = self.workspace / "output"
        self.state = self.workspace / "state"
        self.logs = self.workspace / "logs"
    def ensure(self):
        for p in (self.input,self.source,self.partitions,self.targets,self.decoded,self.repacked,self.output,self.state,self.logs): p.mkdir(parents=True, exist_ok=True)

"""Preflight checks for single-ROM modification."""
from __future__ import annotations
import json, shutil, zipfile, logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
from src.core.rom import RomPackage
from src.core.rom.constants import RomType
@dataclass
class PreflightFinding:
    severity:str; code:str; message:str; target:str; action:str=''; details:dict[str,Any]=field(default_factory=dict)
@dataclass
class PreflightReport:
    metadata:dict[str,Any]=field(default_factory=dict); findings:list[PreflightFinding]=field(default_factory=list)
    def add(self,**kw): self.findings.append(PreflightFinding(**kw))
    @property
    def blockers(self): return [f for f in self.findings if f.severity=='blocker']
    @property
    def risks(self): return [f for f in self.findings if f.severity=='risk']
    def to_dict(self): return {'metadata':self.metadata,'summary':{'total_findings':len(self.findings),'blockers':len(self.blockers),'risks':len(self.risks)},'findings':[asdict(f) for f in self.findings]}
    def has_failures(self,strict=False): return bool(self.blockers or (strict and self.risks))

def _inspect_zip(path):
    with zipfile.ZipFile(path) as z: names=z.namelist()
    return {'has_payload':'payload.bin' in names,'has_super':('super.img' in names or 'images/super.img' in names),'has_sparse_super_chunks':any(n.startswith('images/super.img.') for n in names),'has_brotli_images':any(n.endswith('new.dat.br') for n in names)}

def run_preflight(args, logger:logging.Logger)->PreflightReport:
    report=PreflightReport(metadata={'rom':args.rom,'work_dir':args.work_dir,'phases':args.phases or []})
    path=Path(args.rom).expanduser().resolve()
    if not path.exists():
        report.add(severity='blocker',code='ROM_NOT_FOUND',message=f'ROM path does not exist: {path}',target='rom',action='Fix --rom.')
        return report
    work=Path(args.work_dir).resolve()
    try: work.mkdir(parents=True,exist_ok=True)
    except OSError as exc: report.add(severity='blocker',code='WORK_DIR_NOT_WRITABLE',message=str(exc),target='work_dir',action='Use a writable work directory.')
    try:
        rom=RomPackage(path,work/'.preflight-rom',label='Preflight')
        report.metadata['rom_type']=rom.rom_type.name
        if rom.rom_type==RomType.UNKNOWN: report.add(severity='risk',code='ROM_TYPE_UNKNOWN',message='Could not confidently detect ROM type.',target='rom',action='Verify ZIP/payload/super structure.')
        elif path.is_file() and zipfile.is_zipfile(path): report.add(severity='info',code='ZIP_MARKERS',message='ROM ZIP markers detected.',target='rom',action='No action required.',details=_inspect_zip(path))
    except Exception as exc:
        report.add(severity='blocker',code='ROM_INIT_FAILED',message=f'Failed to initialize ROM: {exc}',target='rom',action='Check archive integrity and format.')
    logger.info('Preflight summary: blockers=%s, risks=%s, findings=%s',len(report.blockers),len(report.risks),len(report.findings))
    for f in report.findings:
        (logger.error if f.severity=='blocker' else logger.warning if f.severity=='risk' else logger.info)('[Preflight][%s] %s',f.code,f.message)
    return report

def save_preflight_report(report,output_path):
    path=Path(output_path).resolve(); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(report.to_dict(),indent=2),encoding='utf-8'); return path

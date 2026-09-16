"""ROM-level modification coordinator."""
from pathlib import Path
from src.core.modifiers.base_modifier import BaseModifier
class RomModifier(BaseModifier):
    def __init__(self,context): super().__init__(context,'RomModifier'); self.target_rom_img=self.ctx.target_rom_dir
    def run_all_modifications(self):
        self.logger.info('=== Starting ROM Modification Phase ==='); self._clean_bloatware(); self._apply_overrides(); self.logger.info('=== Modification Phase Completed ===')
    def _clean_bloatware(self):
        rules=[{'mode':'delete','target':x} for x in ('MSA','AnalyticsCore','MiuiDaemon','MiuiBugReport','MiBrowserGlobal','MiDrop','XiaomiVip','libbugreport.so')]
        if getattr(self.ctx,'syncer',None): self.ctx.syncer.execute_rules(None,self.target_rom_img,rules)
    def _apply_overrides(self):
        self._apply_common_overrides(); general=Path(f'devices/{self.ctx.rom_code}/override/general')
        if general.exists(): self.ctx.syncer.apply_override(general,self.target_rom_img)
        version=Path(f'devices/{self.ctx.rom_code}/override/{self.ctx.android_version}')
        if version.exists(): self.ctx.syncer.apply_override(version,self.target_rom_img)
    def _apply_common_overrides(self):
        common=Path('devices/common/override/os3') if str(self.ctx.rom.get_prop('ro.mi.os.version.name','')).startswith('OS3') else None
        if common and common.exists(): self.ctx.syncer.apply_override(common,self.target_rom_img)

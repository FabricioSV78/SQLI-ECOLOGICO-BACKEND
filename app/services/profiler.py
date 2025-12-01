"""
Wrapper sencillo para profiling usando cProfile + pstats.

Usar como contexto:
with Profiler(enabled=True, output_dir=settings.REPORTS_DIR) as p:
    run_heavy_function()
summary = p.get_text_summary()

Guarda un archivo .prof (binario) y un .txt con el resumen de las funciones más costosas.
"""

import os
import time
import io
import cProfile
import pstats
from typing import Optional
from app.config.config import settings


class Profiler:
    def __init__(self, enabled: bool = True, output_dir: Optional[str] = None, top: int = 30, sort: str = "cumtime"):
        self.enabled = enabled
        self.output_dir = output_dir or getattr(settings, "REPORTS_DIR", ".")
        self.top = top
        self.sort = sort
        self._prof = None
        self._start_time = None
        self._end_time = None
        self._stats_file = None
        self._text_file = None
        self._summary_text = ""

    def __enter__(self):
        if not self.enabled:
            return self

        os.makedirs(self.output_dir, exist_ok=True)
        self._prof = cProfile.Profile()
        self._start_time = time.time()
        self._prof.enable()
        return self

    def __exit__(self, exc_type, exc, tb):
        if not self.enabled or self._prof is None:
            return

        self._prof.disable()
        self._end_time = time.time()

        # Archivos de salida con timestamp
        ts = int(self._end_time)
        base = os.path.join(self.output_dir, f"profiler_{ts}")
        prof_path = f"{base}.prof"
        txt_path = f"{base}.txt"

        try:
            self._prof.dump_stats(prof_path)
            # Generar resumen textual
            s = io.StringIO()
            stats = pstats.Stats(self._prof, stream=s)
            stats.strip_dirs().sort_stats(self.sort).print_stats(self.top)
            self._summary_text = s.getvalue()
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(self._summary_text)

            self._stats_file = prof_path
            self._text_file = txt_path
        except Exception:
            # No fallar si el profiling no puede escribirse
            pass

    def get_text_summary(self) -> str:
        return self._summary_text or ""

    def get_stats_file(self) -> Optional[str]:
        return self._stats_file

    def get_text_file(self) -> Optional[str]:
        return self._text_file


__all__ = ["Profiler"]

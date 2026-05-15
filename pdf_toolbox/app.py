from __future__ import annotations

from .ui.main_window import PdfToolboxApp


def main() -> int:
    app = PdfToolboxApp()
    app.run()
    return 0

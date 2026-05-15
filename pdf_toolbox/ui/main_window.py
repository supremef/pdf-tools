from __future__ import annotations

from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk

from ..registry import ToolDefinition
from ..tools.signature_remove import SignatureRemovalPanel


TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        tool_id="signature-remove",
        name="PDF 签名移除",
        description="移除 PDF 数字签名，支持单文件、多文件和目录批量处理。",
        factory=SignatureRemovalPanel,
    ),
]


class PdfToolboxApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("PDF 功能箱")
        self.root.geometry("980x640")
        self.root.minsize(900, 580)
        self._set_window_icon()

        self._tool_panels: dict[str, object] = {}
        self._tool_frames: dict[str, ttk.Frame] = {}

        self._build_layout()

    def _asset_path(self, relative_path: str) -> Path:
        base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
        return base_path / relative_path

    def _set_window_icon(self) -> None:
        icon_path = self._asset_path("assets/app_icon.ico")
        png_path = self._asset_path("assets/pdf_tool.png")
        if icon_path.exists():
            self.root.iconbitmap(str(icon_path))
        if png_path.exists():
            self._window_icon = tk.PhotoImage(file=str(png_path))
            self.root.iconphoto(True, self._window_icon)

    def _build_layout(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(self.root, padding=(18, 18, 10, 18))
        sidebar.grid(row=0, column=0, sticky="nsw")

        content = ttk.Frame(self.root, padding=(8, 18, 18, 18))
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        title = ttk.Label(
            sidebar,
            text="PDF 功能箱",
            font=("Microsoft YaHei UI", 16, "bold"),
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            sidebar,
            text="便携桌面工具，后续可继续扩展更多 PDF 功能。",
            wraplength=220,
            justify="left",
        )
        subtitle.pack(anchor="w", pady=(8, 18))

        ttk.Label(
            content,
            text="功能面板",
            font=("Microsoft YaHei UI", 12, "bold"),
        ).grid(row=0, column=0, sticky="w")

        panel_host = ttk.Frame(content)
        panel_host.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        panel_host.columnconfigure(0, weight=1)
        panel_host.rowconfigure(0, weight=1)

        for tool in TOOLS:
            button = ttk.Button(
                sidebar,
                text=tool.name,
                width=24,
                command=lambda tool_id=tool.tool_id: self.show_tool(tool_id),
            )
            button.pack(anchor="w", fill="x", pady=(0, 8))

            frame = ttk.Frame(panel_host)
            frame.grid(row=0, column=0, sticky="nsew")

            panel = tool.factory()
            panel.build(frame)

            self._tool_frames[tool.tool_id] = frame
            self._tool_panels[tool.tool_id] = panel

        self.show_tool(TOOLS[0].tool_id)

    def show_tool(self, tool_id: str) -> None:
        for frame in self._tool_frames.values():
            frame.grid_remove()
        self._tool_frames[tool_id].grid()

    def run(self) -> None:
        self.root.mainloop()

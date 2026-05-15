from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import tkinter as tk
from tkinter import ttk


class ToolPanel(Protocol):
    def build(self, parent: ttk.Frame) -> None:
        ...


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    tool_id: str
    name: str
    description: str
    factory: type[ToolPanel]

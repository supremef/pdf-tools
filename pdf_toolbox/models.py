from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SignatureRemovalOptions:
    input_files: list[Path]
    input_directory: Path | None
    output_directory: Path
    keep_signature_appearance: bool = True


@dataclass(slots=True)
class PermissionRemovalOptions:
    input_files: list[Path]
    input_directory: Path | None
    output_directory: Path


@dataclass(slots=True)
class TaskResult:
    success: bool
    message: str
    processed_files: int = 0
    output_files: list[Path] | None = None

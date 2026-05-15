from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..models import PermissionRemovalOptions
from ..services.permission_removal import remove_pdf_permissions


class PermissionRemovalPanel:
    def __init__(self) -> None:
        self.selected_files: list[Path] = []
        self.input_mode_var = tk.StringVar(value="files")
        self.files_var = tk.StringVar(value="未选择文件")
        self.input_dir_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.status_var = tk.StringVar(value="请选择输入来源和输出目录，然后点击执行。")
        self.file_row: ttk.Frame | None = None
        self.directory_row: ttk.Frame | None = None

    def build(self, parent: ttk.Frame) -> None:
        container = ttk.Frame(parent, padding=20)
        container.pack(fill="both", expand=True)

        title = ttk.Label(
            container,
            text="PDF 权限限制移除",
            font=("Microsoft YaHei UI", 14, "bold"),
        )
        title.pack(anchor="w")

        desc = ttk.Label(
            container,
            text=(
                "移除无打开密码 PDF 的所有者权限限制，恢复编辑、打印、复制等操作。"
                "支持选择一个或多个 PDF，也支持选择文件夹批量处理。"
            ),
            wraplength=760,
            justify="left",
        )
        desc.pack(anchor="w", pady=(8, 18))

        source_frame = ttk.LabelFrame(container, text="输入来源", padding=14)
        source_frame.pack(fill="x", pady=(0, 10))

        mode_row = ttk.Frame(source_frame)
        mode_row.pack(fill="x", pady=(0, 8))

        ttk.Radiobutton(
            mode_row,
            text="选择 PDF 文件",
            variable=self.input_mode_var,
            value="files",
            command=self._sync_input_mode,
        ).pack(side="left")

        ttk.Radiobutton(
            mode_row,
            text="选择文件夹",
            variable=self.input_mode_var,
            value="directory",
            command=self._sync_input_mode,
        ).pack(side="left", padx=(24, 0))

        self.file_row = self._build_path_row(
            source_frame,
            label="PDF 文件",
            value_var=self.files_var,
            button_text="选择文件",
            command=self._pick_files,
            pack_now=False,
        )
        self.directory_row = self._build_path_row(
            source_frame,
            label="输入文件夹",
            value_var=self.input_dir_var,
            button_text="选择文件夹",
            command=self._pick_input_directory,
            pack_now=False,
        )

        self._build_path_row(
            container,
            label="输出目录",
            value_var=self.output_dir_var,
            button_text="选择目录",
            command=self._pick_output_directory,
        )

        hint_frame = ttk.LabelFrame(container, text="处理说明", padding=14)
        hint_frame.pack(fill="x", pady=(6, 14))

        hint = ttk.Label(
            hint_frame,
            text=(
                "此功能适用于没有打开密码、但限制编辑/打印/复制的 PDF。"
                "如果 PDF 本身需要打开密码，需要先输入正确密码才能处理。"
            ),
            wraplength=760,
            justify="left",
        )
        hint.pack(anchor="w")

        action_row = ttk.Frame(container)
        action_row.pack(fill="x", pady=(6, 12))

        run_button = ttk.Button(action_row, text="执行权限移除", command=self._run)
        run_button.pack(side="left")

        status = ttk.Label(
            container,
            textvariable=self.status_var,
            wraplength=760,
            justify="left",
        )
        status.pack(fill="x")

        self._sync_input_mode()

    def _build_path_row(
        self,
        parent: ttk.Frame,
        label: str,
        value_var: tk.StringVar,
        button_text: str,
        command: Callable[[], None],
        pack_now: bool = True,
    ) -> ttk.Frame:
        row = ttk.Frame(parent)
        if pack_now:
            row.pack(fill="x", pady=6)

        ttk.Label(row, text=label, width=16).pack(side="left")
        entry = ttk.Entry(row, textvariable=value_var)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Button(row, text=button_text, command=command).pack(side="left")
        return row

    def _sync_input_mode(self) -> None:
        if self.file_row is None or self.directory_row is None:
            return

        self.file_row.pack_forget()
        self.directory_row.pack_forget()

        if self.input_mode_var.get() == "files":
            self.file_row.pack(fill="x", pady=6)
            self.status_var.set("请选择一个或多个 PDF 文件，然后点击执行。")
        else:
            self.directory_row.pack(fill="x", pady=6)
            self.status_var.set("请选择包含 PDF 的文件夹，然后点击执行。")

    def _pick_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="选择一个或多个 PDF 文件",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if not paths:
            return

        self.selected_files = [Path(path) for path in paths]
        display = "；".join(path.name for path in self.selected_files)
        self.files_var.set(display)
        self.status_var.set(f"已选择 {len(self.selected_files)} 个文件。")

    def _pick_input_directory(self) -> None:
        path = filedialog.askdirectory(title="选择 PDF 输入目录")
        if not path:
            return

        self.input_dir_var.set(path)
        self.status_var.set("已设置输入文件夹。")

    def _pick_output_directory(self) -> None:
        path = filedialog.askdirectory(title="选择输出目录")
        if not path:
            return

        self.output_dir_var.set(path)
        self.status_var.set("已设置输出目录。")

    def _run(self) -> None:
        input_mode = self.input_mode_var.get()
        if input_mode == "files" and not self.selected_files:
            messagebox.showwarning("缺少 PDF 文件", "请先选择一个或多个 PDF 文件。")
            return

        if input_mode == "directory" and not self.input_dir_var.get().strip():
            messagebox.showwarning("缺少输入文件夹", "请先选择一个包含 PDF 的文件夹。")
            return

        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            messagebox.showwarning("缺少输出目录", "请先选择输出目录。")
            return

        options = PermissionRemovalOptions(
            input_files=self.selected_files if input_mode == "files" else [],
            input_directory=(
                Path(self.input_dir_var.get()).expanduser()
                if input_mode == "directory" and self.input_dir_var.get().strip()
                else None
            ),
            output_directory=Path(output_dir).expanduser(),
        )

        self.status_var.set("正在处理，请稍候...")

        result = remove_pdf_permissions(options)
        self.status_var.set(result.message)

        if result.success:
            messagebox.showinfo("处理完成", result.message)
        else:
            messagebox.showerror("处理失败", result.message)

from __future__ import annotations

from pathlib import Path

from ..models import PermissionRemovalOptions, TaskResult


def _collect_input_files(options: PermissionRemovalOptions) -> list[Path]:
    files: list[Path] = []

    for file_path in options.input_files:
        if file_path.suffix.lower() == ".pdf" and file_path.is_file():
            files.append(file_path)

    if options.input_directory and options.input_directory.is_dir():
        files.extend(
            sorted(path for path in options.input_directory.glob("*.pdf") if path.is_file())
        )

    seen: set[Path] = set()
    deduped: list[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(path)

    return deduped


def _available_output_path(output_directory: Path, source_file: Path) -> Path:
    base_name = f"{source_file.stem}_unlocked"
    candidate = output_directory / f"{base_name}.pdf"
    index = 1

    while candidate.exists():
        candidate = output_directory / f"{base_name}_{index}.pdf"
        index += 1

    return candidate


def _unlock_pdf_permissions(source_file: Path, target_file: Path) -> bool:
    try:
        import pikepdf
        from pikepdf import PasswordError
    except ImportError as exc:
        raise RuntimeError("未检测到 pikepdf 依赖，暂时无法移除 PDF 权限限制。") from exc

    try:
        with pikepdf.open(source_file, password="") as pdf:
            was_encrypted = bool(pdf.is_encrypted)
            try:
                pdf.save(target_file)
            except PermissionError as exc:
                raise RuntimeError(
                    f"无法写入输出文件：{target_file}。请关闭正在打开的同名 PDF，"
                    "或选择其他输出目录后重试。"
                ) from exc
            return was_encrypted
    except PasswordError as exc:
        raise RuntimeError(
            "此 PDF 需要打开密码，无法无密码移除权限限制。"
        ) from exc


def remove_pdf_permissions(options: PermissionRemovalOptions) -> TaskResult:
    source_files = _collect_input_files(options)
    if not source_files:
        return TaskResult(success=False, message="没有找到可处理的 PDF 文件。")

    options.output_directory.mkdir(parents=True, exist_ok=True)

    output_files: list[Path] = []
    unlocked_count = 0
    copied_count = 0

    for source_file in source_files:
        target_file = _available_output_path(options.output_directory, source_file)
        try:
            was_encrypted = _unlock_pdf_permissions(source_file, target_file)
        except Exception as exc:
            return TaskResult(
                success=False,
                message=f"处理 {source_file.name} 失败：{exc}",
                processed_files=len(output_files),
                output_files=output_files,
            )

        output_files.append(target_file)
        if was_encrypted:
            unlocked_count += 1
        else:
            copied_count += 1

    message_parts = [
        f"处理完成，共输出 {len(output_files)} 个文件",
        f"解除权限限制 {unlocked_count} 个",
    ]
    if copied_count:
        message_parts.append(f"另有 {copied_count} 个文件本身未加密，已重新保存副本")

    return TaskResult(
        success=True,
        message="，".join(message_parts) + "。",
        processed_files=len(output_files),
        output_files=output_files,
    )

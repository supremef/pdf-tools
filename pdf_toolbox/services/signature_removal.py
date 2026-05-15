from __future__ import annotations

from pathlib import Path

from ..models import SignatureRemovalOptions, TaskResult


def _collect_input_files(options: SignatureRemovalOptions) -> list[Path]:
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
    base_name = f"{source_file.stem}_unsigned"
    candidate = output_directory / f"{base_name}.pdf"
    index = 1

    while candidate.exists():
        candidate = output_directory / f"{base_name}_{index}.pdf"
        index += 1

    return candidate


def _extract_signature_appearances(pdf, keep_signature_appearance: bool):
    if not keep_signature_appearance:
        return []

    signature_appearances = []

    for page_index, page in enumerate(pdf.pages):
        if "/Annots" not in page:
            continue

        for annot in page.Annots:
            if str(annot.get("/Subtype", "")) != "/Widget":
                continue
            if str(annot.get("/FT", "")) != "/Sig":
                continue

            rect = annot.get("/Rect", None)
            appearance = annot.get("/AP", None)
            if rect is None or appearance is None:
                continue

            normal_appearance = appearance.get("/N", None)
            if normal_appearance is None:
                continue

            signature_appearances.append((normal_appearance, rect, page_index))

    return signature_appearances


def _remove_signature_fields(pdf):
    from pikepdf import Array

    removed_fields = 0
    removed_annotations = 0
    removed_sigflags = False
    removed_perms = False

    if "/AcroForm" in pdf.Root:
        acroform = pdf.Root.AcroForm
        fields = acroform.get("/Fields", [])
        remaining_fields = Array()

        for field in fields:
            if str(field.get("/FT", "")) == "/Sig":
                removed_fields += 1
                continue
            remaining_fields.append(field)

        acroform.Fields = remaining_fields

        if "/SigFlags" in acroform:
            del acroform.SigFlags
            removed_sigflags = True

    if "/Perms" in pdf.Root:
        del pdf.Root.Perms
        removed_perms = True

    for page in pdf.pages:
        if "/Annots" not in page:
            continue

        remaining_annots = Array()
        for annot in page.Annots:
            subtype = str(annot.get("/Subtype", ""))
            field_type = str(annot.get("/FT", ""))
            if subtype == "/Widget" and field_type == "/Sig":
                removed_annotations += 1
                continue
            remaining_annots.append(annot)

        page.Annots = remaining_annots

    return {
        "removed_fields": removed_fields,
        "removed_annotations": removed_annotations,
        "removed_sigflags": removed_sigflags,
        "removed_perms": removed_perms,
    }


def _restore_signature_appearances(pdf, signature_appearances) -> int:
    from pikepdf import Array, Dictionary, Name

    restored = 0

    for appearance_stream, rect, page_index in signature_appearances:
        page = pdf.pages[page_index]
        stamp_annot = pdf.make_indirect(
            Dictionary(
                {
                    "/Type": Name.Annot,
                    "/Subtype": Name.Stamp,
                    "/Rect": rect,
                    "/F": 4,
                    "/AP": Dictionary({"/N": appearance_stream}),
                }
            )
        )

        if "/Annots" in page:
            page.Annots.append(stamp_annot)
        else:
            page.Annots = Array([stamp_annot])

        restored += 1

    return restored


def _remove_signature_from_file(source_file: Path, target_file: Path, keep_signature_appearance: bool):
    try:
        import pikepdf
    except ImportError as exc:
        raise RuntimeError("未检测到 pikepdf 依赖，暂时无法执行签名移除。") from exc

    with pikepdf.open(source_file) as pdf:
        signature_appearances = _extract_signature_appearances(pdf, keep_signature_appearance)
        stats = _remove_signature_fields(pdf)

        restored_appearances = 0
        if keep_signature_appearance and signature_appearances:
            restored_appearances = _restore_signature_appearances(pdf, signature_appearances)

        try:
            pdf.save(target_file)
        except PermissionError as exc:
            raise RuntimeError(
                f"无法写入输出文件：{target_file}。请关闭正在打开的同名 PDF，"
                "或选择其他输出目录后重试。"
            ) from exc

    stats["restored_appearances"] = restored_appearances
    return stats


def remove_pdf_signatures(options: SignatureRemovalOptions) -> TaskResult:
    source_files = _collect_input_files(options)
    if not source_files:
        return TaskResult(success=False, message="没有找到可处理的 PDF 文件。")

    options.output_directory.mkdir(parents=True, exist_ok=True)

    output_files: list[Path] = []
    total_removed_fields = 0
    total_removed_annotations = 0
    total_removed_sigflags = 0
    total_removed_perms = 0
    total_restored_appearances = 0

    for source_file in source_files:
        target_file = _available_output_path(options.output_directory, source_file)
        try:
            stats = _remove_signature_from_file(
                source_file=source_file,
                target_file=target_file,
                keep_signature_appearance=options.keep_signature_appearance,
            )
        except Exception as exc:
            return TaskResult(
                success=False,
                message=f"处理 {source_file.name} 失败：{exc}",
                processed_files=len(output_files),
                output_files=output_files,
            )

        output_files.append(target_file)

        total_removed_fields += stats["removed_fields"]
        total_removed_annotations += stats["removed_annotations"]
        total_removed_sigflags += 1 if stats["removed_sigflags"] else 0
        total_removed_perms += 1 if stats["removed_perms"] else 0
        total_restored_appearances += stats["restored_appearances"]

    any_change = any(
        [
            total_removed_fields,
            total_removed_annotations,
            total_removed_sigflags,
            total_removed_perms,
        ]
    )

    if not any_change:
        return TaskResult(
            success=False,
            message="处理完成，但没有检测到可移除的数字签名限制。",
            processed_files=len(output_files),
            output_files=output_files,
        )

    message_parts = [
        f"处理完成，共输出 {len(output_files)} 个文件",
        f"移除了 {total_removed_fields} 个签名字段",
        f"删除了 {total_removed_annotations} 个签名注释",
    ]

    if total_removed_sigflags:
        message_parts.append(f"清除了 {total_removed_sigflags} 处 SigFlags")
    if total_removed_perms:
        message_parts.append(f"清除了 {total_removed_perms} 处 Perms")
    if options.keep_signature_appearance:
        message_parts.append(f"保留了 {total_restored_appearances} 处签名外观")

    return TaskResult(
        success=True,
        message="，".join(message_parts) + "。",
        processed_files=len(output_files),
        output_files=output_files,
    )

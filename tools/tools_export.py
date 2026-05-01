from __future__ import annotations

import base64
import datetime as dt
import json
import os
from io import BytesIO
from pathlib import Path
from textwrap import wrap
from typing import Any, Dict, Iterable, List, Literal, Optional, Union

import pandas as pd
from langchain_core.tools import tool
from PIL import Image

try:  # Optional dependency for chart rendering
    import matplotlib.pyplot as plt  # type: ignore
except Exception:  # pragma: no cover - handled at runtime
    plt = None

try:  # Optional dependency for PDF generation
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
except Exception:  # pragma: no cover - handled at runtime
    canvas = None
    A4 = None
    cm = None
    pdfmetrics = None

_PDF_FONT_NAME = "STSong-Light"
_PDF_FONT_REGISTERED = False


ExportAction = Literal["chart_png", "data_export", "report_pdf"]
_DEFAULT_EXPORT_DIR = Path(os.getenv("CHATBI_EXPORT_DIR", Path(__file__).resolve().parent.parent / "exports"))


def _ensure_export_dir(target_dir: Optional[Union[str, Path]]) -> Path:
    export_dir = Path(target_dir) if target_dir else _DEFAULT_EXPORT_DIR
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


def _normalize_filename(filename: Optional[str], suffix: str) -> str:
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = filename or f"export_{timestamp}"
    if suffix.startswith("."):
        extension = suffix
    else:
        extension = f".{suffix}"
    if stem.lower().endswith(extension.lower()):
        return stem
    return f"{stem}{extension}"


def _load_chart_payload(chart_payload: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(chart_payload, dict):
        return chart_payload
    if isinstance(chart_payload, str):
        try:
            return json.loads(chart_payload)
        except json.JSONDecodeError as exc:
            raise ValueError("chart_payload 字串不是有效的 JSON。") from exc
    raise TypeError("chart_payload 必須是 dict 或 JSON 字串。")


def _save_chart_from_base64(image_base64: str, path: Path, resize_width: Optional[int] = None, resize_height: Optional[int] = None) -> None:
    binary = base64.b64decode(image_base64)
    with Image.open(BytesIO(binary)) as img:
        if resize_width and resize_height:
            img = img.resize((resize_width, resize_height), resample=Image.LANCZOS)
        elif resize_width:
            ratio = resize_width / img.width
            img = img.resize((resize_width, int(img.height * ratio)), resample=Image.LANCZOS)
        elif resize_height:
            ratio = resize_height / img.height
            img = img.resize((int(img.width * ratio), resize_height), resample=Image.LANCZOS)
        img.save(path, format="PNG")


def _draw_matplotlib_chart(chart_payload: Dict[str, Any], path: Path, width: int, height: int, dpi: int) -> None:
    if plt is None:
        raise RuntimeError("匯出 PNG 需要安裝 matplotlib，請安裝後再試。")

    title = chart_payload.get("title", {}).get("text") or chart_payload.get("title") or ""
    x_axis = chart_payload.get("xAxis", {})
    if isinstance(x_axis, list):
        categories = x_axis[0].get("categories", [])
    else:
        categories = x_axis.get("categories", [])

    y_title = ""
    y_axis = chart_payload.get("yAxis", {})
    if isinstance(y_axis, list):
        y_title = y_axis[0].get("title", {}).get("text", "")
    else:
        y_title = y_axis.get("title", {}).get("text", "")

    series_list = chart_payload.get("series", [])
    if not series_list:
        raise ValueError("chart_payload 缺少 series，無法繪製圖表。")

    inches_width = max(width / dpi, 8.0)
    inches_height = max(height / dpi, 4.5)
    fig, ax = plt.subplots(figsize=(inches_width, inches_height), dpi=dpi)

    x_values = list(range(len(categories))) if categories else None
    for series in series_list:
        data = series.get("data", [])
        name = series.get("name", "")
        series_type = (series.get("type") or chart_payload.get("chart", {}).get("type") or "line").lower()

        if series_type in {"line", "spline"}:
            ax.plot(categories if categories else range(len(data)), data, label=name, marker="o")
        elif series_type in {"area"}:
            ax.fill_between(categories if categories else range(len(data)), data, alpha=0.3)
            ax.plot(categories if categories else range(len(data)), data, label=name, linewidth=1.5)
        elif series_type in {"column", "bar"}:
            indices = range(len(data))
            if x_values is None:
                x_values = list(indices)
            offset = series_list.index(series) * 0.2
            ax.bar([x + offset for x in x_values], data, width=0.2, label=name)
        else:
            ax.plot(categories if categories else range(len(data)), data, label=name, marker="o")

    ax.set_title(title)
    if categories:
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=45, ha="right")
    if y_title:
        ax.set_ylabel(y_title)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


def _export_chart_png(chart_payload: Union[str, Dict[str, Any]], output_dir: Path, filename: Optional[str], width: int, height: int, dpi: int) -> Dict[str, Any]:
    export_name = _normalize_filename(filename, ".png")
    output_path = output_dir / export_name
    payload = _load_chart_payload(chart_payload)

    if "image_base64" in payload:
        resize_width = payload.get("width") or width
        resize_height = payload.get("height") or height
        _save_chart_from_base64(payload["image_base64"], output_path, resize_width=resize_width, resize_height=resize_height)
    else:
        chart_width = payload.get("width", width)
        chart_height = payload.get("height", height)
        _draw_matplotlib_chart(payload, output_path, chart_width, chart_height, dpi)

    return {
        "status": "success",
        "type": "chart_png",
        "file_path": str(output_path),
        "filename": output_path.name,
    }


def _build_dataframe(rows: Iterable[Any], columns: Optional[List[str]]) -> pd.DataFrame:
    if isinstance(rows, pd.DataFrame):
        df = rows.copy()
        if columns:
            missing = [col for col in columns if col not in df.columns]
            if missing:
                raise ValueError(f"提供的 DataFrame 缺少欄位: {missing}")
            return df[columns]
        return df

    if isinstance(rows, list):
        if rows and isinstance(rows[0], dict):
            df = pd.DataFrame(rows)
            if columns:
                df = df.reindex(columns=columns)
            return df
        elif rows and isinstance(rows[0], (list, tuple)):
            if not columns:
                raise ValueError("rows 是列表形式時必須提供 columns。")
            df = pd.DataFrame(rows, columns=columns)
            return df

    raise TypeError("rows 資料格式不支援，請提供 list[dict]、list[list] 或 pandas.DataFrame。")


def _resolve_excel_engine(preferred_engine: Optional[str] = None) -> str:
    candidates = []
    if preferred_engine:
        candidates.append(preferred_engine)
    candidates.extend(["openpyxl", "xlsxwriter"])
    for engine in candidates:
        try:
            __import__(engine)
            return engine
        except ImportError:
            continue
    raise RuntimeError("匯出 Excel 需要 openpyxl 或 xlsxwriter，請安裝任一套件。")


def _export_data_files(
    rows: Iterable[Any],
    columns: Optional[List[str]],
    output_dir: Path,
    filename: Optional[str],
    include_csv: bool,
    include_excel: bool,
    excel_engine: Optional[str] = None,
) -> Dict[str, Any]:
    df = _build_dataframe(rows, columns)
    payload: Dict[str, Any] = {"status": "success", "type": "data_export", "columns": list(df.columns), "row_count": len(df), "files": {}}

    if include_csv:
        csv_name = _normalize_filename(filename, ".csv")
        csv_path = output_dir / csv_name
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        payload["files"]["csv"] = str(csv_path)

    if include_excel:
        xlsx_name = _normalize_filename(filename, ".xlsx")
        xlsx_path = output_dir / xlsx_name
        engine = _resolve_excel_engine(excel_engine)
        df.to_excel(xlsx_path, index=False, engine=engine)
        payload["files"]["excel"] = str(xlsx_path)

    return payload


def _ensure_pdf_font() -> None:
    global _PDF_FONT_REGISTERED  # noqa: PLW0603
    if _PDF_FONT_REGISTERED or pdfmetrics is None:
        return
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(_PDF_FONT_NAME))
        _PDF_FONT_REGISTERED = True
    except Exception:
        _PDF_FONT_REGISTERED = False


def _set_pdf_font(pdf: canvas.Canvas, size: int) -> None:
    if _PDF_FONT_REGISTERED:
        pdf.setFont(_PDF_FONT_NAME, size)
    else:
        pdf.setFont("Helvetica", size)


def _start_text_page(pdf: canvas.Canvas) -> None:
    _set_pdf_font(pdf, 11)


def _write_wrapped_text(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    line_height: float,
    margin_bottom: float,
) -> float:
    max_chars = max(int(max_width / 6), 20)
    lines = wrap(text, width=max_chars)
    current_y = y
    for line in lines:
        if current_y < margin_bottom:
            pdf.showPage()
            _start_text_page(pdf)
            current_y = A4[1] - margin_bottom
        pdf.drawString(x, current_y, line)
        current_y -= line_height
    return current_y


def _insert_table(
    pdf: canvas.Canvas,
    table: Dict[str, Any],
    x: float,
    y: float,
    max_width: float,
    line_height: float,
    margin_bottom: float,
) -> float:
    title = table.get("title", "Data Table")
    rows = table.get("rows", [])
    columns = table.get("columns")
    y = _write_wrapped_text(pdf, f"[表格] {title}", x, y, max_width, line_height, margin_bottom)

    if not rows:
        return _write_wrapped_text(pdf, "（無資料）", x + 10, y, max_width - 10, line_height, margin_bottom)

    if columns is None and rows and isinstance(rows[0], dict):
        columns = list(rows[0].keys())

    if columns:
        header_line = " | ".join(str(col) for col in columns)
        y = _write_wrapped_text(pdf, header_line, x + 10, y, max_width - 10, line_height, margin_bottom)
        y = _write_wrapped_text(pdf, "-" * min(int(max_width / 3), 80), x + 10, y, max_width - 10, line_height, margin_bottom)

    for row in rows:
        if isinstance(row, dict):
            values = [row.get(col, "") for col in columns] if columns else list(row.values())
        else:
            values = row
        line = " | ".join(str(value) for value in values)
        y = _write_wrapped_text(pdf, line, x + 10, y, max_width - 10, line_height, margin_bottom)

    return y


def _insert_chart_image(
    pdf: canvas.Canvas,
    image_path: str,
    x: float,
    y: float,
    max_width: float,
    margin_bottom: float,
) -> float:
    if not os.path.exists(image_path):
        return _write_wrapped_text(pdf, f"圖像無法載入：{image_path}", x, y, max_width, 14, margin_bottom)

    with Image.open(image_path) as img:
        img_width, img_height = img.size
        ratio = min(max_width / img_width, (y - margin_bottom) / img_height, 1.0)
        display_width = img_width * ratio
        display_height = img_height * ratio

    if y - display_height < margin_bottom:
        pdf.showPage()
        _start_text_page(pdf)
        y = A4[1] - margin_bottom

    pdf.drawImage(image_path, x, y - display_height, width=display_width, height=display_height, preserveAspectRatio=True, anchor="sw")
    return y - display_height - 12


def _export_pdf_report(
    report: Dict[str, Any],
    output_dir: Path,
    filename: Optional[str],
) -> Dict[str, Any]:
    if canvas is None or A4 is None or cm is None:
        raise RuntimeError("匯出 PDF 需要安裝 reportlab，請安裝後再試。")

    pdf_name = _normalize_filename(filename, ".pdf")
    pdf_path = output_dir / pdf_name
    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)

    margin = 1.75 * cm
    line_height = 14
    current_y = A4[1] - margin
    content_width = A4[0] - 2 * margin

    _start_text_page(pdf)

    title = report.get("title") or f"分析報告 - {dt.datetime.now():%Y-%m-%d}"
    _ensure_pdf_font()
    _set_pdf_font(pdf, 16)
    pdf.drawString(margin, current_y, title)
    current_y -= 24
    _set_pdf_font(pdf, 11)

    summary_text = (
        report.get("summary")
        or report.get("description")
        or report.get("overview")
        or report.get("abstract")
    )
    if summary_text:
        current_y = _write_wrapped_text(pdf, f"摘要：{summary_text}", margin, current_y, content_width, line_height, margin)
        current_y -= 8

    questions_list = report.get("questions") or report.get("qa") or report.get("q_and_a")
    if questions_list:
        current_y = _write_wrapped_text(pdf, "提問與回答：", margin, current_y, content_width, line_height, margin)
        for item in questions_list:
            question = item.get("question") or item.get("prompt") or ""
            answer = item.get("answer") or item.get("response") or ""
            if question:
                current_y = _write_wrapped_text(pdf, f"Q: {question}", margin + 10, current_y, content_width - 10, line_height, margin)
            if answer:
                current_y = _write_wrapped_text(pdf, f"A: {answer}", margin + 10, current_y, content_width - 10, line_height, margin)
            current_y -= 6

    insights_list = report.get("insights") or report.get("key_findings") or report.get("highlights")
    if insights_list:
        current_y = _write_wrapped_text(pdf, "洞察：", margin, current_y, content_width, line_height, margin)
        for insight in insights_list:
            current_y = _write_wrapped_text(pdf, f"- {insight}", margin + 10, current_y, content_width - 10, line_height, margin)
        current_y -= 6

    tables_list = report.get("tables") or report.get("data_tables") or report.get("tables_data")
    if tables_list:
        current_y = _write_wrapped_text(pdf, "資料表：", margin, current_y, content_width, line_height, margin)
        for table in tables_list:
            current_y = _insert_table(pdf, table, margin, current_y, content_width, line_height, margin)
            current_y -= 10

    charts_list = report.get("charts") or report.get("chart_paths") or report.get("figures")
    if charts_list:
        current_y = _write_wrapped_text(pdf, "圖表：", margin, current_y, content_width, line_height, margin)
        for chart in charts_list:
            chart_path = chart if isinstance(chart, str) else chart.get("path")
            subtitle = chart.get("title") if isinstance(chart, dict) else None
            if subtitle:
                current_y = _write_wrapped_text(pdf, subtitle, margin + 10, current_y, content_width - 10, line_height, margin)
            current_y = _insert_chart_image(pdf, str(chart_path), margin + 10, current_y, content_width - 20, margin)
            current_y -= 6

    additional_text = report.get("content") or report.get("body") or report.get("text")
    if isinstance(additional_text, str):
        current_y = _write_wrapped_text(pdf, additional_text, margin, current_y, content_width, line_height, margin)

    if not any([summary_text, questions_list, insights_list, tables_list, charts_list, additional_text]):
        current_y = _write_wrapped_text(pdf, "（未提供可呈現的報告內容）", margin, current_y, content_width, line_height, margin)
        current_y -= 6
        pretty_payload = json.dumps(report, ensure_ascii=False, indent=2)
        _write_wrapped_text(pdf, pretty_payload, margin, current_y, content_width, line_height, margin)

    pdf.save()

    return {
        "status": "success",
        "type": "report_pdf",
        "file_path": str(pdf_path),
        "filename": pdf_path.name,
    }


def _export_artifacts(
    action: ExportAction,
    payload: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
    filename: Optional[str] = None,
    width: int = 1920,
    height: int = 1080,
    dpi: int = 300,
    include_csv: bool = True,
    include_excel: bool = True,
    excel_engine: Optional[str] = None,
) -> Dict[str, Any]:
    """
    匯出工具支援：
    - 圖表 PNG：提供 chart_payload（可為 dict 或 JSON 字串），可選擇直接傳入 base64 圖像。
    - 資料 CSV/Excel：提供 rows（list[dict]、list[list] 或 DataFrame）與 columns。
    - PDF 報告：提供 title、summary、questions、insights、tables、charts 等內容。
    """

    payload = payload or {}
    export_dir = _ensure_export_dir(output_dir)

    if action == "chart_png":
        chart_payload = payload.get("chart_payload") or payload
        return _export_chart_png(chart_payload, export_dir, filename, width, height, dpi)

    if action == "data_export":
        rows = payload.get("rows")
        if rows is None:
            raise ValueError("data_export 行為需要提供 rows。")
        columns = payload.get("columns")
        return _export_data_files(rows, columns, export_dir, filename, include_csv, include_excel, excel_engine)

    if action == "report_pdf":
        return _export_pdf_report(payload, export_dir, filename)

    raise ValueError(f"未知的 action：{action}")


export_artifacts_tool = tool(
    "export_artifacts",
    description=(
        "匯出分析產物。action 可為 'chart_png' (匯出圖表 PNG)、'data_export' (匯出資料 CSV/Excel)、"
        "'report_pdf' (產生分析報告 PDF)。"
    ),
)(_export_artifacts)


def export_artifacts(**kwargs: Any) -> Dict[str, Any]:
    """
    直接呼叫匯出函式的便利介面，測試或離線腳本可使用。
    """
    return _export_artifacts(**kwargs)


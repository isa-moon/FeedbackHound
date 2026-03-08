"""报告生成与导出。"""

from __future__ import annotations

from datetime import datetime

import markdown2
import pdfkit

from config import EXPORT_FILENAME_PREFIX


class ReportGenerationError(Exception):
    """报告导出错误。"""


def build_markdown_report(title: str, subtitle: str, body: str) -> str:
    """封装 Markdown 报告。"""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"# {title}\n\n> {subtitle}\n\n生成时间：{generated_at}\n\n---\n\n{body.strip()}\n"


def generate_report_filename(suffix: str, extension: str) -> str:
    """生成导出文件名。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{EXPORT_FILENAME_PREFIX}_{suffix}_{timestamp}.{extension}"


def markdown_to_bytes(markdown_text: str) -> bytes:
    """导出 Markdown 字节流。"""
    return markdown_text.encode("utf-8")


def markdown_to_pdf_bytes(markdown_text: str) -> bytes:
    """将 Markdown 转换为 PDF 字节流。"""
    html = markdown2.markdown(markdown_text)
    styled_html = f"""
    <html>
      <head>
        <meta charset=\"utf-8\" />
        <style>
          body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 24px; }}
          h1, h2, h3 {{ color: #1f2937; }}
          blockquote {{ color: #4b5563; border-left: 4px solid #d1d5db; padding-left: 12px; }}
          code {{ background: #f3f4f6; padding: 2px 4px; }}
        </style>
      </head>
      <body>{html}</body>
    </html>
    """
    try:
        pdf_data = pdfkit.from_string(styled_html, False)
    except OSError as exc:
        raise ReportGenerationError(
            "当前环境缺少 wkhtmltopdf，暂时无法导出 PDF，请先下载 Markdown 报告。"
        ) from exc

    if not pdf_data:
        raise ReportGenerationError("PDF 导出失败，请改为下载 Markdown 报告。")
    return pdf_data

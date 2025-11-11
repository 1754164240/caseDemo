from typing import List, Optional, Dict

from docx import Document
import PyPDF2
import openpyxl


class DocumentParser:
    """文档解析服务，负责不同格式的文本抽取"""

    MAX_CONSECUTIVE_EMPTY_ROWS = 2000

    @staticmethod
    def parse_docx(file_path: str) -> str:
        try:
            doc = Document(file_path)
            text = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
            result = "\n".join(text)
            print(f"[INFO] DOCX 解析成功，提取 {len(text)} 个段落")
            return result
        except Exception as exc:
            print(f"[ERROR] DOCX 解析失败: {exc}")
            raise

    @staticmethod
    def parse_pdf(file_path: str) -> str:
        try:
            text = []
            with open(file_path, "rb") as file_obj:
                pdf_reader = PyPDF2.PdfReader(file_obj)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            result = "\n".join(text)
            print(f"[INFO] PDF 解析成功，提取 {len(text)} 页")
            return result
        except Exception as exc:
            print(f"[ERROR] PDF 解析失败: {exc}")
            raise

    @staticmethod
    def parse_txt(file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as file_obj:
                result = file_obj.read()
            print(f"[INFO] TXT 解析成功，文本长度 {len(result)}")
            return result
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="gbk") as file_obj:
                    result = file_obj.read()
                print(f"[INFO] TXT 解析成功 (GBK 编码)，文本长度 {len(result)}")
                return result
            except Exception as exc:
                print(f"[ERROR] TXT 解析失败: {exc}")
                raise
        except Exception as exc:
            print(f"[ERROR] TXT 解析失败: {exc}")
            raise

    @staticmethod
    def _normalize_cell(value) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    @classmethod
    def _build_excel_headers(cls, row) -> List[str]:
        headers: List[str] = []
        for idx, cell in enumerate(row):
            text = cls._normalize_cell(cell)
            if not text:
                text = f"列{idx + 1}"
            headers.append(text)
        return headers if headers else ["列1"]

    @classmethod
    def _format_excel_row(cls, row, headers: List[str]) -> Optional[str]:
        if not row:
            return None

        cells = []
        for idx, cell in enumerate(row):
            cell_text = cls._normalize_cell(cell)
            if not cell_text:
                continue
            header_name = headers[idx] if idx < len(headers) else f"列{idx + 1}"
            cells.append(f"{header_name}: {cell_text}")

        if not cells:
            return None
        return " | ".join(cells)

    @classmethod
    def _is_header_like_row(cls, headers: List[str], row) -> bool:
        total = 0
        matches = 0
        for idx, cell in enumerate(row):
            cell_text = cls._normalize_cell(cell)
            if not cell_text:
                continue
            total += 1
            header_name = headers[idx] if idx < len(headers) else f"列{idx + 1}"
            if cell_text == header_name:
                matches += 1
        return total > 0 and matches / total >= 0.8

    @classmethod
    def parse_excel(cls, file_path: str) -> str:
        """解析 Excel，过滤空单元并保留列名称"""
        text: List[str] = []
        workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet_names = workbook.sheetnames
        print(f"[INFO] Excel 包含 {len(sheet_names)} 个 sheet: {', '.join(sheet_names)}")

        try:
            for sheet_name in sheet_names:
                sheet = workbook[sheet_name]
                text.append(f"Sheet: {sheet_name}")
                headers: List[str] = []
                header_row = None
                total_rows = 0
                effective_rows = 0
                empty_rows_after_data = 0

                for row in sheet.iter_rows(values_only=True):
                    total_rows += 1

                    if not headers:
                        if not any(cls._normalize_cell(cell) for cell in row):
                            continue
                        headers = cls._build_excel_headers(row)
                        header_row = row
                        text.append("Columns: " + " | ".join(headers))
                        row_text = cls._format_excel_row(row, headers)
                        if row_text and not cls._is_header_like_row(headers, row):
                            effective_rows += 1
                            text.append(row_text)
                        continue

                    row_text = cls._format_excel_row(row, headers)
                    if row_text:
                        effective_rows += 1
                        text.append(row_text)
                        empty_rows_after_data = 0
                    else:
                        empty_rows_after_data += 1
                        if empty_rows_after_data >= cls.MAX_CONSECUTIVE_EMPTY_ROWS:
                            print(
                                f"[INFO] 工作表 '{sheet_name}' 连续空行超过 {cls.MAX_CONSECUTIVE_EMPTY_ROWS}，提前结束扫描"
                            )
                            break

                if effective_rows == 0 and header_row:
                    row_text = cls._format_excel_row(header_row, headers)
                    if row_text:
                        text.append(row_text)
                        effective_rows = 1

                print(
                    f"[INFO] 工作表 '{sheet_name}' 解析完成，提取 {effective_rows} 行（总行数 {total_rows}）"
                )
        finally:
            workbook.close()

        return "\n".join(text)

    @classmethod
    def parse(cls, file_path: str, file_type: str) -> Optional[str]:
        parsers = {
            "docx": cls.parse_docx,
            "pdf": cls.parse_pdf,
            "txt": cls.parse_txt,
            "xls": cls.parse_excel,
            "xlsx": cls.parse_excel,
        }

        parser = parsers.get(file_type.lower())
        if parser:
            return parser(file_path)
        return None

    @staticmethod
    def evaluate_quality(text: str) -> Dict[str, float]:
        """返回文本质量指标，用于校验"""
        lines = text.splitlines()
        total_lines = len(lines)
        non_empty_lines = sum(1 for line in lines if line.strip())
        non_empty_ratio = (non_empty_lines / total_lines) if total_lines else 0.0
        meaningful_chars = sum(1 for ch in text if not ch.isspace())
        return {
            "total_lines": total_lines,
            "non_empty_lines": non_empty_lines,
            "non_empty_ratio": non_empty_ratio,
            "meaningful_chars": meaningful_chars,
        }

import os
from typing import Optional
from docx import Document
import PyPDF2
import openpyxl


class DocumentParser:
    """文档解析服务"""
    
    @staticmethod
    def parse_docx(file_path: str) -> str:
        """解析 DOCX 文件"""
        try:
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            result = "\n".join(text)
            print(f"[INFO] DOCX 解析成功，提取 {len(text)} 个段落")
            return result
        except Exception as e:
            print(f"[ERROR] DOCX 解析失败: {str(e)}")
            raise
    
    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """解析 PDF 文件"""
        try:
            text = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            result = "\n".join(text)
            print(f"[INFO] PDF 解析成功，提取 {len(text)} 页")
            return result
        except Exception as e:
            print(f"[ERROR] PDF 解析失败: {str(e)}")
            raise
    
    @staticmethod
    def parse_txt(file_path: str) -> str:
        """解析 TXT 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                result = file.read()
            print(f"[INFO] TXT 解析成功，文本长度: {len(result)}")
            return result
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    result = file.read()
                print(f"[INFO] TXT 解析成功 (GBK编码)，文本长度: {len(result)}")
                return result
            except Exception as e:
                print(f"[ERROR] TXT 解析失败: {str(e)}")
                raise
        except Exception as e:
            print(f"[ERROR] TXT 解析失败: {str(e)}")
            raise
    
    @staticmethod
    def parse_excel(file_path: str) -> str:
        """解析 Excel 文件"""
        workbook = openpyxl.load_workbook(file_path)
        text = []
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            text.append(f"Sheet: {sheet_name}")
            for row in sheet.iter_rows(values_only=True):
                row_text = "\t".join([str(cell) if cell is not None else "" for cell in row])
                if row_text.strip():
                    text.append(row_text)
        return "\n".join(text)
    
    @classmethod
    def parse(cls, file_path: str, file_type: str) -> Optional[str]:
        """根据文件类型解析文档"""
        parsers = {
            'docx': cls.parse_docx,
            'pdf': cls.parse_pdf,
            'txt': cls.parse_txt,
            'xls': cls.parse_excel,
            'xlsx': cls.parse_excel,
        }
        
        parser = parsers.get(file_type.lower())
        if parser:
            return parser(file_path)
        return None


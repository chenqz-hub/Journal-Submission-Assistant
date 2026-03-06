import re
import os
import logging
from docx import Document

logger = logging.getLogger(__name__)

class DocumentSplitter:
    """
    V2.0 核心模块：学术文档语义解构引擎。
    负责将一篇包含所有内容的“大杂烩”论文稿件，根据标题、格式和正则表达式，
    智能拆分为 Title Page、Abstract、Main Text、Figure Legends、Tables 等结构化区块。
    """
    
    def __init__(self):
        # 定义文献常见独立章节的正则表达式（忽略大小写）
        self.section_patterns = {
            "abstract": re.compile(r"^(abstract|summary)$", re.IGNORECASE),
            "introduction": re.compile(r"^(1\.?\s*)?(introduction|background)$", re.IGNORECASE),
            "acknowledgements": re.compile(r"^(acknowledgements|acknowledgments)$", re.IGNORECASE),
            "declarations": re.compile(r"^(declarations|conflict of interest|funding|data availability|author contributions)$", re.IGNORECASE),
            "references": re.compile(r"^(references|bibliography)$", re.IGNORECASE),
            "figure_legends": re.compile(r"^(figure legends|figure captions)$", re.IGNORECASE),
            "tables_text": re.compile(r"^(tables|tables? legends?)$", re.IGNORECASE),
        }
        
        # 匹配分散在正文的单个图表标题 (如 "Fig. 1...", "Table 1:") 
        self.single_fig_pattern = re.compile(r"^(figure|fig\.?)\s*\d+[:\.]?", re.IGNORECASE)
        self.single_table_pattern = re.compile(r"^table\s*\d+[:\.]?", re.IGNORECASE)

    def parse(self, file_path: str) -> dict:
        """主入口：根据文件类型决定解析方式"""
        ext = file_path.lower().split('.')[-1]
        sections = {
            "title_page": [],       # 包含标题、作者、单位等（Abstract 之前的内容）
            "abstract": [],         # 摘要与关键词
            "main_text": [],        # 正文（引言至结论）
            "acknowledgements": [], # 致谢（可能需要盲审剔除）
            "declarations": [],     # 声明（利益冲突、资金等）
            "references": [],       # 参考文献
            "figure_legends": [],   # 图注
            "tables_text": [],      # 以文本出现的表格说明
            "tables_obj": []        # 真实的 Word Table 对象
        }
        
        if ext in ['md', 'txt']:
            return self._parse_text(file_path, sections)
        else:
            return self._parse_docx(file_path, sections)

    def _is_heading(self, text: str) -> str:
        """判断当前行是否是进入某个特定结构的章节标题"""
        # 兼容 Markdown 语法，过滤掉标题前的 '#' 或 '*' 等符号
        text_clean = text.lstrip('#* \t').strip()
        # 标题通常较短（比如小于100个字符）
        if text_clean and len(text_clean) < 100:
            for key, pattern in self.section_patterns.items():
                if pattern.match(text_clean):
                    return key
        return None

    def _parse_docx(self, file_path: str, sections: dict) -> dict:
        try:
            doc = Document(file_path)
        except Exception as e:
            logger.error(f'Failed to read DOCX for splitting: {e}')
            raise ValueError(f'无法读取 Word 文件: {str(e)}')

        current_section = 'title_page'

        from services.docx_utils import iter_block_items
        from docx.text.paragraph import Paragraph
        from docx.table import Table

        pending_table_title = []
        last_table_group = None

        for block in iter_block_items(doc):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if not text:
                    continue

                para_data = {
                    'text': text,
                    'style': block.style.name if block.style else None,
                    'runs': []
                }
                for run in block.runs:
                    if not run.text:
                        continue
                    para_data['runs'].append({
                        'text': run.text,
                        'bold': run.bold,
                        'italic': run.italic,
                        'underline': run.underline
                    })

                if self.single_table_pattern.match(text):
                    pending_table_title.append(para_data)
                    continue

                if self.single_fig_pattern.match(text) and len(text) > 10:
                    if current_section != 'figure_legends':
                        sections['figure_legends'].append(para_data)
                        continue

                heading_type = self._is_heading(text)

                if heading_type:
                    if heading_type == 'introduction':
                        current_section = 'main_text'
                    else:
                        current_section = heading_type

                if last_table_group is not None and not heading_type:
                    if text.lower().startswith('note') or text.startswith('*') or len(text)<150 or text.lower().startswith('abbreviation'):
                        last_table_group['footnotes'].append(para_data)
                        continue
                    else:
                        last_table_group = None

                sections[current_section].append(para_data)

            elif isinstance(block, Table):
                tbl_group = {
                    'title': pending_table_title,
                    'table': block,
                    'footnotes': []
                }
                sections['tables_obj'].append(tbl_group)
                pending_table_title = []
                last_table_group = tbl_group
                
        return sections

    def _parse_text(self, file_path: str, sections: dict) -> dict:
        """处理 Markdown 或 txt 的备用逻辑，增加对 MD 表格的支持"""
        import re

        class MockCell:
            def __init__(self, text):
                self.text = text
            @property
            def paragraphs(self):
                return []
        
        class MockRow:
            def __init__(self, cells):
                self.cells = [MockCell(c) for c in cells]
                
        class MockTable:
            def __init__(self, rows):
                self.rows = [MockRow(r) for r in rows]
                self.columns = self.rows[0].cells if self.rows else []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            raise ValueError(f"无法读取文本文件: {str(e)}")

        current_section = "title_page"
        current_table_rows = []
        pending_table_title = []
        
        for line in lines:
            text = line.strip()
            
            if text.startswith('|') and text.endswith('|'):
                cells = [c.strip() for c in text.split('|')[1:-1]]
                if all(re.match(r'^[-:\s]+$', c) for c in cells if c):
                    continue
                current_table_rows.append(cells)
                continue
                
            if current_table_rows:
                sections["tables_obj"].append({
                    "title": pending_table_title,
                    "table": MockTable(current_table_rows),
                    "footnotes": []
                })
                current_table_rows = []
                pending_table_title = []
                
            if not text:
                continue

            if self.single_fig_pattern.match(text) and len(text) > 10:
                if current_section != 'figure_legends':
                    sections["figure_legends"].append(text)
                    continue

            if self.single_table_pattern.match(text) and len(text) < 200:
                pending_table_title.append(text)
                sections[current_section].append(text)
                continue

            heading_type = self._is_heading(text)
            if heading_type:
                if heading_type == "introduction":
                    current_section = "main_text"
                else:
                    current_section = heading_type

            sections[current_section].append(text)

        if current_table_rows:
            sections["tables_obj"].append({
                "title": pending_table_title,
                "table": MockTable(current_table_rows),
                "footnotes": []
            })
            
        return sections

# 用于测试运行
if __name__ == "__main__":
    pass

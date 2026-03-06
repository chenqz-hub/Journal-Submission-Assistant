import os
import logging
from docx import Document
from services.document_splitter import DocumentSplitter

logger = logging.getLogger(__name__)

class DocumentMerger:
    """
    负责处理用户上传的多个稿件文件（如前一次投稿被拒后的单独文件：Title_Page.docx, Manuscript.docx, Figures.docx）
    通过文件名以及内容特征，将它们合并并解析成统一的 sections 字典格式，
    以便重新传送给 DocumentBuilder 进行新期刊的靶向排版。
    """
    
    def __init__(self):
        self.splitter = DocumentSplitter()
        self.sections = {
            "title_page": [],       
            "abstract": [],         
            "main_text": [],        
            "acknowledgements": [], 
            "declarations": [],     
            "references": [],       
            "figure_legends": [],   
            "tables_text": [],      
            "tables_obj": []        
        }

    def guess_initial_section(self, filename: str) -> str:
        """根据文件名推测该文件最可能属于哪个 section"""
        lower_name = filename.lower()
        if "title" in lower_name:
            return "title_page"
        if "abstract" in lower_name:
            return "abstract"
        if "figure" in lower_name or "fig" in lower_name or "caption" in lower_name:
            return "figure_legends"
        if "table" in lower_name:
            return "tables_obj" # 表格文件单独处理可能更好
        if "declarations" in lower_name or "conflict" in lower_name:
            return "declarations"
        if "ack" in lower_name:
            return "acknowledgements"
        if "ref" in lower_name:
            return "references"
        
        # 默认作为正文处理
        return "main_text"

    def merge_files(self, temp_file_paths: list) -> dict:
        """
        遍历处理每个文件，将内容洗入统一的 sections。
        """
        for filepath in temp_file_paths:
            filename = os.path.basename(filepath)
            initial_guess = self.guess_initial_section(filename)
            logger.info(f"Merging file: {filename}, guessed initial section: {initial_guess}")
            
            ext = filename.lower().split('.')[-1]
            if ext in ['md', 'txt']:
                self._merge_text(filepath, initial_guess)
            elif ext in ['docx', 'doc']:
                self._merge_docx(filepath, initial_guess)
            else:
                logger.warning(f"Unsupported file format for merging: {filename}")
                
        return self.sections

    def _merge_docx(self, file_path, current_section):
        try:
            doc = Document(file_path)
        except Exception as e:
            logger.error(f'Failed to read DOCX for merging: {e}')
            return

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

                # Check if it's explicitly a table title
                if self.splitter.single_table_pattern.match(text):
                    pending_table_title.append(para_data)
                    continue

                # If we are parsing a tables-only document, distribute text around tables
                if current_section == 'tables_obj':
                    if not last_table_group:
                        pending_table_title.append(para_data)
                    else:
                        last_table_group['footnotes'].append(para_data)
                    continue

                heading_type = self.splitter._is_heading(text)
                if heading_type:
                    if heading_type == 'introduction':
                        current_section = 'main_text'
                    else:
                        current_section = heading_type

                if self.splitter.single_fig_pattern.match(text) and len(text) > 10:
                    self.sections['figure_legends'].append(para_data)
                    if current_section == 'main_text':
                        continue

                # Table footnotes heuristic (if we just saw a table and text is short or note-like)
                if last_table_group is not None and not heading_type:
                    if text.lower().startswith('note') or text.startswith('*') or len(text)<150 or text.lower().startswith('abbreviation'):
                        last_table_group['footnotes'].append(para_data)
                        continue
                    else:
                        last_table_group = None

                self.sections[current_section].append(para_data)
            
            elif isinstance(block, Table):
                tbl_group = {
                    'title': pending_table_title,
                    'table': block,
                    'footnotes': []
                }
                self.sections['tables_obj'].append(tbl_group)
                pending_table_title = []
                last_table_group = tbl_group

    def _merge_text(self, file_path, current_section):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"Failed to read text file for merging: {e}")
            return
            
        for line in lines:
            text = line.strip()
            if not text: 
                continue
                
            heading_type = self.splitter._is_heading(text)
            if heading_type:
                if heading_type == "introduction":
                    current_section = "main_text"
                else:
                    current_section = heading_type
            
            if self.splitter.single_fig_pattern.match(text) and len(text) > 10:
                self.sections["figure_legends"].append(text)
                continue
                
            self.sections[current_section].append(text)

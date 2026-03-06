import io
import os
import logging
from PIL import Image
from docx import Document

logger = logging.getLogger(__name__)

class ImageChecker:
    @staticmethod
    def check_dpi(docx_paths: list) -> list:
        """
        批量检查文档中所有的图片 DPI，找出低于 300 DPI 的图片。
        """
        warnings = []
        for path in docx_paths:
            if not path.endswith('.docx') and not path.endswith('.doc'):
                continue
            if not os.path.exists(path):
                continue
                
            try:
                doc = Document(path)
                doc_name = os.path.basename(path)
                
                # 遍历文档关联的部分寻找图片
                for rel in doc.part.rels.values():
                    if "image" in rel.reltype:
                        image_part = rel.target_part
                        img_data = image_part.blob
                        try:
                            img = Image.open(io.BytesIO(img_data))
                            
                            # 获取图片 DPI 元数据
                            dpi = img.info.get('dpi')
                            dpi_val = 0
                            
                            if dpi:
                                dpi_val = min(dpi[0], dpi[1]) # 取长宽中较小的 DPI
                            
                            width, height = img.size
                            
                            status = "ok"
                            if not dpi:
                                status = "missing"
                                dpi_val = 96 # 一般屏幕默认
                            elif dpi_val < 300:
                                status = "low"
                                
                            if status in ["low", "missing"]:
                                warnings.append({
                                    "document": doc_name,
                                    "image_name": os.path.basename(image_part.partname),
                                    "dpi": int(dpi_val) if dpi else "未配置/缺失(默认96)",
                                    "dimensions": f"{width}x{height}",
                                    "issue": "DPI 低于 300" if status == "low" else "缺失 DPI 属性(可能为截屏)",
                                    "suggestion": "期刊通常要求 Figure 分辨率在 300 DPI 以上，建议使用原始高保真图片替换。"
                                })
                        except Exception as e:
                            logger.error(f"Error reading image in {doc_name}: {e}")
            except Exception as e:
                logger.error(f"Failed to check DPI for document {path}: {str(e)}")
                
        return warnings

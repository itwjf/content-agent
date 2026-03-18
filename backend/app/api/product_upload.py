"""
商品文档上传模块
用于上传产品文档并添加到向量数据库中
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.services.rag_service import rag_service
import os
import tempfile
import fitz  # PyMuPDF for PDF
import docx  # python-docx for DOCX

router = APIRouter()

# 临时存储目录
UPLOAD_DIR = tempfile.gettempdir()


def parse_file(file_path: str, file_type: str) -> str:
    """
    解析不同格式的文件，返回文本内容
    
    Args:
        file_path: 文件路径
        file_type: 文件类型
    
    Returns:
        解析后的文本内容
    """
    try:
        if file_type in ["txt", "md"]:
            # 文本文件
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif file_type == "pdf":
            # PDF文件
            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        elif file_type == "docx":
            # DOCX文件
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
    except Exception as e:
        raise Exception(f"文件解析失败: {str(e)}")


@router.post("/upload")
async def upload_product_document(
    file: UploadFile = File(...)
):
    """
    上传产品文档并添加到向量数据库
    
    Args:
        file: 上传的文件
    
    Returns:
        上传结果
    """
    try:
        # 获取文件类型
        file_ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
        if file_ext not in ["txt", "md", "pdf", "doc", "docx"]:
            raise HTTPException(status_code=400, detail="不支持的文件类型，仅支持 txt、md、pdf、doc、docx")
        
        # 保存文件到临时目录
        file_path = os.path.join(UPLOAD_DIR, f"{file.filename}")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 解析文件
        text = parse_file(file_path, file_ext)
        
        # 添加到向量数据库
        result = rag_service.add_document(
            collection_name="products",
            text=text,
            metadata={"type": "product_document", "filename": file.filename}
        )
        
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "status": "success",
            "message": "文件上传成功并添加到知识库",
            "filename": file.filename,
            "chunks_count": result.get("chunks_count", 0),
            "storage": result.get("storage", "unknown")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

"""
RAG 知识库 API
"""
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.rag_service import rag_service

router = APIRouter()


# ==================== 请求/响应模型 ====================

class AddDocumentRequest(BaseModel):
    """添加文档请求"""
    collection: str
    text: str
    metadata: Dict = {}


class SearchRequest(BaseModel):
    """搜索请求"""
    collection: str
    query: str
    top_k: int = 3


class CollectionInfo(BaseModel):
    """集合信息"""
    name: str
    chunks_count: int
    total_chars: int


# ==================== 路由 ====================

@router.get("/rag/collections")
async def get_collections():
    """获取所有知识库集合"""
    collections = rag_service.get_collections()
    return {"collections": collections}


@router.get("/rag/collections/{collection_name}")
async def get_collection_info(collection_name: str):
    """获取集合详情"""
    info = rag_service.get_collection_info(collection_name)
    return info


@router.post("/rag/documents")
async def add_document(request: AddDocumentRequest):
    """添加文档到知识库"""
    try:
        result = rag_service.add_document(
            collection_name=request.collection,
            text=request.text,
            metadata=request.metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/search")
async def search(request: SearchRequest):
    """语义搜索"""
    try:
        results = rag_service.search(
            collection_name=request.collection,
            query=request.query,
            top_k=request.top_k
        )
        return {
            "query": request.query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rag/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """删除知识库集合"""
    success = rag_service.delete_collection(collection_name)
    if success:
        return {"message": f"Collection {collection_name} deleted"}
    raise HTTPException(status_code=404, detail="Collection not found")

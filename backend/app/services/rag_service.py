"""
RAG 知识库服务 - 接入真正的 Qdrant
功能：文档管理、文本分块、向量化存储、语义搜索
"""

from typing import List, Dict, Optional
import json
import requests
from app.core.config import get_settings

settings = get_settings()

# 尝试导入 Qdrant client
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
    print("[RAG] Qdrant client 导入成功")
except ImportError:
    QDRANT_AVAILABLE = False
    print("[RAG] Qdrant client 未安装，使用内存存储")


class RAGService:
    """
    RAG 知识库服务类

    功能：
    1. add_document: 添加文档到知识库
       - 文本分块
       - 调用 SiliconFlow embedding API 生成向量
       - 存入 Qdrant 向量数据库

    2. search: 语义搜索
       - 把查询转为向量
       - 在 Qdrant 中搜索相似向量
       - 返回结果
    """

    # 文本分块配置
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    # 向量维度（BAAI/bge-large-zh-v1.5 输出 1024 维）
    VECTOR_SIZE = 1024

    def __init__(self):
        """初始化服务"""
        # 初始化 Qdrant 客户端
        self.qdrant_client = None
        self.use_qdrant = False

        if QDRANT_AVAILABLE:
            try:
                # 连接到 Qdrant（本地或云端）
                qdrant_host = settings.qdrant_host
                qdrant_port = settings.qdrant_port

                # 尝试连接
                self.qdrant_client = QdrantClient(
                    host=qdrant_host,
                    port=qdrant_port
                )

                # 测试连接
                collections = self.qdrant_client.get_collections()
                print(f"[RAG] Qdrant 连接成功，共 {len(collections.collections)} 个集合")

                self.use_qdrant = True
            except Exception as e:
                print(f"[RAG] Qdrant 连接失败: {e}，使用内存存储")
                self.use_qdrant = False
        else:
            print("[RAG] Qdrant 未安装，使用内存存储")

        # 内存存储（备用或开发测试用）
        self.vector_store = {}

        print("[RAG] 知识库服务初始化完成")

    def add_document(
        self,
        collection_name: str,
        text: str,
        metadata: Dict = None
    ) -> Dict:
        """
        添加文档到知识库
        """
        # Step 1: 文本分块
        chunks = self._chunk_text(text)
        print(f"[RAG] 文档分块完成，共 {len(chunks)} 个chunk")

        # Step 2: 为每个chunk生成向量并存储
        points = []
        for i, chunk in enumerate(chunks):
            chunk_id = len(self.vector_store.get(collection_name, [])) + i

            # 调用 embedding API 生成向量
            vector = self._get_embedding(chunk)
            print(f"[RAG] chunk {i+1} 向量化完成，向量维度: {len(vector)}")

            # 构建点数据
            if self.use_qdrant:
                points.append(PointStruct(
                    id=chunk_id,
                    vector=vector,
                    payload={
                        "text": chunk,
                        "metadata": metadata or {}
                    }
                ))
            else:
                # 内存存储
                if collection_name not in self.vector_store:
                    self.vector_store[collection_name] = []

                self.vector_store[collection_name].append({
                    "id": chunk_id,
                    "text": chunk,
                    "vector": vector,
                    "metadata": metadata or {}
                })

        # Step 3: 存储到 Qdrant 或内存
        if self.use_qdrant:
            try:
                # 确保 collection 存在
                self._ensure_collection(collection_name)

                # 批量插入
                self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                print(f"[RAG] 已存入 Qdrant，{len(points)} 个向量")
            except Exception as e:
                print(f"[RAG] Qdrant 存储失败: {e}，存入内存")
                # 存入内存
                if collection_name not in self.vector_store:
                    self.vector_store[collection_name] = []
                for pt in points:
                    self.vector_store[collection_name].append({
                        "id": pt.id,
                        "text": pt.payload["text"],
                        "vector": pt.vector,
                        "metadata": pt.payload["metadata"]
                    })

        return {
            "collection": collection_name,
            "chunks_count": len(chunks),
            "storage": "qdrant" if self.use_qdrant else "memory",
            "status": "success"
        }

    def _ensure_collection(self, collection_name: str):
        """确保 collection 存在，不存在则创建"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if collection_name not in collection_names:
                # 创建 collection
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )
                print(f"[RAG] 创建 Qdrant collection: {collection_name}")
        except Exception as e:
            print(f"[RAG] 检查/创建 collection 失败: {e}")

    def _get_embedding(self, text: str) -> List[float]:
        """
        调用 SiliconFlow Embedding API 将文本转为向量
        """
        try:
            # 从环境变量读取 API Key
            api_key = getattr(settings, 'siliconflow_api_key', None)

            if not api_key:
                print("[RAG] 警告: 未设置 SILICONFLOW_API_KEY，使用备用方案")
                return self._fallback_embedding(text)

            response = requests.post(
                "https://api.siliconflow.cn/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "BAAI/bge-large-zh-v1.5",
                    "input": text
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                embedding = result["data"][0]["embedding"]
                return embedding
            else:
                print(f"[RAG] SiliconFlow embedding 失败: {response.status_code}")
                return self._fallback_embedding(text)

        except Exception as e:
            print(f"[RAG] Embedding API 调用失败: {e}")
            return self._fallback_embedding(text)

    def _fallback_embedding(self, text: str) -> List[float]:
        """备用 embedding 方案"""
        import hashlib

        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()

        vector = []
        for i in range(0, len(hash_hex), 2):
            try:
                vector.append(int(hash_hex[i:i+2], 16) / 255.0)
            except:
                vector.append(0.5)

        while len(vector) < self.VECTOR_SIZE:
            vector.extend(vector[:min(self.VECTOR_SIZE - len(vector), len(vector))])

        return vector[:self.VECTOR_SIZE]

    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 3
    ) -> List[Dict]:
        """
        语义搜索
        """
        # Step 1: 把查询转为向量
        query_vector = self._get_embedding(query)
        print(f"[RAG] 查询向量化完成")

        results = []

        if self.use_qdrant:
            try:
                # 在 Qdrant 中搜索
                search_results = self.qdrant_client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=top_k
                )

                for result in search_results:
                    results.append({
                        "text": result.payload.get("text", ""),
                        "score": result.score,
                        "metadata": result.payload.get("metadata", {})
                    })
                print(f"[RAG] Qdrant 搜索完成，返回 {len(results)} 条结果")
            except Exception as e:
                print(f"[RAG] Qdrant 搜索失败: {e}，使用内存搜索")
                results = self._search_memory(collection_name, query_vector, top_k)
        else:
            # 使用内存搜索
            results = self._search_memory(collection_name, query_vector, top_k)

        return results

    def _search_memory(self, collection_name: str, query_vector: List[float], top_k: int) -> List[Dict]:
        """内存搜索"""
        if collection_name not in self.vector_store:
            return []

        chunks = self.vector_store[collection_name]
        results = []

        for chunk in chunks:
            similarity = self._cosine_similarity(query_vector, chunk["vector"])
            results.append({
                "text": chunk["text"],
                "score": similarity,
                "metadata": chunk.get("metadata", {})
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _chunk_text(self, text: str) -> List[str]:
        """文本分块"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.CHUNK_SIZE
            chunk = text[start:end]

            if end < len(text):
                for sep in ['。', '！', '？', '，', '\n']:
                    last_sep = chunk.rfind(sep)
                    if last_sep > self.CHUNK_SIZE // 2:
                        end = start + last_sep + 1
                        chunk = text[start:end]
                        break

            if chunk.strip():
                chunks.append(chunk.strip())

            start = end - self.CHUNK_OVERLAP

        return chunks

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def get_collections(self) -> List[str]:
        """获取所有集合名称"""
        if self.use_qdrant:
            try:
                collections = self.qdrant_client.get_collections()
                return [c.name for c in collections.collections]
            except:
                pass
        return list(self.vector_store.keys())

    def get_collection_info(self, collection_name: str) -> Dict:
        """获取集合信息"""
        if self.use_qdrant:
            try:
                info = self.qdrant_client.get_collection(collection_name)
                return {
                    "name": collection_name,
                    "vectors_count": info.vectors_count,
                    "points_count": info.points_count,
                    "status": "qdrant"
                }
            except:
                pass

        if collection_name not in self.vector_store:
            return {"error": "Collection not found"}

        chunks = self.vector_store[collection_name]
        return {
            "name": collection_name,
            "chunks_count": len(chunks),
            "total_chars": sum(len(c["text"]) for c in chunks),
            "status": "memory"
        }

    def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        if self.use_qdrant:
            try:
                self.qdrant_client.delete_collection(collection_name)
                return True
            except:
                pass

        if collection_name in self.vector_store:
            del self.vector_store[collection_name]
            return True
        return False


# 创建服务实例
rag_service = RAGService()


def init_knowledge_base():
    """初始化预设知识库"""
    # 商品知识
    product_knowledge = """
    控油修护精华液产品介绍：
    - 产品名称：控油修护精华液
    - 规格：30ml
    - 价格：350元
    - 成分：水杨酸、烟酰胺、 透明质酸
    - 功效：控油、修护、保湿
    - 适用人群：油性皮肤、混合性皮肤
    - 使用方法：早晚洁面后，取适量精华液涂抹于面部，轻拍至吸收
    - 注意事项：敏感肌初次使用建议先在耳后测试

    常见问题：
    Q: 油皮能用吗？A: 这款精华专门针对油皮设计，水杨酸成分可以深层清洁毛孔、控油。
    Q: 敏感肌能用吗？A: 建议先测试，成分温和，但个体差异存在。
    Q: 和其他精华叠加使用？A: 可以搭配保湿精华使用，先用控油精华再用保湿产品。
    """

    rag_service.add_document(
        collection_name="products",
        text=product_knowledge,
        metadata={"type": "product", "sku": "12345"}
    )

    # 直播话术知识
    live_script_knowledge = """
    直播话术模板：

    开场话术：
    - "欢迎各位宝宝们来到直播间！"
    - "感谢大家的支持，点击关注不迷路！"

    产品介绍话术：
    - "今天给大家介绍我们家的爆款产品..."
    - "这个产品真的非常好用，我自己也一直在用"

    促单话术：
    - "今天直播间专属优惠，只剩最后XX单！"
    - "家人们赶紧下单，优惠名额有限！"
    - "3-2-1，开始秒杀！"

    互动话术：
    - "有任何问题随时问我哦"
    - "宝宝们扣1告诉我你们想要什么优惠"
    """

    rag_service.add_document(
        collection_name="live_scripts",
        text=live_script_knowledge,
        metadata={"type": "script"}
    )

    print("[RAG] 预设知识库初始化完成")


# 初始化
init_knowledge_base()

"""
RAG 知识库服务
功能：文档管理、文本分块、向量化存储、语义搜索

注意：
- 本模块使用 DeepSeek 的 embedding API 将文本转为向量
- 向量存储使用 Qdrant 向量数据库
"""

from typing import List, Dict, Optional
import json
import requests
from app.core.config import get_settings

settings = get_settings()


class RAGService:
    """
    RAG 知识库服务类

    主要功能：
    1. add_document: 添加文档到知识库
       - 文本分块（chunking）
       - 调用 embedding API 生成向量
       - 存入 Qdrant

    2. search: 语义搜索
       - 把查询转为向量
       - 在 Qdrant 中搜索相似向量
       - 返回结果
    """

    # 文本分块配置
    CHUNK_SIZE = 500  # 每个chunk的字符数
    CHUNK_OVERLAP = 50  # 重叠字符数

    def __init__(self):
        """初始化服务"""
        # Qdrant 配置（如果使用 Qdrant）
        # self.qdrant_url = "http://localhost:6333"

        # 模拟向量存储（开发测试用，生产环境应使用 Qdrant）
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

        参数:
            collection_name: 集合名称（类似文件夹/表名）
            text: 文档内容
            metadata: 元数据（如商品ID、类型等）

        流程:
            1. 文本分块
            2. 对每个chunk调用embedding API生成向量
            3. 存储到向量数据库

        返回:
            添加结果
        """
        # Step 1: 文本分块
        chunks = self._chunk_text(text)
        print(f"[RAG] 文档分块完成，共 {len(chunks)} 个chunk")

        # Step 2: 为每个chunk生成向量并存储
        chunks_with_vectors = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{collection_name}_{i}_{len(self.vector_store)}"

            # 调用 embedding API 生成向量
            vector = self._get_embedding(chunk)
            print(f"[RAG] chunk {i+1} 向量化完成，向量维度: {len(vector)}")

            chunks_with_vectors.append({
                "id": chunk_id,
                "text": chunk,
                "vector": vector,
                "metadata": metadata or {}
            })

        # Step 3: 存储
        if collection_name not in self.vector_store:
            self.vector_store[collection_name] = []

        self.vector_store[collection_name].extend(chunks_with_vectors)

        return {
            "collection": collection_name,
            "chunks_count": len(chunks),
            "status": "success"
        }

    def _get_embedding(self, text: str) -> List[float]:
        """
        调用 Embedding API 将文本转为向量

        这是核心函数！负责把文字转成数字向量。

        参数:
            text: 输入文本

        返回:
            向量列表（浮点数列表）
        """
        try:
            # 方法1: 使用 DeepSeek Embedding API
            # 注意：需要 DeepSeek API 支持 embedding 模型
            response = requests.post(
                "https://api.deepseek.com/embeddings",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-embeddings",
                    "input": text
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                # DeepSeek 返回格式: {"data": [{"embedding": [...]}]}
                embedding = result["data"][0]["embedding"]
                return embedding
            else:
                print(f"[RAG] DeepSeek embedding 失败: {response.status_code}, 使用备用方案")
                return self._fallback_embedding(text)

        except Exception as e:
            print(f"[RAG] Embedding API 调用失败: {e}，使用备用方案")
            return self._fallback_embedding(text)

    def _fallback_embedding(self, text: str) -> List[float]:
        """
        备用 embedding 方案
        当 API 调用失败时使用，仅用于开发测试
        生产环境应该使用真正的 embedding
        """
        import hashlib

        # 用文本的 MD5 hash 生成伪向量
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()

        # 转换为 0-1 之间的浮点数
        vector = []
        for i in range(0, len(hash_hex), 2):
            try:
                vector.append(int(hash_hex[i:i+2], 16) / 255.0)
            except:
                vector.append(0.5)

        # 填充到固定长度 1536（与 OpenAI embedding 相同）
        while len(vector) < 1536:
            vector.extend(vector[:min(1536 - len(vector), len(vector))])

        return vector[:1536]

    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 3
    ) -> List[Dict]:
        """
        语义搜索

        参数:
            collection_name: 集合名称
            query: 查询内容
            top_k: 返回前k个结果

        流程:
            1. 把查询转为向量（调用 embedding API）
            2. 计算与库中向量的相似度
            3. 返回最相似的top_k个结果

        返回:
            搜索结果列表
        """
        if collection_name not in self.vector_store:
            return []

        # Step 1: 把查询转为向量
        query_vector = self._get_embedding(query)
        print(f"[RAG] 查询向量化完成")

        # Step 2: 计算相似度
        chunks = self.vector_store[collection_name]
        results = []

        for chunk in chunks:
            similarity = self._cosine_similarity(query_vector, chunk["vector"])
            results.append({
                "text": chunk["text"],
                "score": similarity,
                "metadata": chunk.get("metadata", {})
            })

        # Step 3: 排序返回 top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _chunk_text(self, text: str) -> List[str]:
        """
        文本分块

        把长文本分割成较小的 chunk，方便向量化和检索。

        参数:
            text: 原始文本

        返回:
            chunk 列表
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.CHUNK_SIZE
            chunk = text[start:end]

            # 尽量在句子边界分割（更符合语义）
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
        """
        计算余弦相似度

        向量相似度计算方法之一，值越接近1越相似。

        参数:
            vec1, vec2: 两个向量

        返回:
            相似度分数 (0-1)
        """
        # 点积
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # 向量长度
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def get_collections(self) -> List[str]:
        """获取所有集合名称"""
        return list(self.vector_store.keys())

    def get_collection_info(self, collection_name: str) -> Dict:
        """获取集合信息"""
        if collection_name not in self.vector_store:
            return {"error": "Collection not found"}

        chunks = self.vector_store[collection_name]
        return {
            "name": collection_name,
            "chunks_count": len(chunks),
            "total_chars": sum(len(c["text"]) for c in chunks)
        }

    def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        if collection_name in self.vector_store:
            del self.vector_store[collection_name]
            return True
        return False


# 创建服务实例
rag_service = RAGService()


def init_knowledge_base():
    """
    初始化预设知识库

    添加一些示例文档到知识库中，用于演示和测试。
    """
    # 商品知识
    product_knowledge = """
    控油修护精华液产品介绍：
    - 产品名称：控油修护精华液
    - 规格：30ml
    - 价格：350元
    - 成分：水杨酸、烟酰胺、透明质酸
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

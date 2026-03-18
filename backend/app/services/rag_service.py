"""
RAG 知识库服务
功能：文档管理、文本分块、向量化存储、语义搜索
"""
from typing import List, Dict, Optional
import json
import hashlib
from app.core.llm import call_llm


class RAGService:
    """RAG 知识库服务"""

    # 模拟向量存储（生产环境应使用 Qdrant）
    vector_store = {}

    # 文本分块配置
    CHUNK_SIZE = 500  # 每个chunk的字符数
    CHUNK_OVERLAP = 50  # 重叠字符数

    def __init__(self):
        pass

    def add_document(
        self,
        collection_name: str,
        text: str,
        metadata: Dict = None
    ) -> Dict:
        """
        添加文档到知识库

        Args:
            collection_name: 集合名称（类似文件夹）
            text: 文档内容
            metadata: 元数据

        Returns:
            添加结果
        """
        # 1. 文本分块
        chunks = self._chunk_text(text)

        # 2. 为每个chunk生成向量（模拟）
        chunks_with_vectors = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{collection_name}_{len(self.vector_store) + i}"
            # 生成模拟向量（实际应调用embedding API）
            vector = self._generate_vector(chunk)

            chunks_with_vectors.append({
                "id": chunk_id,
                "text": chunk,
                "vector": vector,
                "metadata": metadata or {}
            })

        # 3. 存储到向量库
        if collection_name not in self.vector_store:
            self.vector_store[collection_name] = []

        self.vector_store[collection_name].extend(chunks_with_vectors)

        return {
            "collection": collection_name,
            "chunks_count": len(chunks),
            "status": "success"
        }

    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 3
    ) -> List[Dict]:
        """
        语义搜索

        Args:
            collection_name: 集合名称
            query: 查询内容
            top_k: 返回前k个结果

        Returns:
            搜索结果列表
        """
        if collection_name not in self.vector_store:
            return []

        # 1. 把查询转成向量
        query_vector = self._generate_vector(query)

        # 2. 计算相似度
        chunks = self.vector_store[collection_name]
        results = []

        for chunk in chunks:
            similarity = self._cosine_similarity(query_vector, chunk["vector"])
            results.append({
                "text": chunk["text"],
                "score": similarity,
                "metadata": chunk.get("metadata", {})
            })

        # 3. 排序并返回top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _chunk_text(self, text: str) -> List[str]:
        """文本分块"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.CHUNK_SIZE
            chunk = text[start:end]

            # 尽量在句子边界分割
            if end < len(text):
                # 找最后一个句号、逗号或换行
                for sep in ['。', '！', '？', '，', '\n']:
                    last_sep = chunk.rfind(sep)
                    if last_sep > self.CHUNK_SIZE // 2:
                        end = start + last_sep + 1
                        chunk = text[start:end]
                        break

            chunks.append(chunk.strip())
            start = end - self.CHUNK_OVERLAP

        return chunks

    def _generate_vector(self, text: str) -> List[float]:
        """
        生成文本向量
        注意：这里使用简化实现，生产环境应调用专业的embedding API
        """
        # 简化的hash作为向量（实际应使用embedding模型）
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()

        # 转换为固定长度的向量
        vector = []
        for i in range(0, len(hash_hex), 2):
            vector.append(int(hash_hex[i:i+2], 16) / 255.0)

        # 确保向量长度为128
        while len(vector) < 128:
            vector.extend(vector[:min(128 - len(vector), len(vector))])

        return vector[:128]

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


# 服务实例
rag_service = RAGService()


# 预设知识库数据
def init_knowledge_base():
    """初始化预设知识库"""
    # 添加商品知识库
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

    # 添加直播话术知识库
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


# 初始化
init_knowledge_base()

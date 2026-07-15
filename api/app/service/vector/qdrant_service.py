from typing import List, Dict, Any, Optional
from qdrant_client import models

# 导入您提供的客户端实例
# 请根据您的实际模块路径修改此处的导入语句
from app.component import qdrant_client


class QdrantService:
    """向量数据库服务类，封装对 Qdrant 的常用操作"""

    def __init__(self):
        if qdrant_client is None:
            raise ValueError("Qdrant client is not initialized. Please check your configuration.")
        self.client = qdrant_client

    async def ensure_collection_exists(
            self,
            collection_name: str,
            vector_size: int,
            distance: str = "Cosine"
    ) -> bool:
        """
        确保指定的集合存在，如果不存在则创建它。

        :param collection_name: 集合名称
        :param vector_size: 向量维度
        :param distance: 距离计算方法，可选 "Cosine", "Euclid", "Dot"
        :return: 如果集合已存在或成功创建则返回 True，否则 False
        """
        try:
            # 检查集合是否存在
            exists = await self.client.collection_exists(collection_name)
            if exists:
                return True

            # 如果不存在，则创建集合
            distance_map = {
                "Cosine": models.Distance.COSINE,
                "Euclid": models.Distance.EUCLID,
                "Dot": models.Distance.DOT
            }
            distance_enum = distance_map.get(distance.upper())
            if not distance_enum:
                raise ValueError(f"Unsupported distance metric: {distance}")

            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=distance_enum
                )
            )
            return True
        except Exception as e:
            print(f"确保集合存在时发生错误: {e}")
            return False

    async def upsert(
            self,
            collection_name: str,
            vectors: List[List[float]],
            payloads: List[Dict[str, Any]],
            ids: Optional[List[int]] = None
    ) -> bool:
        """
        插入或更新向量记录 (upsert)。
        如果指定了 ids，则对应 id 的记录将被更新；如果没有指定，则会插入新记录。

        :param collection_name: 集合名称
        :param vectors: 向量列表，每个向量是一个浮点数列表
        :param payloads: 与向量对应的元数据（payload）列表
        :param ids: 可选，为每个向量指定的唯一ID列表。如果提供，长度必须与 vectors 一致。
        :return: 操作是否成功
        """
        if not vectors or len(vectors) != len(payloads):
            raise ValueError("向量列表和payload列表不能为空，且长度必须相等")

        if ids is not None and len(ids) != len(vectors):
            raise ValueError("ids列表的长度必须与vectors列表的长度相同")

        try:
            # 构建 PointStruct 对象列表
            points = [
                models.PointStruct(
                    id=pid if ids is not None else None,
                    vector=vec,
                    payload=payload
                )
                for pid, vec, payload in zip(ids, vectors, payloads)
            ]

            # 执行 upsert 操作
            operation_info = await self.client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True  # 等待操作完成
            )

            # 检查操作状态
            return operation_info.status == 'completed'
        except Exception as e:
            print(f"Upsert操作失败: {e}")
            return False

    async def search(
            self,
            collection_name: str,
            query_vector: List[float],
            limit: int = 10,
            filter: Optional[Dict[str, Any]] = None,
            with_payload: bool = True,
            with_vectors: bool = False
    ) -> List[Dict[str, Any]]:
        """
        在指定集合中搜索与查询向量最相似的向量。

        :param collection_name: 集合名称
        :param query_vector: 查询向量
        :param limit: 返回结果的数量上限
        :param filter: 可选，用于过滤结果的条件字典 (例如: {"category": "news"})
        :param with_payload: 是否返回 payload 数据
        :param with_vectors: 是否返回向量数据
        :return: 包含搜索结果的字典列表，每个字典包含 'id', 'score', 'payload' 等信息
        """
        qdrant_filter = None
        if filter:
            # 将简单的字典过滤器转换为 Qdrant Filter 对象
            # 这是一个简化的实现，仅支持完全匹配 (MatchValue)
            field_conditions = [
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value)
                )
                for key, value in filter.items()
            ]
            qdrant_filter = models.Filter(must=field_conditions)

        try:
            search_results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=limit,
                with_payload=with_payload,
                with_vectors=with_vectors
            )

            # 将结果转换为字典列表以便于使用
            return [{
                'id': hit.id,
                'score': hit.score,
                'payload': hit.payload,
                'vector': hit.vector
            } for hit in search_results]
        except Exception as e:
            print(f"搜索操作失败: {e}")
            return []

    async def get_by_id(
            self,
            collection_name: str,
            vector_id: int,
            with_payload: bool = True,
            with_vectors: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单个向量记录。

        :param collection_name: 集合名称
        :param vector_id: 向量ID
        :param with_payload: 是否返回payload
        :param with_vectors: 是否返回向量
        :return: 包含记录信息的字典，如果未找到则返回 None
        """
        try:
            record = await self.client.retrieve(
                collection_name=collection_name,
                ids=[vector_id],
                with_payload=with_payload,
                with_vectors=with_vectors
            )

            if record:
                return {
                    'id': record[0].id,
                    'payload': record[0].payload,
                    'vector': record[0].vector
                }
            return None
        except Exception as e:
            print(f"根据ID获取向量失败: {e}")
            return None

    async def delete_by_ids(
            self,
            collection_name: str,
            vector_ids: List[int]
    ) -> bool:
        """
        根据ID列表删除向量记录。

        :param collection_name: 集合名称
        :param vector_ids: 要删除的向量ID列表
        :return: 操作是否成功
        """
        if not vector_ids:
            return True

        try:
            operation_info = await self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=vector_ids)
            )
            return operation_info.status == 'completed'
        except Exception as e:
            print(f"删除操作失败: {e}")
            return False

    async def delete_by_filter(
            self,
            collection_name: str,
            filter: Dict[str, Any]
    ) -> bool:
        """
        根据过滤条件删除向量记录。

        :param collection_name: 集合名称
        :param filter: 用于指定删除条件的字典 (例如: {"category": "temp"})
        :return: 操作是否成功
        """
        if not filter:
            return False

        try:
            # 构建 Qdrant Filter 对象
            field_conditions = [
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value)
                )
                for key, value in filter.items()
            ]
            qdrant_filter = models.Filter(must=field_conditions)

            operation_info = await self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(filter=qdrant_filter)
            )
            return operation_info.status == 'completed'
        except Exception as e:
            print(f"根据过滤条件删除操作失败: {e}")
            return False
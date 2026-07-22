from langchain_postgres.v2.hybrid_search_config import HybridSearchConfig


class PGHybridSearchConfig(HybridSearchConfig):
    tsv_column = "content_tsv",
    tsv_lang = "pg_catalog.simple",
    fusion_function = "weighted_sum_ranking",
    fusion_function_parameters = {
        "vector_weight": 0.7,
        "text_weight": 0.3,
    },
    primary_top_k = 10,
    secondary_top_k = 10,
    index_name = "idx_content_tsv",
    index_type = "GIN"
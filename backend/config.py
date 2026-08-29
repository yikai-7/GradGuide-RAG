# backend/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# 路径配置
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CHROMA_DIR = DATA_DIR / "chroma_db"

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"

# Embedding 模型配置
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"

# Reranker 模型配置
RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"

# 检索配置
BM25_TOP_K = 20          # BM25 召回数量
VECTOR_TOP_K = 20        # 向量检索召回数量
RERANK_TOP_K = 5         # Reranker 精排后保留数量
RRF_K = 60               # RRF 融合参数

# 置信度阈值
CONFIDENCE_THRESHOLD_HIGH = 0.8
CONFIDENCE_THRESHOLD_LOW = 0.5
RECALL_FLOOR = 0.15           # 召回覆盖率满分时，单文档分数下限（低于此值仍拒答）

# Chunk 配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

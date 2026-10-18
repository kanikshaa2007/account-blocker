"""\n配置管理\n统一从项目根目录的 .env 文件加载配置\n"""

import os
from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
# 路径: MiroFish/.env (相对于 backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    # 如果根目录没有 .env，尝试加载环境变量（用于生产环境）
    load_dotenv(override=True)


class Config:
    """Flask配置类"""
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mirofish-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # JSON配置 - 禁用ASCII转义，让中文直接显示
    JSON_AS_ASCII = False
    
    # LLM配置（统一使用OpenAI格式）
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')
    
    # Zep配置
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')

    # Stage0: India Viral Monitoring - additive, all optional, warn-only
    # Neo4j persistent spread graph (Zep Cloud remains default semantic memory)
    NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')
    # Social connectors (official APIs only)
    X_BEARER_TOKEN = os.environ.get('X_BEARER_TOKEN')
    INSTAGRAM_ACCESS_TOKEN = os.environ.get('INSTAGRAM_ACCESS_TOKEN')
    YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
    PIB_FACTCHECK_RSS_URL = os.environ.get(
        'PIB_FACTCHECK_RSS_URL', 'https://factcheck.pib.gov.in/feed/'
    )
    # Safety: report_only is the only allowed mode in Stage0
    ACTION_MODE = os.environ.get('ACTION_MODE', 'report_only')
    # Stage8: live social feeds (keyless public endpoints)
    REDDIT_SUBS = [s.strip() for s in os.environ.get('REDDIT_SUBS', 'india').split(',') if s.strip()]
    YOUTUBE_CHANNELS = [c.strip() for c in os.environ.get('YOUTUBE_CHANNELS', 'UCGDQNvybfDDeGTf4GtigXaw').split(',') if c.strip()]
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}
    
    # 文本处理配置
    DEFAULT_CHUNK_SIZE = 500  # 默认切块大小
    DEFAULT_CHUNK_OVERLAP = 50  # 默认重叠大小
    
    # OASIS模拟配置
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')
    
    # OASIS平台可用动作配置
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]
    
    # Report Agent配置
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))
    
    @classmethod
    def validate(cls) -> list[str]:
        """验证必要配置"""
        errors: list[str] = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY 未配置")
        if not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY 未配置")
        if os.environ.get("ZEP_API_URL"):
            errors.append("ZEP_API_URL 不受支持；MiroFish 仅连接 Zep Cloud")
        if cls.DEBUG:
            import warnings
            warnings.warn("Flask DEBUG mode is enabled. Do not use in production.", RuntimeWarning)
        return errors

    @classmethod
    def validate_stage0(cls) -> list[str]:
        """Stage0 warn-only checks: baseline + new connectors. Never blocks boot."""
        warnings_list: list[str] = []
        for missing in cls.validate():
            warnings_list.append(f"baseline: {missing}")
        if not cls.NEO4J_PASSWORD:
            warnings_list.append("stage0: NEO4J_PASSWORD 未配置，Neo4j 写入将跳过")
        if not cls.X_BEARER_TOKEN:
            warnings_list.append("stage0: X_BEARER_TOKEN 未配置，X 采集将跳过")
        if not cls.INSTAGRAM_ACCESS_TOKEN:
            warnings_list.append("stage0: INSTAGRAM_ACCESS_TOKEN 未配置，Instagram 采集将跳过")
        if not cls.YOUTUBE_API_KEY:
            warnings_list.append("stage0: YOUTUBE_API_KEY 未配置，YouTube 采集将跳过")
        if cls.ACTION_MODE != "report_only":
            warnings_list.append(
                f"stage0: ACTION_MODE={cls.ACTION_MODE} 不允许，Stage0 仅允许 report_only"
            )
        return warnings_list

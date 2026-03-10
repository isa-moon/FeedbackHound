"""全局配置。"""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_secret(key):
    """优先从 st.secrets 读取，不可用时从 .env 读取。"""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key)


APP_NAME = "FeedbackHound"
APP_SLOGAN = "用户反馈抓取与 AI 分析工具"

REDDIT_CLIENT_ID = get_secret("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = get_secret("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = get_secret("REDDIT_USER_AGENT")

DEFAULT_MAX_POSTS = 100
MAX_POSTS_LIMIT = 1000
DEFAULT_MIN_DELAY = 0.2
DEFAULT_MAX_DELAY = 0.6
REQUEST_TIMEOUT = 60
SUMMARY_POST_LIMIT = 30
SUMMARY_TEXT_LIMIT = 200
EXPORT_FILENAME_PREFIX = "feedbackhound"
SUPPORTED_AI_PROVIDERS = {
    "OpenAI": "openai",
    "Anthropic": "anthropic",
    "DeepSeek": "deepseek",
}
AI_PROVIDER_OPTIONS = list(SUPPORTED_AI_PROVIDERS.keys())
AI_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "deepseek": "deepseek-chat",
}
STEP_GUIDE = [
    "第 1 步：填写 subreddit、日期范围和抓取数量后开始抓取。",
    "第 2 步：在同一页面查看数据预览、搜索、统计和导出。",
    "第 3 步：按需填写 AI 服务商与 API Key，生成分析报告。",
]
SESSION_DEFAULTS = {
    "ai_provider": AI_PROVIDER_OPTIONS[0],
    "ai_api_key": "",
    "scraped_data": None,
    "scrape_summary": {},
    "analysis_report": "",
    "analysis_markdown_name": "",
    "analysis_pdf_error": "",
}

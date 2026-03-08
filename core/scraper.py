"""Reddit 抓取核心逻辑。"""

from __future__ import annotations

import io
import random
import time
from datetime import date, datetime, time as dt_time
from typing import Callable, Optional

import pandas as pd
import praw

from config import (
    DEFAULT_MAX_DELAY,
    DEFAULT_MIN_DELAY,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
)

ProgressCallback = Optional[Callable[[int, int], None]]
StatusCallback = Optional[Callable[[str], None]]


class ScraperError(Exception):
    """抓取模块错误。"""


def convert_timestamp(timestamp: float) -> str:
    """将 Unix 时间戳转换为本地时间字符串。"""
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def _normalize_date_range(start_date: Optional[date], end_date: Optional[date]) -> tuple[Optional[float], Optional[float]]:
    start_timestamp = None
    end_timestamp = None

    if start_date:
        start_timestamp = datetime.combine(start_date, dt_time.min).timestamp()
    if end_date:
        end_timestamp = datetime.combine(end_date, dt_time.max).timestamp()

    if start_timestamp and end_timestamp and start_timestamp > end_timestamp:
        raise ScraperError("起始日期不能晚于结束日期。")

    return start_timestamp, end_timestamp


def initialize_reddit() -> praw.Reddit:
    """使用 .env 中的 Reddit 凭据初始化客户端，并进行轻量验证。"""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET or not REDDIT_USER_AGENT:
        raise ScraperError("缺少 Reddit 凭据，请检查项目根目录下的 .env 配置。")

    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID.strip(),
            client_secret=REDDIT_CLIENT_SECRET.strip(),
            user_agent=REDDIT_USER_AGENT.strip(),
            check_for_async=False,
        )
        reddit.read_only = True
        _ = reddit.user.me()
        return reddit
    except Exception as exc:
        raise ScraperError("Reddit API 验证失败，请检查 .env 中的 Reddit 配置是否正确。") from exc


def fetch_posts(
    reddit: praw.Reddit,
    subreddit_name: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    max_posts: int = 100,
    min_delay: float = DEFAULT_MIN_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    progress_callback: ProgressCallback = None,
    status_callback: StatusCallback = None,
) -> pd.DataFrame:
    """抓取 subreddit 帖子并返回 DataFrame。"""
    if not subreddit_name or not subreddit_name.strip():
        raise ScraperError("请输入有效的 subreddit 名称。")
    if max_posts <= 0:
        raise ScraperError("最大抓取数量必须大于 0。")
    if min_delay < 0 or max_delay < 0 or min_delay > max_delay:
        raise ScraperError("延迟配置无效，请确保最小延迟不大于最大延迟且均不为负数。")

    start_timestamp, end_timestamp = _normalize_date_range(start_date, end_date)
    collected_posts: list[dict] = []
    subreddit = reddit.subreddit(subreddit_name.strip())
    seen_ids: set[str] = set()

    if status_callback:
        status_callback(f"正在连接 r/{subreddit_name.strip()} 并抓取帖子…")

    try:
        for submission in subreddit.new(limit=max_posts * 3):
            post_time = submission.created_utc

            if start_timestamp and post_time < start_timestamp:
                break
            if end_timestamp and post_time > end_timestamp:
                continue
            if submission.id in seen_ids:
                continue

            seen_ids.add(submission.id)
            collected_posts.append(
                {
                    "post_id": submission.id,
                    "subreddit": subreddit_name.strip(),
                    "title": submission.title,
                    "author": str(submission.author) if submission.author else "[已删除]",
                    "created_utc": post_time,
                    "post_time": convert_timestamp(post_time),
                    "content": submission.selftext if hasattr(submission, "selftext") else "",
                    "score": int(getattr(submission, "score", 0) or 0),
                    "num_comments": int(getattr(submission, "num_comments", 0) or 0),
                    "url": f"https://reddit.com{submission.permalink}",
                }
            )

            current_count = len(collected_posts)
            if progress_callback:
                progress_callback(current_count, max_posts)
            if status_callback:
                status_callback(f"已抓取 {current_count}/{max_posts} 条帖子")

            if current_count >= max_posts:
                break

            if max_delay > 0:
                time.sleep(random.uniform(min_delay, max_delay))

        if not collected_posts:
            return pd.DataFrame(
                columns=[
                    "post_id",
                    "subreddit",
                    "title",
                    "author",
                    "created_utc",
                    "post_time",
                    "content",
                    "score",
                    "num_comments",
                    "url",
                ]
            )

        return pd.DataFrame(collected_posts).sort_values("created_utc", ascending=False).reset_index(drop=True)
    except ScraperError:
        raise
    except Exception as exc:
        raise ScraperError(f"抓取帖子失败：{exc}") from exc


def dataframe_to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    """将 DataFrame 导出为 CSV 字节流。"""
    return dataframe.to_csv(index=False).encode("utf-8-sig")


def dataframe_to_excel_bytes(dataframe: pd.DataFrame) -> bytes:
    """将 DataFrame 导出为 Excel 字节流。"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="posts")
    buffer.seek(0)
    return buffer.getvalue()

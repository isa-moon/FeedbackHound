"""AI 调用与数据摘要逻辑。"""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from config import AI_MODELS, REQUEST_TIMEOUT, SUMMARY_POST_LIMIT, SUMMARY_TEXT_LIMIT


class AIAnalyzerError(Exception):
    """AI 分析模块错误。"""


def _truncate_text(value: Any, limit: int = SUMMARY_TEXT_LIMIT) -> str:
    text = str(value or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return f"{text[:limit]}…"


def build_data_summary(dataframe: pd.DataFrame, subreddit: str) -> str:
    """将帖子数据整理成受控长度的文本摘要。"""
    if dataframe is None or dataframe.empty:
        raise AIAnalyzerError("当前没有可用于分析的数据，请先完成抓取。")

    ranked = dataframe.sort_values(["score", "num_comments"], ascending=False).head(SUMMARY_POST_LIMIT)
    lines = [
        f"社区：r/{subreddit}",
        f"总帖子数：{len(dataframe)}",
        f"纳入摘要帖子数：{len(ranked)}",
        "",
    ]

    for index, row in enumerate(ranked.itertuples(index=False), start=1):
        lines.extend(
            [
                f"[{index}] 标题：{_truncate_text(getattr(row, 'title', ''))}",
                f"发布时间：{getattr(row, 'post_time', '')}",
                f"Score：{getattr(row, 'score', 0)} | 评论数：{getattr(row, 'num_comments', 0)}",
                f"正文摘要：{_truncate_text(getattr(row, 'content', ''))}",
                f"链接：{getattr(row, 'url', '')}",
                "",
            ]
        )

    return "\n".join(lines).strip()


def _openai_like_request(url: str, model: str, api_key: str, prompt: str) -> str:
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一名专业的中文商业分析助手。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        },
        timeout=REQUEST_TIMEOUT,
    )
    _raise_for_response(response)
    payload = response.json()
    try:
        return payload["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AIAnalyzerError("AI 服务返回了异常响应，未能解析生成内容。") from exc


def _anthropic_request(api_key: str, prompt: str) -> str:
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": AI_MODELS["anthropic"],
            "max_tokens": 1800,
            "temperature": 0.4,
            "messages": [
                {"role": "user", "content": prompt},
            ],
        },
        timeout=REQUEST_TIMEOUT,
    )
    _raise_for_response(response)
    payload = response.json()
    try:
        blocks = payload["content"]
        texts = [block.get("text", "") for block in blocks if block.get("type") == "text"]
        result = "\n".join(part for part in texts if part).strip()
        if not result:
            raise AIAnalyzerError("AI 服务返回了空内容。")
        return result
    except (KeyError, TypeError) as exc:
        raise AIAnalyzerError("AI 服务返回了异常响应，未能解析生成内容。") from exc


def _raise_for_response(response: requests.Response) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = ""
        try:
            payload = response.json()
            detail = payload.get("error", {}).get("message") or payload.get("message") or str(payload)
        except ValueError:
            detail = response.text[:300]
        raise AIAnalyzerError(f"AI 请求失败（HTTP {response.status_code}）：{detail}") from exc


def call_ai_api(provider: str, api_key: str, prompt: str, data_summary: str) -> str:
    """统一接口，根据 provider 调用不同的 AI API。"""
    if not provider:
        raise AIAnalyzerError("请选择 AI 服务商。")
    if not api_key or not api_key.strip():
        raise AIAnalyzerError("请输入 AI API Key。")

    combined_prompt = f"{prompt}\n\n{data_summary}".strip()

    try:
        if provider == "openai":
            return _openai_like_request(
                "https://api.openai.com/v1/chat/completions",
                AI_MODELS["openai"],
                api_key.strip(),
                combined_prompt,
            )
        if provider == "deepseek":
            return _openai_like_request(
                "https://api.deepseek.com/v1/chat/completions",
                AI_MODELS["deepseek"],
                api_key.strip(),
                combined_prompt,
            )
        if provider == "anthropic":
            return _anthropic_request(api_key.strip(), combined_prompt)
        raise AIAnalyzerError("暂不支持所选 AI 服务商。")
    except requests.Timeout as exc:
        raise AIAnalyzerError("AI 请求超时，请稍后重试。") from exc
    except requests.RequestException as exc:
        raise AIAnalyzerError(f"AI 请求失败：{exc}") from exc

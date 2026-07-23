"""结构化报告解析与图表渲染。

设计原则（详见本次改造思路）：
- 事实类图表（互动分布）直接从抓取的 DataFrame 计算，零幻觉；
- 定性类图表（情感、优劣势、维度对比）由 AI 以 JSON 结构化输出后再渲染；
- 配色经过色盲可辨性校验，且每个分类都带直接标签，身份不单靠颜色区分。
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

import pandas as pd
import plotly.graph_objects as go

# 经 dataviz 调色校验的分类色：
SENTIMENT_POS = "#0d9488"   # 正面 · 青绿
SENTIMENT_NEG = "#e11d48"   # 负面 · 玫红
SENTIMENT_NEU = "#9ca3af"   # 中性 · 语义化灰（带直接标签）
STRENGTH_COLOR = "#0d9488"  # 优势 · 单色量级
WEAKNESS_COLOR = "#e11d48"  # 劣势 · 单色量级
RADAR_USER = "#2563eb"      # 你的品牌 · 蓝
RADAR_COMP = "#f59e0b"      # 竞品 · 橙
SCATTER_COLOR = "#2563eb"

_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"


# --------------------------------------------------------------------------
# 解析：从 AI 文本中分离出 JSON 结构与叙述 Markdown
# --------------------------------------------------------------------------
def _find_json_block(text: str) -> tuple[Optional[str], Optional[tuple[int, int]]]:
    """定位文本中的 JSON 块，返回 (json字符串, (起, 止))。"""
    fence = re.search(r"```json\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        return fence.group(1).strip(), fence.span()

    for match in re.finditer(r"```\s*(.*?)```", text, re.DOTALL):
        candidate = match.group(1).strip()
        if candidate.startswith("{"):
            return candidate, match.span()

    # 无围栏时，做一次花括号配平扫描
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1], (start, i + 1)
    return None, None


_SCAFFOLD_BAR = re.compile(r"^\s*=+.*=+\s*$")
_SCAFFOLD_HEAD = re.compile(
    r"^\s*#{0,6}\s*(第[一二三]部分|.*结构化数据.*JSON|.*叙述报告.*Markdown)",
    re.IGNORECASE,
)


def _clean_narrative(text: str) -> str:
    """清理叙述中的脚手架残留：分隔条、分节标题，以及抽走 JSON 后悬空的尾部标题/分隔线。"""
    lines = [
        ln for ln in text.split("\n")
        if not _SCAFFOLD_BAR.match(ln) and not _SCAFFOLD_HEAD.match(ln)
    ]
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()

    # 反复剥除尾部悬空的分隔线（---）与空标题（# 开头且其后无内容）
    prev = None
    while prev != out:
        prev = out
        out = re.sub(r"(?:\s*-{3,}\s*)+$", "", out).strip()
        tail = out.split("\n")
        if tail and tail[-1].lstrip().startswith("#"):
            out = "\n".join(tail[:-1]).strip()
    return out


def extract_report_payload(text: str) -> tuple[Optional[dict], str]:
    """拆分 AI 输出：返回 (结构化数据 或 None, 叙述 Markdown)。

    解析失败时降级为 (None, 清理后的原文)，绝不抛出，保证报告至少有文字。
    """
    if not text:
        return None, ""

    block, span = _find_json_block(text)
    if block is not None and span is not None:
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            return None, _clean_narrative(text)
        narrative = _clean_narrative(text[:span[0]] + text[span[1]:])
        return data, narrative

    return None, _clean_narrative(text)


# --------------------------------------------------------------------------
# 数值兜底
# --------------------------------------------------------------------------
def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(round(float(value))))
    except (TypeError, ValueError):
        return default


def _safe_num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _style(fig: go.Figure, height: int = 340) -> go.Figure:
    """统一浅色主题：透明背景、细网格、系统字体。"""
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=12, t=52, b=12),
        font=dict(family=_FONT, size=13, color="#333333"),
        title=dict(font=dict(family=_FONT, size=15, color="#000000"), x=0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eeeeee", zeroline=False, linecolor="#e0e0e0")
    fig.update_yaxes(showgrid=True, gridcolor="#eeeeee", zeroline=False, linecolor="#e0e0e0")
    return fig


# --------------------------------------------------------------------------
# 图表构造（返回 Figure 或 None；数据不足即 None）
# --------------------------------------------------------------------------
def sentiment_donut(sentiment: Any) -> Optional[go.Figure]:
    """情感分布环形图（正/负/中）。"""
    if not isinstance(sentiment, dict):
        return None
    keys = ["positive", "negative", "neutral"]
    labels = ["正面", "负面", "中性"]
    colors = [SENTIMENT_POS, SENTIMENT_NEG, SENTIMENT_NEU]
    values = [_safe_int(sentiment.get(k)) for k in keys]
    if sum(values) <= 0:
        return None

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.58,
            sort=False,
            direction="clockwise",
            marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
            textinfo="label+percent",
            textfont=dict(family=_FONT, size=13),
            hovertemplate="%{label}：%{value}（%{percent}）<extra></extra>",
        )
    )
    fig.update_layout(title="用户情感分布", showlegend=False)
    return _style(fig, height=320)


def mentions_bar(items: Any, title: str, color: str) -> Optional[go.Figure]:
    """优势/劣势横向条形图，按被提及次数排序。"""
    if not isinstance(items, list):
        return None
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        point = str(item.get("point", "")).strip()
        if point:
            rows.append((point, _safe_int(item.get("mentions"))))
    if not rows:
        return None

    rows.sort(key=lambda r: r[1])  # 升序：横向图中最大者显示在顶部
    labels = [r[0] for r in rows]
    vals = [r[1] for r in rows]

    fig = go.Figure(
        go.Bar(
            x=vals,
            y=labels,
            orientation="h",
            marker=dict(color=color, cornerradius=4, line=dict(color="#ffffff", width=1)),
            text=vals,
            textposition="outside",
            textfont=dict(family=_FONT, size=12),
            hovertemplate="%{y}：被提及 %{x} 次<extra></extra>",
            width=0.62,
        )
    )
    fig.update_layout(title=title, showlegend=False, bargap=0.35)
    _style(fig, height=max(220, 48 * len(rows) + 90))
    fig.update_xaxes(title="被提及次数", rangemode="tozero")
    fig.update_yaxes(showgrid=False, automargin=True)
    return fig


def comparison_radar(radar: Any, user_label: str, competitor_label: str) -> Optional[go.Figure]:
    """你的品牌 vs 竞品 的维度雷达图。"""
    if not isinstance(radar, dict):
        return None
    dims = radar.get("dimensions")
    user = radar.get("user_brand")
    comp = radar.get("competitor")
    if not (isinstance(dims, list) and isinstance(user, list) and isinstance(comp, list)):
        return None
    n = min(len(dims), len(user), len(comp))
    if n < 3:
        return None

    dims = [str(d) for d in dims[:n]]
    user_vals = [_safe_num(v) for v in user[:n]]
    comp_vals = [_safe_num(v) for v in comp[:n]]
    theta = dims + [dims[0]]  # 闭合多边形

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=user_vals + [user_vals[0]], theta=theta, name=user_label or "你的品牌",
            fill="toself", line=dict(color=RADAR_USER, width=2),
            fillcolor="rgba(37,99,235,0.12)",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=comp_vals + [comp_vals[0]], theta=theta, name=competitor_label or "竞品",
            fill="toself", line=dict(color=RADAR_COMP, width=2),
            fillcolor="rgba(245,158,11,0.12)",
        )
    )
    fig.update_layout(
        title="优劣势维度对比",
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10], gridcolor="#eeeeee", linecolor="#e0e0e0"),
            angularaxis=dict(gridcolor="#eeeeee", linecolor="#e0e0e0"),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return _style(fig, height=380)


def engagement_scatter(dataframe: Optional[pd.DataFrame]) -> Optional[go.Figure]:
    """互动分布散点图（Score × 评论数），纯从抓取数据计算。"""
    if dataframe is None or getattr(dataframe, "empty", True):
        return None
    if "score" not in dataframe or "num_comments" not in dataframe:
        return None

    titles = dataframe["title"] if "title" in dataframe else None
    fig = go.Figure(
        go.Scatter(
            x=dataframe["score"],
            y=dataframe["num_comments"],
            mode="markers",
            marker=dict(size=9, color=SCATTER_COLOR, opacity=0.55, line=dict(color="#ffffff", width=1)),
            text=titles,
            hovertemplate="Score %{x} · 评论 %{y}<br>%{text}<extra></extra>"
            if titles is not None
            else "Score %{x} · 评论 %{y}<extra></extra>",
        )
    )
    fig.update_layout(title="高互动分布（Score × 评论数）", showlegend=False)
    _style(fig, height=340)
    fig.update_xaxes(title="Score", rangemode="tozero")
    fig.update_yaxes(title="评论数", rangemode="tozero")
    return fig


def render_competitor_charts(
    payload: Optional[dict],
    dataframe: Optional[pd.DataFrame],
    user_label: str,
    competitor_label: str,
) -> None:
    """在 Streamlit 中渲染竞品分析图表看板。payload 为空时仍尝试渲染数据类图表。"""
    import streamlit as st

    scatter = engagement_scatter(dataframe)

    if not payload:
        if scatter is not None:
            st.plotly_chart(scatter, use_container_width=True)
        return

    donut = sentiment_donut(payload.get("sentiment"))
    radar = comparison_radar(payload.get("radar"), user_label, competitor_label)
    strengths = mentions_bar(payload.get("strengths"), "竞品优势（被提及次数）", STRENGTH_COLOR)
    weaknesses = mentions_bar(payload.get("weaknesses"), "竞品劣势（被提及次数）", WEAKNESS_COLOR)

    top = st.columns(2)
    if donut is not None:
        top[0].plotly_chart(donut, use_container_width=True)
    if radar is not None:
        top[1].plotly_chart(radar, use_container_width=True)

    mid = st.columns(2)
    if strengths is not None:
        mid[0].plotly_chart(strengths, use_container_width=True)
    if weaknesses is not None:
        mid[1].plotly_chart(weaknesses, use_container_width=True)

    if scatter is not None:
        st.plotly_chart(scatter, use_container_width=True)

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

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    _CHARTS_OK = True
except Exception:  # 云端缺 plotly 时降级，避免整个应用崩溃
    go = None
    pio = None
    _CHARTS_OK = False

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
def sentiment_donut(sentiment: Any) -> Optional["go.Figure"]:
    """情感分布环形图（正/负/中）。"""
    if not _CHARTS_OK or not isinstance(sentiment, dict):
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


def _hbar(rows: list[tuple[str, float]], title: str, color: str, x_title: str, hover: str) -> Optional["go.Figure"]:
    """通用横向条形图。rows 为 (标签, 数值)；按数值升序（最大者显示在顶部）。"""
    if not _CHARTS_OK or not rows:
        return None
    rows = sorted(rows, key=lambda r: r[1])
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
            hovertemplate=hover,
            width=0.62,
        )
    )
    fig.update_layout(title=title, showlegend=False, bargap=0.35)
    _style(fig, height=max(220, 48 * len(rows) + 90))
    fig.update_xaxes(title=x_title, rangemode="tozero")
    fig.update_yaxes(showgrid=False, automargin=True)
    return fig


def _collect(items: Any, label_key: str, value_key: str) -> list[tuple[str, int]]:
    """从 [{label_key:..., value_key:...}] 中抽取 (标签, 整数值)。"""
    rows = []
    if not isinstance(items, list):
        return rows
    for item in items:
        if not isinstance(item, dict):
            continue
        label = str(item.get(label_key, "")).strip()
        if label:
            rows.append((label, _safe_int(item.get(value_key))))
    return rows


def mentions_bar(items: Any, title: str, color: str) -> Optional[go.Figure]:
    """优势/劣势横向条形图，按被提及次数排序。"""
    return _hbar(_collect(items, "point", "mentions"), title, color, "被提及次数", "%{y}：被提及 %{x} 次<extra></extra>")


def topics_bar(items: Any, color: str = RADAR_USER) -> Optional[go.Figure]:
    """热门话题 Top5 横向条形图（按热度）。"""
    return _hbar(_collect(items, "topic", "heat"), "热门话题 Top5（热度）", color, "热度", "%{y}：热度 %{x}<extra></extra>")


def features_bar(items: Any, color: str = SENTIMENT_POS) -> Optional[go.Figure]:
    """高互动内容特征横向条形图（按出现频次）。"""
    return _hbar(_collect(items, "feature", "count"), "高互动内容特征（出现频次）", color, "出现次数", "%{y}：出现 %{x} 次<extra></extra>")


def _post_timestamps(dataframe: pd.DataFrame) -> Optional[pd.Series]:
    """从 created_utc（优先）或 post_time 解析出 datetime 序列。"""
    if "created_utc" in dataframe:
        ts = pd.to_datetime(dataframe["created_utc"], unit="s", errors="coerce")
    elif "post_time" in dataframe:
        ts = pd.to_datetime(dataframe["post_time"], errors="coerce")
    else:
        return None
    ts = ts.dropna()
    return ts if not ts.empty else None


def posting_heatmap(dataframe: Optional[pd.DataFrame]) -> Optional["go.Figure"]:
    """发帖时段热力图（星期 × 小时），纯从抓取数据计算。"""
    if not _CHARTS_OK or dataframe is None or getattr(dataframe, "empty", True):
        return None
    ts = _post_timestamps(dataframe)
    if ts is None:
        return None

    matrix = [[0] * 24 for _ in range(7)]
    for weekday, hour in zip(ts.dt.dayofweek, ts.dt.hour):
        matrix[int(weekday)][int(hour)] += 1

    days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    fig = go.Figure(
        go.Heatmap(
            z=matrix,
            x=[str(h) for h in range(24)],
            y=days,
            colorscale=[[0.0, "#eff6ff"], [0.5, "#60a5fa"], [1.0, "#1e3a8a"]],
            hovertemplate="%{y} %{x}:00<br>发帖 %{z} 条<extra></extra>",
            colorbar=dict(title="帖数", thickness=12, len=0.8),
        )
    )
    fig.update_layout(title="发帖时段热力（星期 × 小时）")
    _style(fig, height=320)
    fig.update_xaxes(title="小时", dtick=2, showgrid=False)
    fig.update_yaxes(showgrid=False, autorange="reversed")  # 周一置顶
    return fig


def comparison_radar(radar: Any, user_label: str, competitor_label: str) -> Optional["go.Figure"]:
    """你的品牌 vs 竞品 的维度雷达图。"""
    if not _CHARTS_OK or not isinstance(radar, dict):
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
    _style(fig, height=440)
    # 该图分值由模型综合判断给出，缺少可复算的数据依据。
    # 说明写进图表本身（而非页面），保证导出与截图时不丢失；
    # 放在底部作脚注，避免与顶部图例重叠。
    fig.add_annotation(
        text="分值为模型综合判断的估计值，非抓取数据统计",
        xref="paper", yref="paper", x=0, y=-0.10,
        xanchor="left", yanchor="top", showarrow=False,
        font=dict(family=_FONT, size=12, color="#8a8a8a"),
    )
    # 顶部留白加大，使绘图区连同图例整体下移，与标题拉开距离
    fig.update_layout(
        margin=dict(l=12, r=12, t=96, b=60),
        title=dict(y=0.96, yanchor="top"),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="left", x=0),
    )
    return fig


def engagement_scatter(dataframe: Optional[pd.DataFrame]) -> Optional["go.Figure"]:
    """互动分布散点图（Score × 评论数），纯从抓取数据计算。"""
    if not _CHARTS_OK or dataframe is None or getattr(dataframe, "empty", True):
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

    if not _CHARTS_OK:
        st.info("图表库（plotly）暂未就绪，本次仅显示文字报告。请在右下角 Manage app → Reboot 重启应用以完成安装。")
        return

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


def render_content_ops_charts(payload: Optional[dict], dataframe: Optional[pd.DataFrame]) -> None:
    """在 Streamlit 中渲染内容运营图表看板。payload 为空时仍渲染时段/互动等数据类图表。"""
    import streamlit as st

    if not _CHARTS_OK:
        st.info("图表库（plotly）暂未就绪，本次仅显示文字报告。请在右下角 Manage app → Reboot 重启应用以完成安装。")
        return

    heatmap = posting_heatmap(dataframe)
    scatter = engagement_scatter(dataframe)
    topics = topics_bar(payload.get("hot_topics")) if payload else None
    features = features_bar(payload.get("engagement_features")) if payload else None

    if topics is not None or features is not None:
        top = st.columns(2)
        if topics is not None:
            top[0].plotly_chart(topics, use_container_width=True)
        if features is not None:
            top[1].plotly_chart(features, use_container_width=True)

    if heatmap is not None:
        st.plotly_chart(heatmap, use_container_width=True)
    if scatter is not None:
        st.plotly_chart(scatter, use_container_width=True)


# --------------------------------------------------------------------------
# 图表收集（供 HTML 导出复用；顺序与看板一致）
# --------------------------------------------------------------------------
def competitor_figures(payload, dataframe, user_label, competitor_label):
    """返回竞品报告的图表列表（去掉 None）。"""
    if not _CHARTS_OK:
        return []
    figs = []
    if payload:
        figs += [
            sentiment_donut(payload.get("sentiment")),
            comparison_radar(payload.get("radar"), user_label, competitor_label),
            mentions_bar(payload.get("strengths"), "竞品优势（被提及次数）", STRENGTH_COLOR),
            mentions_bar(payload.get("weaknesses"), "竞品劣势（被提及次数）", WEAKNESS_COLOR),
        ]
    figs.append(engagement_scatter(dataframe))
    return [f for f in figs if f is not None]


def content_ops_figures(payload, dataframe):
    """返回内容运营报告的图表列表（去掉 None）。"""
    if not _CHARTS_OK:
        return []
    figs = []
    if payload:
        figs += [
            topics_bar(payload.get("hot_topics")),
            features_bar(payload.get("engagement_features")),
        ]
    figs += [posting_heatmap(dataframe), engagement_scatter(dataframe)]
    return [f for f in figs if f is not None]


# --------------------------------------------------------------------------
# 自包含 HTML 报告导出
# --------------------------------------------------------------------------
_HTML_CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin: 0; background: #ffffff; color: #111111;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', sans-serif;
  line-height: 1.7; }
.wrap { max-width: 1120px; margin: 0 auto; padding: 48px 28px 64px; }
.brand { font-size: .95rem; color: #888; letter-spacing: .02em; }
h1.title { font-size: clamp(1.9rem, 4vw, 2.6rem); font-weight: 800; letter-spacing: -.03em; margin: .3rem 0 .6rem; }
.subtitle { color: #666; font-size: 1rem; }
.meta { color: #999; font-size: .85rem; margin-top: .4rem; }
hr { border: none; border-top: 1px solid #ececec; margin: 2rem 0; }
h2.section { font-size: 1.35rem; font-weight: 700; letter-spacing: -.02em; margin: 2.2rem 0 1rem;
  display: flex; align-items: center; gap: 10px; }
h2.section::before { content: ''; width: 9px; height: 9px; border-radius: 999px; background: #111; }
.charts { display: flex; flex-wrap: wrap; gap: 18px; }
.chart { flex: 1 1 460px; min-width: 340px; border: 1px solid #eee; border-radius: 14px; padding: 6px; overflow-x: auto; }
.report { border: 1px solid #ececec; border-radius: 16px; padding: 8px 26px 22px; }
.report h1, .report h2, .report h3 { letter-spacing: -.02em; }
.report h1 { font-size: 1.5rem; } .report h2 { font-size: 1.2rem; } .report h3 { font-size: 1.03rem; }
.report p, .report li { color: #333; }
.report blockquote { margin: 1rem 0; padding-left: 1rem; border-left: 3px solid #d9d9d9; color: #666; }
.report table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
.report th, .report td { border: 1px solid #e5e5e5; padding: 8px 10px; text-align: left; font-size: .95rem; }
.report th { background: #f7f7f7; }
.footer { text-align: center; color: #aaa; font-size: .82rem; margin-top: 2.5rem; }
""".strip()


def _escape(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_html_report(title: str, subtitle: str, narrative_md: str, figures: list) -> str:
    """把图表与文字组装成一个自包含 HTML 报告（plotly.js 内联，可离线打开）。"""
    import datetime

    import markdown2

    figures = [f for f in (figures or []) if f is not None]
    chart_html = ""
    if _CHARTS_OK and pio is not None and figures:
        cards = []
        for i, fig in enumerate(figures):
            # 仅第一张内联 plotly.js，整份文件只带一份库
            include = "inline" if i == 0 else False
            snippet = pio.to_html(fig, include_plotlyjs=include, full_html=False,
                                  config={"displayModeBar": False})
            cards.append(f"<div class='chart'>{snippet}</div>")
        chart_html = f"<h2 class='section'>数据看板</h2><div class='charts'>{''.join(cards)}</div>"

    narrative_html = markdown2.markdown(
        narrative_md or "", extras=["tables", "fenced-code-blocks", "cuddled-lists", "strike"]
    )
    generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_escape(title)}</title>
<style>{_HTML_CSS}</style></head>
<body><div class="wrap">
  <div class="brand">FeedbackHound · 反馈猎犬</div>
  <h1 class="title">{_escape(title)}</h1>
  <div class="subtitle">{_escape(subtitle)}</div>
  <div class="meta">生成时间：{generated_at}</div>
  <hr>
  {chart_html}
  <h2 class="section">分析报告</h2>
  <div class="report">{narrative_html}</div>
  <div class="footer">© FeedbackHound · 本报告由 AI 辅助生成，请结合业务判断使用</div>
</div></body></html>"""

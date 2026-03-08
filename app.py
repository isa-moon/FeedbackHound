"""Streamlit 主入口。"""

from datetime import date

import streamlit as st

from config import (
    AI_PROVIDER_OPTIONS,
    APP_NAME,
    APP_SLOGAN,
    DEFAULT_MAX_POSTS,
    MAX_POSTS_LIMIT,
    SUPPORTED_AI_PROVIDERS,
)
from core.ai_analyzer import AIAnalyzerError, build_data_summary, call_ai_api
from core.report_generator import (
    ReportGenerationError,
    build_markdown_report,
    generate_report_filename,
    markdown_to_bytes,
    markdown_to_pdf_bytes,
)
from core.scraper import ScraperError, dataframe_to_csv_bytes, dataframe_to_excel_bytes, fetch_posts, initialize_reddit
from core.ui import setup_page
from prompts.competitor_analysis import COMPETITOR_ANALYSIS_PROMPT
from prompts.content_operations import CONTENT_OPERATIONS_PROMPT


st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="collapsed")
setup_page()

st.markdown(
    """
    <style>
        .stApp {
            background: #ffffff;
            color: #000000;
        }
        .block-container {
            max-width: 1120px;
            padding-top: 3.5rem;
            padding-bottom: 3rem;
        }
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        h1, h2, h3 {
            color: #000000;
            letter-spacing: -0.03em;
        }
        p, li, div {
            line-height: 1.6;
        }
        .fh-hero {
            padding: 0;
            margin: 0 0 4.25rem 0;
        }
        .fh-brand {
            font-size: clamp(3rem, 8vw, 4.6rem);
            font-weight: 800;
            line-height: 0.95;
            margin: 0;
            color: #000000;
        }
        .fh-subtitle {
            margin-top: 1rem;
            color: #666666;
            font-size: 1rem;
        }
        .fh-slogan {
            margin-top: 1.4rem;
            color: #000000;
            font-size: 1.25rem;
            font-weight: 400;
            line-height: 1.5;
        }
        .fh-flow {
            margin-top: 0.95rem;
            color: #999999;
            font-size: 0.96rem;
            letter-spacing: 0.01em;
        }
        .fh-section {
            background: #f5f5f5;
            border: 1px solid #eeeeee;
            border-radius: 16px;
            padding: 28px;
            margin: 0 0 4rem 0;
        }
        .fh-section-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.45rem;
            font-weight: 700;
            color: #000000;
            margin-bottom: 0.4rem;
        }
        .fh-section-title::before {
            content: "";
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: #000000;
            flex: 0 0 auto;
        }
        .fh-section-desc {
            margin: 0 0 1.1rem 0;
            color: #666666;
            font-size: 0.98rem;
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e8e8e8;
            border-radius: 14px;
            padding: 16px 18px;
            box-shadow: none;
        }
        [data-testid="stMetricLabel"] {
            color: #666666;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: #000000;
        }
        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        div[data-baseweb="select"] > div {
            background: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 8px !important;
            color: #000000 !important;
            box-shadow: none !important;
        }
        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stDateInput input:focus {
            border-color: #000000 !important;
            box-shadow: 0 0 0 1px #000000 !important;
        }
        .stButton > button {
            width: 100%;
            min-height: 48px;
            border-radius: 8px;
            border: 1px solid #000000;
            background: #000000;
            color: #ffffff;
            font-size: 16px;
            font-weight: 600;
        }
        .stButton > button:hover {
            background: #222222;
            border-color: #222222;
            color: #ffffff;
        }
        .stDownloadButton > button {
            width: 100%;
            min-height: 44px;
            border-radius: 8px;
            border: 1px solid #d9d9d9;
            background: #ffffff;
            color: #000000;
            font-weight: 600;
        }
        .stDownloadButton > button:hover {
            background: #f3f3f3;
            color: #000000;
            border-color: #cccccc;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid #e5e5e5;
            border-radius: 14px;
            overflow: hidden;
            background: #ffffff;
        }
        .fh-table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin: 1.4rem 0 0.8rem 0;
            flex-wrap: wrap;
        }
        .fh-table-title {
            font-size: 1rem;
            font-weight: 700;
            color: #000000;
        }
        .fh-table-meta {
            font-size: 0.9rem;
            color: #999999;
        }
        .fh-top-posts {
            display: grid;
            gap: 10px;
            margin-top: 0.9rem;
        }
        .fh-top-post {
            background: #ffffff;
            border: 1px solid #e8e8e8;
            border-radius: 12px;
            padding: 14px 16px;
        }
        .fh-top-post-title {
            font-size: 0.98rem;
            font-weight: 700;
            color: #000000;
            margin-bottom: 6px;
        }
        .fh-top-post-meta {
            font-size: 0.9rem;
            color: #666666;
        }
        .fh-report-wrap {
            margin-top: 1.4rem;
        }
        .fh-report-toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 0.9rem;
            flex-wrap: wrap;
        }
        .fh-report-label {
            font-size: 0.9rem;
            color: #999999;
            letter-spacing: 0.01em;
        }
        .fh-report-card {
            background: #ffffff;
            border: 1px solid #e8e8e8;
            border-radius: 16px;
            padding: 24px;
        }
        .fh-report-card h1,
        .fh-report-card h2,
        .fh-report-card h3 {
            color: #000000;
            letter-spacing: -0.02em;
            margin-top: 1.2rem;
            margin-bottom: 0.7rem;
        }
        .fh-report-card h1 {
            font-size: 1.7rem;
            margin-top: 0;
        }
        .fh-report-card h2 {
            font-size: 1.25rem;
        }
        .fh-report-card h3 {
            font-size: 1.05rem;
        }
        .fh-report-card p,
        .fh-report-card li,
        .fh-report-card blockquote {
            color: #333333;
            font-size: 0.98rem;
            line-height: 1.8;
        }
        .fh-report-card ul,
        .fh-report-card ol {
            padding-left: 1.2rem;
        }
        .fh-report-card blockquote {
            margin: 1rem 0;
            padding-left: 1rem;
            border-left: 3px solid #d9d9d9;
            color: #666666;
        }
        .fh-report-card hr {
            border: none;
            border-top: 1px solid #ececec;
            margin: 1.2rem 0;
        }
        .fh-report-card code {
            background: #f5f5f5;
            border-radius: 6px;
            padding: 0.15rem 0.35rem;
            font-size: 0.92em;
        }
        .fh-report-actions {
            margin-top: 1rem;
        }
        .fh-footer {
            text-align: center;
            color: #999999;
            font-size: 0.88rem;
            padding-top: 0.5rem;
        }
        @media (max-width: 900px) {
            .block-container {
                padding-top: 2rem;
            }
            .fh-section {
                padding: 20px;
                margin-bottom: 3rem;
            }
            .fh-hero {
                margin-bottom: 3rem;
            }
        }
        @media (prefers-reduced-motion: reduce) {
            * {
                scroll-behavior: auto !important;
                transition: none !important;
                animation: none !important;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <section class="fh-hero">
        <h1 class="fh-brand">FeedbackHound</h1>
        <div class="fh-subtitle">反馈猎犬 · {APP_SLOGAN}</div>
        <div class="fh-slogan">每一条社区评论背后，都藏着一个产品机会。</div>
        <div class="fh-flow">抓取社区帖子 → 筛选观察信号 → 生成 AI 洞察</div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="fh-section">
        <div class="fh-section-title">抓取数据</div>
        <p class="fh-section-desc">输入 subreddit、时间范围和抓取数量，开始建立本次分析样本。</p>
    """,
    unsafe_allow_html=True,
)

subreddit = st.text_input("Subreddit 名称", placeholder="例如：openai")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("起始日期", value=None)
with col2:
    end_date = st.date_input("结束日期", value=None)

max_posts = st.number_input("最大抓取数量", min_value=1, max_value=MAX_POSTS_LIMIT, value=DEFAULT_MAX_POSTS, step=10)

if st.button("开始抓取", type="primary", use_container_width=True):
    if not subreddit.strip():
        st.error("请输入 subreddit 名称。")
    else:
        progress_bar = st.progress(0)
        status_box = st.empty()

        def update_progress(current: int, total: int) -> None:
            ratio = min(current / total, 1.0) if total else 0.0
            progress_bar.progress(ratio)

        def update_status(message: str) -> None:
            status_box.info(message)

        try:
            with st.status("准备抓取 Reddit 帖子", expanded=True) as status:
                reddit = initialize_reddit()
                status.write("Reddit 凭据加载并验证通过。")

                dataframe = fetch_posts(
                    reddit=reddit,
                    subreddit_name=subreddit.strip(),
                    start_date=start_date if isinstance(start_date, date) else None,
                    end_date=end_date if isinstance(end_date, date) else None,
                    max_posts=int(max_posts),
                    progress_callback=update_progress,
                    status_callback=update_status,
                )

                summary = {
                    "subreddit": subreddit.strip(),
                    "total_posts": int(len(dataframe)),
                    "start_date": start_date.isoformat() if start_date else "不限",
                    "end_date": end_date.isoformat() if end_date else "不限",
                }
                if not dataframe.empty:
                    summary["actual_time_range"] = f"{dataframe['post_time'].min()} ~ {dataframe['post_time'].max()}"
                else:
                    summary["actual_time_range"] = "无符合条件的数据"

                st.session_state["scraped_data"] = dataframe
                st.session_state["scrape_summary"] = summary
                st.session_state["analysis_report"] = ""
                st.session_state["analysis_markdown_name"] = ""
                st.session_state["analysis_pdf_error"] = ""
                status.update(label="抓取完成", state="complete")

            progress_bar.progress(1.0)
            st.success(f"抓取完成，共获得 {len(dataframe)} 条帖子。")
        except ScraperError as exc:
            progress_bar.progress(0)
            st.error(str(exc))
        except Exception as exc:
            progress_bar.progress(0)
            st.error(f"抓取过程中出现未预期错误：{exc}")

st.markdown("</section>", unsafe_allow_html=True)

dataframe = st.session_state.get("scraped_data")
summary = st.session_state.get("scrape_summary", {})

if dataframe is not None:
    st.markdown(
        """
        <section class="fh-section">
            <div class="fh-section-title">数据预览</div>
            <p class="fh-section-desc">先查看样本质量、关键词信号和热门帖子，再决定是否进一步交给 AI 分析。</p>
        """,
        unsafe_allow_html=True,
    )

    if dataframe.empty:
        st.info("当前抓取结果为空，请调整条件后重新抓取。")
    else:
        keyword = st.text_input("关键词搜索", placeholder="按标题或正文包含过滤")
        filtered = dataframe
        if keyword.strip():
            mask = (
                dataframe["title"].fillna("").str.contains(keyword, case=False, na=False, regex=False)
                | dataframe["content"].fillna("").str.contains(keyword, case=False, na=False, regex=False)
            )
            filtered = dataframe[mask].copy()

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("总帖子数", int(len(filtered)))
        col_b.metric("平均 Score", f"{filtered['score'].mean():.1f}" if not filtered.empty else "0.0")
        col_c.metric("平均评论数", f"{filtered['num_comments'].mean():.1f}" if not filtered.empty else "0.0")

        st.caption(
            f"当前社区：r/{summary.get('subreddit', '-')} | 抓取时间范围：{summary.get('actual_time_range', '-')}"
        )

        st.markdown(
            f"""
<div class="fh-table-header">
    <div class="fh-table-title">帖子明细</div>
    <div class="fh-table-meta">当前结果 {len(filtered)} 条</div>
</div>
            """,
            unsafe_allow_html=True,
        )

        display_dataframe = filtered.copy()
        display_dataframe["content"] = display_dataframe["content"].fillna("").apply(
            lambda text: text if len(text) <= 100 else f"{text[:100]}…"
        )

        st.dataframe(
            display_dataframe[["post_time", "title", "content", "author", "score", "num_comments", "url"]],
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Top 5 热门帖子")
        top_posts = filtered.sort_values(["score", "num_comments"], ascending=False).head(5)
        if top_posts.empty:
            st.info("当前筛选条件下没有可展示的帖子。")
        else:
            top_post_cards = []
            for row in top_posts.itertuples(index=False):
                top_post_cards.append(
                    f"""
<div class="fh-top-post">
    <div class="fh-top-post-title">{row.title}</div>
    <div class="fh-top-post-meta">Score {row.score} · 评论 {row.num_comments} · 时间 {row.post_time}</div>
</div>
                    """
                )
            st.markdown(
                f"<div class='fh-top-posts'>{''.join(top_post_cards)}</div>",
                unsafe_allow_html=True,
            )

        csv_bytes = dataframe_to_csv_bytes(filtered)
        excel_bytes = dataframe_to_excel_bytes(filtered)

        download_col1, download_col2 = st.columns(2)
        download_col1.download_button(
            "下载 CSV",
            data=csv_bytes,
            file_name="feedbackhound_posts.csv",
            mime="text/csv",
            use_container_width=True,
        )
        download_col2.download_button(
            "下载 Excel",
            data=excel_bytes,
            file_name="feedbackhound_posts.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.markdown("</section>", unsafe_allow_html=True)

    st.markdown(
        """
        <section class="fh-section">
            <div class="fh-section-title">AI 分析</div>
            <p class="fh-section-desc">确认样本后，再接入 AI 服务商，将反馈整理成结构化中文洞察报告。</p>
        """,
        unsafe_allow_html=True,
    )

    st.selectbox("AI 服务商", AI_PROVIDER_OPTIONS, key="ai_provider")
    st.text_input("AI API Key", key="ai_api_key", type="password")

    provider_label = st.session_state.get("ai_provider", "OpenAI")
    provider = SUPPORTED_AI_PROVIDERS.get(provider_label, "")
    api_key = st.session_state.get("ai_api_key", "")
    analysis_type = st.radio("分析方向", ["竞品分析", "内容运营助手"], horizontal=True)
    analysis_subreddit = summary.get("subreddit", dataframe["subreddit"].iloc[0] if not dataframe.empty else "")

    prompt = ""
    report_title = ""
    report_subtitle = f"社区：r/{analysis_subreddit} | 服务商：{provider_label}"

    if analysis_type == "竞品分析":
        user_brand = st.text_input("你的产品/品牌名称")
        competitor_brand = st.text_input("竞品名称")
        prompt = COMPETITOR_ANALYSIS_PROMPT.format(
            subreddit=analysis_subreddit,
            user_brand=user_brand.strip() or "未提供",
            competitor_brand=competitor_brand.strip() or "未提供",
            data_summary="{data_summary}",
        )
        report_title = "FeedbackHound 竞品分析报告"
    else:
        user_brand = st.text_input("你的品牌名称")
        target_audience = st.text_input("目标受众描述")
        prompt = CONTENT_OPERATIONS_PROMPT.format(
            subreddit=analysis_subreddit,
            user_brand=user_brand.strip() or "未提供",
            target_audience=target_audience.strip() or "未提供",
            data_summary="{data_summary}",
        )
        report_title = "FeedbackHound 内容运营洞察报告"

    if st.button("生成分析报告", type="primary", use_container_width=True):
        try:
            if analysis_type == "竞品分析" and (not user_brand.strip() or not competitor_brand.strip()):
                raise AIAnalyzerError("请填写你的产品/品牌名称和竞品名称。")
            if analysis_type == "内容运营助手" and (not user_brand.strip() or not target_audience.strip()):
                raise AIAnalyzerError("请填写你的品牌名称和目标受众描述。")

            with st.spinner("正在生成分析报告，请稍候…"):
                data_summary = build_data_summary(dataframe, analysis_subreddit)
                final_prompt = prompt.format(data_summary=data_summary)
                result = call_ai_api(provider, api_key, final_prompt, "")
                markdown_report = build_markdown_report(report_title, report_subtitle, result)
                st.session_state["analysis_report"] = markdown_report
                st.session_state["analysis_markdown_name"] = generate_report_filename("report", "md")
                st.session_state["analysis_pdf_error"] = ""
            st.success("分析完成。")
        except AIAnalyzerError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"生成报告时出现未预期错误：{exc}")

    report = st.session_state.get("analysis_report", "")
    if report:
        st.markdown(
            """
<div class="fh-report-wrap">
    <div class="fh-report-toolbar">
        <div class="fh-report-label">AI 生成结果 · 可继续下载 Markdown 或 PDF</div>
    </div>
</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div class='fh-report-card'>", unsafe_allow_html=True)
        st.markdown(report)
        st.markdown("</div>", unsafe_allow_html=True)

        markdown_name = st.session_state.get("analysis_markdown_name") or generate_report_filename("report", "md")
        pdf_name = generate_report_filename("report", "pdf")

        st.markdown("<div class='fh-report-actions'>", unsafe_allow_html=True)
        report_col1, report_col2 = st.columns(2)
        report_col1.download_button(
            "下载 Markdown",
            data=markdown_to_bytes(report),
            file_name=markdown_name,
            mime="text/markdown",
            use_container_width=True,
        )

        try:
            pdf_bytes = markdown_to_pdf_bytes(report)
            report_col2.download_button(
                "下载 PDF",
                data=pdf_bytes,
                file_name=pdf_name,
                mime="application/pdf",
                use_container_width=True,
            )
        except ReportGenerationError as exc:
            st.session_state["analysis_pdf_error"] = str(exc)
            report_col2.button("下载 PDF", disabled=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.get("analysis_pdf_error"):
            st.warning(st.session_state["analysis_pdf_error"])

    st.markdown("</section>", unsafe_allow_html=True)

st.markdown("<div class='fh-footer'>© 2025 FeedbackHound · Built for product teams</div>", unsafe_allow_html=True)

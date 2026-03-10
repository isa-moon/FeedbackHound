# FeedbackHound

FeedbackHound 是一个基于 Streamlit 的轻量 MVP，用于抓取 Reddit 社区帖子、预览与导出数据，并结合用户自行提供的 AI API Key 生成结构化中文分析报告。

开箱即用：https://feedbackhound.streamlit.app

## 功能概览

- 抓取指定 subreddit 的帖子数据
- 基于关键词搜索标题与正文
- 预览数据并导出 CSV / Excel
- 支持 OpenAI、Anthropic、DeepSeek 三种 AI 服务商
- 生成竞品分析或内容运营洞察报告
- 支持 Markdown 下载，若本机安装 wkhtmltopdf 则可导出 PDF

## 使用流程

1. 打开首页，填写 subreddit、日期范围和抓取数量后开始抓取（Reddit API 凭证已内置，开箱即用）
2. 在同一页面直接查看数据预览、关键词搜索、统计卡片和导出按钮
3. 如需分析，再在页面下方填写 AI 服务商与 API Key，生成结构化中文报告并下载

## 安装步骤

```bash
pip install -r requirements.txt
```

## Reddit API 抓取帖子说明

本项目已内置 Reddit API 凭证，来自开源项目 [KungfuSnail/reddit_data_collector](https://github.com/KungfuSnail/reddit_data_collector)（Unlicense 协议），无需自行申请即可直接使用。

如遇到 API 速率限制或内置凭证失效，你也可以自行申请：

1. 打开 Reddit 应用管理页面：`https://www.reddit.com/prefs/apps`
2. 点击 `create another app...`
3. 选择 `script` 类型
4. 填写应用名称与重定向地址（例如 `http://localhost:8080`）
5. 创建后获取 `client_id`、`client_secret`
6. 自定义一个 `user_agent`，例如：`python:feedbackhound:v1.0 (by /u/yourname)`

然后替换代码中对应的值即可。

## 运行方式

在 `feedbackhound/` 目录下执行：

```bash
streamlit run app.py
```

## 环境变量配置

本项目已内置 Reddit API 凭证，默认无需配置。如需替换为自己的凭证，可在 `feedbackhound/` 目录下创建 `.env` 文件：

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=python:feedbackhound:v1.0 (by /u/yourname)
```

## PDF 导出说明

PDF 导出依赖本机安装 `wkhtmltopdf`。如果未安装，应用会保留 Markdown 下载，并提示 PDF 暂不可用。

## 安全说明

- AI API Key 仅保存在当前会话中，不会写入磁盘
- 应用不会在错误信息中打印 API Key
- 页面刷新后需重新填写 AI API Key

## 示例

<img width="2574" height="1616" alt="微信图片_20260311004228_1444_8" src="https://github.com/user-attachments/assets/6f20e891-6d79-43cc-9e9e-9516534f1c87" />

<img width="2574" height="1616" alt="微信图片_20260311005731_1454_8" src="https://github.com/user-attachments/assets/47d672d7-d0f8-4a39-b21b-984994e474de" />

<img width="2574" height="1616" alt="微信图片_20260311005722_1453_8" src="https://github.com/user-attachments/assets/4a3ace26-47ef-4a54-b750-af6cc7163205" />

<img width="2574" height="1616" alt="微信图片_20260311005714_1452_8" src="https://github.com/user-attachments/assets/25e091fd-668d-4981-a3cf-ef24a341ce0f" />

竞品分析版：

<img width="2574" height="1616" alt="微信图片_20260311005704_1451_8" src="https://github.com/user-attachments/assets/14ead565-c2d9-4204-8463-43dd9f4dfc26" />

<img width="2574" height="1616" alt="微信图片_20260311004706_1450_8" src="https://github.com/user-attachments/assets/2a8ff92e-d732-4c9b-9fa6-bc6737671ae6" />

内容运营助手版：

<img width="2574" height="1616" alt="微信图片_20260311004650_1449_8" src="https://github.com/user-attachments/assets/a9802b72-f2b0-4eeb-a075-e05928419d1b" />

<img width="2574" height="1616" alt="微信图片_20260311004551_1448_8" src="https://github.com/user-attachments/assets/d1d73307-f3d5-4b67-87a1-3d41031408cf" />

<img width="2574" height="1616" alt="微信图片_20260311004454_1447_8" src="https://github.com/user-attachments/assets/a34c8b1b-dca6-4e6d-be91-feb38ac171ec" />

<img width="2574" height="1616" alt="微信图片_20260311004437_1446_8" src="https://github.com/user-attachments/assets/8aabcecd-54dd-4785-9175-d566dc9289f1" />

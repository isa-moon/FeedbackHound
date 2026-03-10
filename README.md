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

<img width="2574" height="1616" alt="微信图片_20260311004228_1444_8" src="https://github.com/user-attachments/assets/23958e28-9ac0-4c33-9f02-85674fae26f0" />

<img width="2574" height="1616" alt="微信图片_20260311004437_1446_8" src="https://github.com/user-attachments/assets/145abe8d-7b6e-44af-885e-a09cbb6bd684" />

<img width="2574" height="1616" alt="微信图片_20260311004454_1447_8" src="https://github.com/user-attachments/assets/c0323917-1d27-48a0-a442-91e279938784" />

<img width="2574" height="1616" alt="微信图片_20260311004551_1448_8" src="https://github.com/user-attachments/assets/ea5f3d38-3bbf-40a5-a75b-8b17b0c4ae06" />


竞品分析：

<img width="2574" height="1616" alt="微信图片_20260311004650_1449_8" src="https://github.com/user-attachments/assets/e3a961c3-f3d0-4275-bc5d-1f9b54005d69" />

<img width="2574" height="1616" alt="微信图片_20260311004706_1450_8" src="https://github.com/user-attachments/assets/1c3714ba-6918-4392-934f-66f533396a9f" />

内容运营助手：

<img width="2574" height="1616" alt="微信图片_20260311005704_1451_8" src="https://github.com/user-attachments/assets/7fc278ec-c1fd-402b-aee6-5c5211192921" />

<img width="2574" height="1616" alt="微信图片_20260311005714_1452_8" src="https://github.com/user-attachments/assets/c1329d5c-6d4a-4615-a915-53994f6f9869" />

<img width="2574" height="1616" alt="微信图片_20260311005722_1453_8" src="https://github.com/user-attachments/assets/e60be482-7de4-4aae-9e91-adb5403773f9" />

<img width="2574" height="1616" alt="微信图片_20260311005731_1454_8" src="https://github.com/user-attachments/assets/b6cd1c78-2c57-48d2-9d3f-2c5b2c96c322" />

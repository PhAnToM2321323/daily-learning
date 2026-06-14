# 每日学习 App（网页版）

每天展示四类学习内容：
1. 推理思路训练（含详细推理步骤，点击展开）
2. AI 新闻摘要（自动网络搜索当日新闻）
3. 金融知识点
4. 粤语知识

## 文件说明

```
daily-learning-app/
├── index.html              网页（打开即可查看）
├── generate_daily.py       生成当日内容的脚本
├── daily_content.json       内容数据（脚本生成，index.html 读取）
└── .github/workflows/daily.yml   GitHub Actions 自动定时任务
```

---

## 方式一：本地手动使用（最简单，先体验）

### 1. 安装依赖
```bash
pip install anthropic
```

### 2. 设置 API Key
去 https://console.anthropic.com/ 注册并创建一个 API Key，然后：

```bash
# macOS / Linux
export ANTHROPIC_API_KEY="你的key"

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="你的key"
```

### 3. 生成今天的内容
```bash
python generate_daily.py
```
运行成功后会生成/覆盖 `daily_content.json`。

### 4. 打开网页
直接双击 `index.html` 在浏览器打开即可看到当天内容。

> 之后每天打开网页前，重新运行一次 `python generate_daily.py` 即可更新内容。
> 可以设置一个本机定时任务（如 macOS/Linux 的 cron 或 Windows 的「任务计划程序」）每天早上自动执行这个命令。

---

## 方式二：全自动 + 网页托管（推荐，免维护）

利用 GitHub Actions 每天自动生成内容，并用 GitHub Pages 免费托管网页，
你每天打开同一个网址即可看到当天最新内容。

### 步骤

1. **创建 GitHub 仓库**
   在 GitHub 新建一个仓库（例如 `daily-learning`），把本文件夹中所有文件
   （包括隐藏的 `.github` 文件夹）上传/推送到该仓库。

2. **添加 API Key 到仓库密钥**
   仓库页面 → Settings → Secrets and variables → Actions → New repository secret
   - Name: `ANTHROPIC_API_KEY`
   - Value: 你的 Anthropic API Key

3. **开启 GitHub Pages**
   仓库页面 → Settings → Pages → Source 选择 `Deploy from a branch`，
   分支选 `main`，目录选 `/ (root)`，保存。
   稍等几分钟后会得到一个网址，例如：
   `https://你的用户名.github.io/daily-learning/`

4. **测试自动任务**
   仓库页面 → Actions → 选择「每日生成学习内容」→ 点击 `Run workflow` 手动跑一次，
   确认 `daily_content.json` 被成功更新（会看到一个新的 commit）。

5. **完成**
   之后每天 GitHub Actions 会在北京/香港时间早上 7 点自动运行，
   更新 `daily_content.json` 并提交到仓库，GitHub Pages 网页会自动同步显示最新内容。
   你每天打开同一个网址即可。

---

## 自定义

- **修改推送时间**：编辑 `.github/workflows/daily.yml` 中的 `cron` 表达式（使用 UTC 时间）。
- **调整内容主题/难度**：编辑 `generate_daily.py` 中各个 `gen_xxx()` 函数里的 prompt 文字，
  例如可以指定"金融知识请偏重港股/美股""推理题难度提高"等。
- **更换 AI 模型**：修改 `generate_daily.py` 顶部的 `MODEL` 变量。

## 常见问题

- **网页显示"找不到 daily_content.json"**：说明还没运行过 `generate_daily.py`，
  或者 `daily_content.json` 和 `index.html` 不在同一目录。
- **API 调用报错/超出额度**：检查 Anthropic 账户余额与 API Key 是否正确。
- **想换成 Telegram/邮件推送**：当前为网页方案；如需主动推送，
  可以在 `generate_daily.py` 生成内容后，额外调用 Telegram Bot API 或 SMTP 发送邮件，
  我可以在需要时帮你补充这部分代码。

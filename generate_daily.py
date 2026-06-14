"""
每日学习内容生成脚本
功能：调用 Anthropic Claude API，生成当天的：
  1. 推理思路训练题（含详细推理过程）
  2. AI 新闻摘要（含网络搜索获取最新资讯）
  3. 金融知识点
  4. 粤语知识

输出：daily_content.json （供 index.html 读取展示）

使用前准备：
  1. pip install anthropic
  2. 设置环境变量 ANTHROPIC_API_KEY=你的key
     (https://console.anthropic.com/ 申请)
  3. 运行: python generate_daily.py
"""

import os
import json
import datetime
import anthropic

MODEL = "claude-sonnet-4-6"
OUTPUT_FILE = "daily_content.json"

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)


def ask_claude(prompt: str, use_web_search: bool = False) -> str:
    """调用 Claude，返回纯文本内容"""
    kwargs = {
        "model": MODEL,
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
    }
    if use_web_search:
        kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]

    response = client.messages.create(**kwargs)

    # 拼接所有文本块（web_search 模式下可能有多个 text block）
    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts).strip()


def gen_reasoning():
    """生成推理思路训练题"""
    prompt = """请生成一道适合每日训练的逻辑推理题（可以是数学谜题、逻辑悖论、福尔摩斯式案例分析、
费米估算题或商业案例推理中的任意一种，每天尽量种类不同）。

请用纯 JSON 格式输出（不要markdown代码块标记），结构如下：
{
  "title": "题目标题",
  "question": "题目描述",
  "hints": ["提示1", "提示2"],
  "reasoning_steps": ["推理步骤1", "推理步骤2", "推理步骤3", "..."],
  "answer": "最终答案",
  "takeaway": "这道题训练的思维方式/可迁移的推理技巧（一两句话）"
}
"""
    text = ask_claude(prompt)
    return safe_json(text)


def gen_ai_news():
    """生成今日AI新闻摘要（使用网络搜索）"""
    today = datetime.date.today().strftime("%Y年%m月%d日")
    prompt = f"""今天是{today}。请搜索今天或最近一两天的 AI 行业重要新闻
（模型发布、公司动态、技术突破、政策法规等），挑选3-5条最重要的，
用中文为每条写一段50-100字的摘要说明意义。

请用纯 JSON 格式输出（不要markdown代码块标记），结构如下：
{{
  "date": "{today}",
  "items": [
    {{"headline": "新闻标题", "summary": "摘要说明", "source": "来源名称"}}
  ]
}}
"""
    text = ask_claude(prompt, use_web_search=True)
    return safe_json(text)


def gen_finance():
    """生成金融知识点"""
    prompt = """请生成一个适合每日学习的金融知识点（涵盖投资、宏观经济、公司财务、
金融市场、估值方法、风险管理等任意领域，每天尽量不重复主题）。

请用纯 JSON 格式输出（不要markdown代码块标记），结构如下：
{
  "concept": "概念名称（中英对照）",
  "explanation": "通俗易懂的解释，200字左右",
  "example": "一个具体例子或案例帮助理解",
  "common_misunderstanding": "常见误解或容易混淆的点",
  "related_terms": ["相关术语1", "相关术语2"]
}
"""
    text = ask_claude(prompt)
    return safe_json(text)


def gen_cantonese():
    """生成粤语知识"""
    prompt = """请生成一个适合每日学习的粤语知识点（可以是常用口语表达、俚语、
粤语特有词汇、与普通话差异较大的说法等，每天不重复）。

请用纯 JSON 格式输出（不要markdown代码块标记），结构如下：
{
  "phrase": "粤语表达（汉字）",
  "jyutping": "粤拼注音",
  "meaning": "意思解释",
  "example_sentence": "粤语例句（汉字）",
  "example_translation": "例句的普通话翻译",
  "usage_note": "使用场景或文化背景小知识"
}
"""
    text = ask_claude(prompt)
    return safe_json(text)


def safe_json(text: str):
    """尝试解析 JSON，去除可能的 markdown 代码块标记"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"raw_text": text, "parse_error": True}


def main():
    today_str = datetime.date.today().isoformat()
    print(f"正在生成 {today_str} 的每日学习内容...")

    content = {
        "date": today_str,
        "reasoning": gen_reasoning(),
        "ai_news": gen_ai_news(),
        "finance": gen_finance(),
        "cantonese": gen_cantonese(),
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    print(f"已生成 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

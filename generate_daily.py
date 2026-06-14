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
        "max_tokens": 4000,
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

目标读者是完全没有相关背景的初学者，所以推理步骤要写得非常详细、循序渐进，
每一步都要说明"为什么这样想"、用到了什么思考方法，让读者读完后真正学会
一种可以用在其他问题上的思维方式，而不是只看到一个孤立的答案。

请用纯 JSON 格式输出（不要markdown代码块标记），结构如下：
{
  "title": "题目标题",
  "question": "题目描述（背景信息要交代清楚，确保新手能理解题意）",
  "hints": ["提示1", "提示2"],
  "reasoning_steps": [
    "第一步：先点明这一步在'排除什么/聚焦什么'，再给出具体分析，2-3句话",
    "第二步：同样格式，承接上一步的结论继续推进，2-3句话",
    "...每一步都要像在给一个第一次接触这类问题的人讲解，不要跳步"
  ],
  "answer": "最终答案，并用一句话总结整个推理链条",
  "takeaway": "这道题训练的思维方式/可迁移的推理技巧，至少3句话，
    要说明：这个技巧叫什么名字、它的核心思路是什么、还能用在生活/工作中的什么场景"
}
"""
    text = ask_claude(prompt)
    return safe_json(text)


def gen_ai_news():
    """生成今日AI新闻摘要（使用网络搜索）"""
    today = datetime.date.today().strftime("%Y年%m月%d日")
    prompt = f"""今天是{today}。请搜索今天或最近一两天的 AI 行业重要新闻
（模型发布、公司动态、技术突破、政策法规等），挑选3-5条最重要的。

目标读者是对 AI 行业不太熟悉的初学者，所以每条新闻除了说明"发生了什么"，
还要补充背景知识帮助理解：涉及的公司/技术是做什么的、这个新闻为什么重要、
对普通人或行业可能带来什么影响。避免直接堆砌专业术语，如果用到术语要简单解释。

请用纯 JSON 格式输出（不要markdown代码块标记），结构如下：
{{
  "date": "{today}",
  "items": [
    {{
      "headline": "新闻标题",
      "background": "背景知识：简单介绍涉及的公司/技术/概念是什么（1-2句话）",
      "summary": "发生了什么事（2-3句话，说清楚具体内容）",
      "why_it_matters": "为什么重要：对行业或普通人意味着什么（2-3句话）",
      "source": "来源名称"
    }}
  ]
}}

如果搜索没有返回任何相关内容，请仍然按上述格式输出，
items 可以基于你已知的近期重要 AI 趋势话题，但要在 summary 开头注明"（基于已知信息，非当日最新）"。
"""
    text = ask_claude(prompt, use_web_search=True)
    return safe_json(text)


def gen_finance():
    """生成金融知识点"""
    prompt = """请生成一个适合每日学习的金融知识点（涵盖投资、宏观经济、公司财务、
金融市场、估值方法、风险管理等任意领域，每天尽量不重复主题）。

目标读者是金融零基础的初学者，所以讲解要做到：
1）先用一个生活中的类比帮助建立直觉，再给出正式定义；
2）用具体数字举例，一步步演算，让读者能跟着算一遍；
3）说明这个知识点在现实中具体用在什么场景（比如买股票/看新闻/管理个人财务时会用到）；
4）指出初学者最容易搞错的地方，并解释为什么会搞错。

请用纯 JSON 格式输出（不要markdown代码块标记），结构如下：
{
  "concept": "概念名称（中英对照）",
  "analogy": "生活化类比，帮助建立直觉，2-3句话",
  "explanation": "正式解释，包含定义和原理，150-250字",
  "example": "具体数字例子，分步骤演算，让读者能跟着计算理解",
  "real_world_use": "现实中什么场景会用到这个知识点，举1-2个具体情境",
  "common_misunderstanding": "初学者常见误解，并解释为什么容易搞错",
  "related_terms": ["相关术语1", "相关术语2", "相关术语3"]
}
"""
    text = ask_claude(prompt)
    return safe_json(text)


def gen_cantonese():
    """生成粤语知识"""
    prompt = """请生成一个适合每日学习的粤语知识点（可以是常用口语表达、俚语、
粤语特有词汇、与普通话差异较大的说法等，每天不重复）。

目标读者完全不懂粤语，所以要做到：
1）逐字拆解发音和含义，不要只给整体翻译；
2）说明这个表达和普通话直译的差异在哪里（如果直译会很奇怪，要解释为什么）；
3）给出至少2个不同场景的例句，让读者感受用法的灵活性；
4）补充相关的文化背景或常见搭配，帮助记忆。

请用纯 JSON 格式输出（不要markdown代码块标记），结构如下：
{
  "phrase": "粤语表达（汉字）",
  "jyutping": "粤拼注音（整体）",
  "char_breakdown": "逐字解释，格式如'唔(m4,不) + 使(sai2,需要) = 不需要'",
  "meaning": "整体意思解释",
  "literal_vs_actual": "如果直译成普通话会有什么差异或显得奇怪，解释为什么这么说",
  "examples": [
    {"sentence": "粤语例句1", "translation": "普通话翻译1", "context": "使用场景说明"},
    {"sentence": "粤语例句2", "translation": "普通话翻译2", "context": "使用场景说明"}
  ],
  "usage_note": "文化背景、常见搭配或记忆小technique"
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

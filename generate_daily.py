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
HISTORY_FILE = "topics_history.json"
HISTORY_LIMIT = 30  # 每个类别最多记住最近30个主题，避免文件无限增长、prompt无限变长

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)


def load_history() -> dict:
    """读取历史主题记录，格式：{"reasoning": [...], "finance": [...], "cantonese": [...]}"""
    if not os.path.exists(HISTORY_FILE):
        return {"reasoning": [], "finance": [], "cantonese": []}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in ("reasoning", "finance", "cantonese"):
            data.setdefault(key, [])
        return data
    except (json.JSONDecodeError, OSError):
        return {"reasoning": [], "finance": [], "cantonese": []}


def save_history(history: dict) -> None:
    """保存历史主题记录，每个类别只保留最近 HISTORY_LIMIT 条"""
    trimmed = {k: v[-HISTORY_LIMIT:] for k, v in history.items()}
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)


def history_block(topics: list) -> str:
    """把历史主题列表拼成一段可以插入prompt的文字，列表为空时返回空字符串"""
    if not topics:
        return ""
    joined = "、".join(topics)
    return f"\n\n【避免重复】以下主题最近已经讲过，请这次换一个完全不同的主题，不要重复或只是小幅变体：\n{joined}\n"


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


def gen_reasoning(history_topics: list):
    """生成推理思路训练题"""
    prompt = """请生成一道适合每日训练的逻辑推理题（可以是数学谜题、逻辑悖论、福尔摩斯式案例分析、
费米估算题或商业案例推理中的任意一种，每天尽量种类不同）。

目标读者是完全没有相关背景的初学者，所以推理步骤要写得非常详细、循序渐进，
每一步都要说明"为什么这样想"、用到了什么思考方法，让读者读完后真正学会
一种可以用在其他问题上的思维方式，而不是只看到一个孤立的答案。
""" + history_block(history_topics) + """
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

【重要格式要求】这是一个JSON字符串值，如果你需要在文字中强调某个词或引用，
请使用中文书名号或单引号（如 『xxx』 或 'xxx'），绝对不要使用英文双引号 " 来包裹强调内容，
因为双引号会破坏JSON格式导致解析失败。
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

【重要格式要求】最终回复必须只包含纯 JSON 内容本身，不要有任何开场白
（例如"好的，我已经搜索到了"之类的句子），不要用 markdown 代码块包裹（不要加三个反引号加json或三个反引号），
直接以左花括号开头、以右花括号结尾。如果你需要在文字中强调某个词或引用原文，
请使用中文书名号或单引号（如 『xxx』 或 'xxx'），绝对不要使用英文双引号 " 来包裹强调内容，
因为双引号会破坏JSON格式导致解析失败。
"""
    text = ask_claude(prompt, use_web_search=True)
    return safe_json(text)


def gen_finance(history_topics: list):
    """生成金融知识点"""
    prompt = """请生成一个适合每日学习的金融知识点（涵盖投资、宏观经济、公司财务、
金融市场、估值方法、风险管理等任意领域，每天尽量不重复主题）。

目标读者是金融零基础的初学者，所以讲解要做到：
1）先用一个生活中的类比帮助建立直觉，再给出正式定义；
2）用具体数字举例，一步步演算，让读者能跟着算一遍；
3）说明这个知识点在现实中具体用在什么场景（比如买股票/看新闻/管理个人财务时会用到）；
4）指出初学者最容易搞错的地方，并解释为什么会搞错。
""" + history_block(history_topics) + """
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

【重要格式要求】这是一个JSON字符串值，如果你需要在解释文字中强调某个词或引用，
请使用中文书名号或单引号（如 『xxx』 或 'xxx'），绝对不要使用英文双引号 " 来包裹强调内容，
因为双引号会破坏JSON格式导致解析失败。
"""
    text = ask_claude(prompt)
    return safe_json(text)


def gen_cantonese(history_topics: list):
    """生成粤语知识"""
    prompt = """请生成一个适合每日学习的粤语知识点（可以是常用口语表达、俚语、
粤语特有词汇、与普通话差异较大的说法等，每天不重复）。

目标读者完全不懂粤语，所以要做到：
1）逐字拆解发音和含义，不要只给整体翻译；
2）说明这个表达和普通话直译的差异在哪里（如果直译会很奇怪，要解释为什么）；
3）给出至少2个不同场景的例句，让读者感受用法的灵活性；
4）补充相关的文化背景或常见搭配，帮助记忆。
""" + history_block(history_topics) + """
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

【重要格式要求】这是一个JSON字符串值，如果你需要在文字中强调某个词或引用，
请使用中文书名号或单引号（如 『xxx』 或 'xxx'），绝对不要使用英文双引号 " 来包裹强调内容，
因为双引号会破坏JSON格式导致解析失败。
"""
    text = ask_claude(prompt)
    return safe_json(text)


def safe_json(text: str):
    """尝试解析 JSON，去除可能的 markdown 代码块标记和前后多余文字，
    并对常见的'字符串内部出现未转义双引号'问题做自动修复尝试"""
    cleaned = text.strip()

    # 优先尝试：提取 ```json ... ``` 或 ``` ... ``` 代码块内的内容
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            if candidate.startswith("{") or candidate.startswith("["):
                cleaned = candidate
                break

    # 如果还是不是以 { 或 [ 开头，找到第一个 { 和最后一个 } 之间的内容
    if not (cleaned.startswith("{") or cleaned.startswith("[")):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end + 1]

    # 第一次尝试：直接解析
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 第二次尝试：自动修复模型在字符串值内部误用未转义双引号的问题
    # 用状态机逐字符扫描：只有紧跟在 , { [ : 之后的引号才是字符串"开始"，
    # 字符串内部再次出现引号时，看其后第一个非空白字符是否为 , } ] :
    # 如果不是，说明这是字符串内部的引号（如中文强调用的"xxx"），应转义而非当作结束符
    def repair_unescaped_quotes(s: str) -> str:
        out = []
        i, n = 0, len(s)
        in_string = False
        escape = False
        while i < n:
            ch = s[i]
            if in_string:
                if escape:
                    out.append(ch)
                    escape = False
                    i += 1
                    continue
                if ch == '\\':
                    out.append(ch)
                    escape = True
                    i += 1
                    continue
                if ch == '"':
                    j = i + 1
                    while j < n and s[j] in ' \t\r\n':
                        j += 1
                    next_char = s[j] if j < n else ''
                    if next_char in (',', '}', ']', ':') or j >= n:
                        out.append(ch)
                        in_string = False
                    else:
                        out.append('\\"')
                    i += 1
                    continue
                out.append(ch)
                i += 1
            else:
                if ch == '"':
                    in_string = True
                out.append(ch)
                i += 1
        return ''.join(out)

    try:
        repaired = repair_unescaped_quotes(cleaned)
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    return {"raw_text": text, "parse_error": True}


def extract_topic(result: dict, key: str) -> str | None:
    """从生成结果中提取本次的主题标识，用于记入历史。
    如果解析失败（parse_error），返回 None，不记录这次的主题。"""
    if not isinstance(result, dict) or result.get("parse_error"):
        return None
    return result.get(key)


def main():
    today_str = datetime.date.today().isoformat()
    print(f"正在生成 {today_str} 的每日学习内容...")

    history = load_history()

    reasoning = gen_reasoning(history["reasoning"])
    finance = gen_finance(history["finance"])
    cantonese = gen_cantonese(history["cantonese"])
    ai_news = gen_ai_news()  # 新闻是时效性内容，按当天真实事件生成，不需要去重

    content = {
        "date": today_str,
        "reasoning": reasoning,
        "ai_news": ai_news,
        "finance": finance,
        "cantonese": cantonese,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    # 更新历史主题记录，供下次生成时去重参考
    new_reasoning_topic = extract_topic(reasoning, "title")
    new_finance_topic = extract_topic(finance, "concept")
    new_cantonese_topic = extract_topic(cantonese, "phrase")

    if new_reasoning_topic:
        history["reasoning"].append(new_reasoning_topic)
    if new_finance_topic:
        history["finance"].append(new_finance_topic)
    if new_cantonese_topic:
        history["cantonese"].append(new_cantonese_topic)

    save_history(history)

    print(f"已生成 {OUTPUT_FILE}")
    print(f"已更新 {HISTORY_FILE}（用于下次去重）")


if __name__ == "__main__":
    main()

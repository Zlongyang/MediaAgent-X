"""LLM 唯一入口（契约 §7.2：chat() 是唯一入口，换模型/换 provider 不动业务代码）。

- 有 DEEPSEEK_API_KEY 且装了 langchain_openai → ChatOpenAI(base_url=deepseek)
- 否则自动降级 MockChat（确定性演示内容，离线可跑通全流程——冒烟测试依赖此特性）

MockChat 按 prompt 关键词路由到 mock_content 的确定性 fixture，
输出形状与真实 LLM 约定一致（结构化需求一律返回 JSON 字符串）。
"""
from __future__ import annotations

import json
import re
import warnings

from agent import config
from agent.tools import mock_content


def _mock_reply(user: str, system: str = "") -> str:
    text = f"{system}\n{user}"
    if "候选选题" in text or "热点扫描" in text:
        return json.dumps(mock_content.TOPIC_CANDIDATES, ensure_ascii=False)
    if "分镜" in text or "镜头表" in text:
        return json.dumps(mock_content.SHOTS, ensure_ascii=False)
    if "打包" in text or "标题" in text and "标签" in text:
        return json.dumps(mock_content.PACK_LLM_RESULT, ensure_ascii=False)
    if "复盘" in text:
        return mock_content.REVIEW_TEXT
    if "脚本" in text or "编剧" in text:
        return mock_content.SCRIPT_FULL
    return "收到，按总编要求执行。"


class MockChat:
    """确定性假 LLM：同样的输入永远给同样的输出。"""

    def invoke(self, messages: list[dict]) -> str:
        system = next((m["content"] for m in messages if m.get("role") == "system"), "")
        user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        return _mock_reply(user, system)


_chat_instance = None


def _build_chat():
    if config.has_llm_key():
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            warnings.warn("检测到 DEEPSEEK_API_KEY 但未安装 langchain_openai，降级 MockChat。")
            return MockChat()
        return ChatOpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
            model=config.DEEPSEEK_MODEL,
            temperature=0.7,
        )
    return MockChat()


def get_chat():
    """惰性单例：避免 import 时就触网/触包。"""
    global _chat_instance
    if _chat_instance is None:
        _chat_instance = _build_chat()
    return _chat_instance


def is_mock() -> bool:
    return isinstance(get_chat(), MockChat)


def chat(user: str, system: str = "") -> str:
    """全项目唯一 LLM 调用入口。返回纯文本（结构化需求由调用方 json.loads）。"""
    model = get_chat()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    result = model.invoke(messages)
    return getattr(result, "content", result)


def load_prompt(rel_path: str) -> str:
    """prompt 即文件：人设从 prompts/ 目录读取，用户可直接编辑。"""
    p = config.PROMPTS_DIR / rel_path
    try:
        return p.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


_JSON_BLOCK = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```")


def parse_llm_json(text: str):
    """解析 LLM 的结构化输出：容忍 ```json 围栏与首尾散文；空/截断/垃圾抛异常（调用方兜底）。

    MockChat 返回裸 JSON 走快路径；真实 LLM 偶尔加围栏或解释性文字时，
    提取首个 [...] 或 {...} 片段。提取层宽松，解析本身仍是严格 json.loads。
    """
    raw = (text or "").strip()
    if not raw:
        raise ValueError("LLM 返回为空")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = _JSON_BLOCK.search(raw)
    if m:
        return json.loads(m.group(1))
    start = min((i for i in (raw.find("["), raw.find("{")) if i >= 0), default=-1)
    if start >= 0:
        end = max(raw.rfind("]"), raw.rfind("}"))
        if end > start:
            return json.loads(raw[start : end + 1])
    raise ValueError(f"LLM 输出不含可解析 JSON：{raw[:80]!r}")


if __name__ == "__main__":
    assert parse_llm_json('[{"a":1}]') == [{"a": 1}]
    assert parse_llm_json('```json\n[{"a":1}]\n```') == [{"a": 1}]
    assert parse_llm_json('好的，结果是：\n[{"a":1}]\n以上。') == [{"a": 1}]
    assert parse_llm_json('{"k": "v"}') == {"k": "v"}
    for bad in ("", "没有 JSON", '[{"a":1'):
        try:
            parse_llm_json(bad)
            raise SystemExit(f"应当抛异常：{bad!r}")
        except (ValueError, json.JSONDecodeError):
            pass
    print("[PASS] llm.parse_llm_json 自测通过")

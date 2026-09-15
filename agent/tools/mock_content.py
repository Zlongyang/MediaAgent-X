"""离线确定性 fixture（契约 §7.2 tools/mock_content.py）。

形状与契约 §1/§4 及前端 web/src/data/mock.js 对齐：
- TOPIC_CANDIDATES：3 个选题候选 {title, source, heat, reason}
- SCRIPT_FULL / SCRIPT_EXCERPT：脚本与闸门节选
- SHOTS：分镜表 [{idx, narration, visual, search, duration}]
- PACK_*：打包结果 {platform, title, caption, tags[], titleLen, descLen}
冒烟测试全程离线可跑，不依赖任何 API key 与网络。
"""

# ---- trend_scan：3 个候选选题（契约 §1 #1） ----
TOPIC_CANDIDATES = [
    {
        "title": "百元降噪耳机横评：谁最能打？",
        "source": "抖音热榜 · 数码",
        "heat": "86.4w",
        "reason": "争议型对比天然带评论，近 7 天搜索量 +142%，且与账号既有粉丝画像高度重合。",
    },
    {
        "title": "我把手机换成了“老人机”用了 7 天",
        "source": "B站 · 科技区上升",
        "heat": "52.1w",
        "reason": "反差体验类内容 3s 留存高，制作成本低，适合快反；但同质化开始冒头，需要强钩子。",
    },
    {
        "title": "618 别乱买：桌面好物避雷清单",
        "source": "小红书 · 热点",
        "heat": "38.7w",
        "reason": "临近大促转化意图强，挂车收益高；风险是清单类同质化，需要“翻车实测”角度。",
    },
]

# ---- script_draft：脚本全文 + 闸门节选（契约 §1 #3） ----
SCRIPT_FULL = """# 百元降噪耳机横评：谁最能打？

[00:00-00:03] 钩子
画面：三款耳机同时摔在桌上，价格标签特写
台词：「100 块的降噪耳机，和 1000 块的，差距可能就一根线。」

[00:03-00:18] 冲突建立
画面：地铁通勤实测分屏
台词：「我把三款都戴上了早高峰的 2 号线，结果最贵的那款，第一个被我摘下来。」

[00:18-00:45] 横评三段：降噪 / 音质 / 佩戴
每段 9 秒，参数字幕条上屏：
- 降噪实测：三款波形对比，差距一目了然
- 音质环节：百元档里它是唯一没糊的
- 佩戴：连续 4 小时耳道压力测试

[00:45-00:58] 收尾 + 评论引导
台词：「预算两百内的答案我放评论区置顶，你站哪一款？说错了算我的。」
"""

SCRIPT_EXCERPT = """# 百元降噪耳机横评：谁最能打？（节选）

[00:00-00:03] 钩子
画面：三款耳机同时摔在桌上，价格标签特写
台词：「100 块的降噪耳机，和 1000 块的，差距可能就一根线。」

[00:03-00:18] 冲突建立
画面：地铁通勤实测分屏
台词：「我把三款都戴上了早高峰的 2 号线，
  结果最贵的那款，第一个被我摘下来。」

[00:18-00:45] 横评三段：降噪 / 音质 / 佩戴
...（每段 9 秒，参数字幕条上屏）

[00:45-00:58] 收尾 + 评论引导
台词：「预算两百内的答案我放评论区置顶，
  你站哪一款？说错了算我的。」"""

# ---- storyboard：镜头表（契约 §1 #5） ----
SHOTS = [
    {"idx": 1, "narration": "100 块的降噪耳机，和 1000 块的，差距可能就一根线。", "visual": "三款耳机摔在桌上，价格标签特写，手持晃动感", "search": "earbuds on desk price tag close up", "duration": "3s"},
    {"idx": 2, "narration": "我把三款都戴上了早高峰的 2 号线。", "visual": "地铁车厢内主观视角，人潮，降噪波形动画叠加", "search": "subway commute crowd pov", "duration": "6s"},
    {"idx": 3, "narration": "最贵的那款，第一个被我摘下来。", "visual": "摘下耳机特写，表情反差，字幕条弹出", "search": "take off earbuds close up", "duration": "4s"},
    {"idx": 4, "narration": "降噪实测：三款波形对比，差距在这里。", "visual": "三段分屏波形图，参数字幕条上屏", "search": "sound wave comparison graphic", "duration": "9s"},
    {"idx": 5, "narration": "音质环节，百元档里它是唯一没糊的。", "visual": "频谱仪画面 + 桌面静物旋转展示", "search": "audio spectrum product turntable", "duration": "9s"},
    {"idx": 6, "narration": "预算两百内的答案我放评论区置顶，你站哪一款？", "visual": "三款耳机全家福定格，点赞按钮动效", "search": "earbuds group shot studio light", "duration": "8s"},
]

# 素材搜索词（mpt_pipeline.terms 子任务，有序模式，对齐 SHOTS 顺序）
SEARCH_TERMS = [s["search"] for s in SHOTS]

# ---- packaging：打包结果（契约 §1 #8，形状 {platform,title,caption,tags[],titleLen,descLen}） ----
PACK_LLM_RESULT = {
    "title": "百元降噪耳机横评：最贵的那款我第一个摘了",
    "caption": "三款百元降噪耳机早高峰实测，结果最贵的那款第一个被我摘下来。答案在评论区置顶。",
    "hashtags": ["数码测评", "降噪耳机", "百元好物", "618"],
}
PACK_RESULT = {
    "platform": "抖音",
    "title": PACK_LLM_RESULT["title"],
    "caption": PACK_LLM_RESULT["caption"],
    "tags": PACK_LLM_RESULT["hashtags"],
    "titleLen": len(PACK_LLM_RESULT["title"]),
    "descLen": len(PACK_LLM_RESULT["caption"]),
}

# ---- publish：发布记录（无账号 → unpublished，见 stages/publish.py） ----
PUBLISH_RECORD = {
    "platform": "抖音",
    "video_id": "7312458801",
    "url": "https://www.douyin.com/video/7312458801",
    "status": "published",
}

# ---- monitoring：排期与快照（契约 §1 #11） ----
METRICS_SCHEDULE = ["T+1h", "T+6h", "T+24h", "T+7d"]
METRICS_SNAPSHOTS = [
    {"t": "T+1h", "play": 12480, "like": 936, "comment": 128, "share": 210},
    {"t": "T+6h", "play": 28940, "like": 2310, "comment": 402, "share": 560},
    {"t": "T+24h", "play": 51200, "like": 4020, "comment": 688, "share": 1140},
    {"t": "T+7d", "play": 63800, "like": 4720, "comment": 801, "share": 1420},
]

# ---- review：复盘（契约 §1 #12） ----
REVIEW_TIPS = [
    "建议修改 skills/爆款脚本.md 的钩子公式：前 3 秒把「价格冲突」前置为「反直觉结论」。",
    "评论区高频词是「链接」，下一轮简介栏固定挂清单索引。",
]
REVIEW_TEXT = """# 复盘报告 · 百元降噪耳机横评

## 数据结论
- T+7d 播放 63800，赞播比 7.4%，分享率高于账号均值 1.8 倍。
- 钩子留存：3s 留存 78%，「价格冲突前置」公式验证有效。

## 归因
- 争议型对比选题 + 实测分屏结构 → 评论率拉高。
- 第 3 镜头「摘下耳机」反差点是分享峰值来源。

## 下一轮行动
1. 钩子公式迭代：反直觉结论前置到第 1 句。
2. 简介栏固定挂清单索引，承接「链接」高频评论。
"""

# ---- mock 音视频物料占位内容（确定性字节） ----
MOCK_AUDIO_BYTES = b"MOCK-TTS-AUDIO\n" + ("百元降噪耳机横评配音占位\n".encode("utf-8"))
MOCK_SRT = """1
00:00:00,000 --> 00:00:03,000
100 块的降噪耳机，和 1000 块的，差距可能就一根线。

2
00:00:03,000 --> 00:00:09,000
我把三款都戴上了早高峰的 2 号线。

3
00:00:09,000 --> 00:00:13,000
最贵的那款，第一个被我摘下来。
"""
MOCK_VIDEO_BYTES = b"MOCK-VIDEO-MP4\nfinal composite placeholder\n"
MOCK_COVER_BYTES = bytes.fromhex("FFD8FFE0") + b"MOCK-COVER-JPEG\n" + bytes.fromhex("FFD9")

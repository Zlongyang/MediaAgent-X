// Central mock data for MediaAgent-X demo. All display-only.

export const ACCOUNTS = [
  { key: 'dy-shuma', label: '抖音 · 数码小X', platform: '抖音' },
  { key: 'bili-xiaox', label: 'B站 · 小X评测', platform: 'B站' },
]

export const NO_ACCOUNT = { key: 'none', label: '暂不选择 / 未安排', platform: '—' }

export const ACCOUNT_FANS = {
  'dy-shuma': '12.8w',
  'bili-xiaox': '3.4w',
}

export const STATUS = {
  generating: { label: '生成中', kind: 'business' },
  review: { label: '待审查', kind: 'warn' },
  unpublished: { label: '未发布', kind: 'success' },
  published: { label: '已发布', kind: 'neutral' },
  failed: { label: '生成失败', kind: 'error' },
}

const BASE_CONFIG = {
  ratio: '9:16',
  duration: '60s',
  count: 1,
  voice: '云希（青年男声）',
  voiceRate: '1.0x',
  voiceVol: '100%',
  bgm: { src: '卡点榜 · 轻快电子', vol: '20%' },
  subtitle: { size: '16px', color: '白色描边', pos: '底部 12%' },
  material: 'Pexels + AI 生成',
}

function cfg(patch) {
  return { ...BASE_CONFIG, ...patch, bgm: { ...BASE_CONFIG.bgm, ...(patch && patch.bgm) }, subtitle: { ...BASE_CONFIG.subtitle, ...(patch && patch.subtitle) } }
}

export function defaultConfig() {
  return cfg({})
}

const STAGE_ROWS = [
  // key, 阶段, 工种, icon, 耗时s, llm, material, tts, status
  ['trend_scan', 'trend_scan · 选题扫描', '选题猎手', 'target', 2.0, 0.12, 0, 0],
  ['gate_topic', '选题确认', '总编', null, null, 0, 0, 0],
  ['script_draft', 'script_draft · 脚本草稿', '编剧', 'pen', 2.5, 0.35, 0, 0],
  ['gate_script', '脚本确认', '总编', null, null, 0, 0, 0],
  ['storyboard', 'storyboard · 分镜设计', '分镜师', 'clapper', 2.0, 0.28, 0, 0],
  ['mpt_terms', 'mpt/terms · 提示词生成', '制片', 'factory', 1.5, 0.10, 0, 0],
  ['mpt_audio', 'mpt/audio · 配音合成', '制片', 'factory', 1.5, 0, 0, 1.20],
  ['mpt_subtitle', 'mpt/subtitle · 字幕生成', '制片', 'factory', 1.5, 0.08, 0, 0],
  ['mpt_materials', 'mpt/materials · 素材拉取', '制片', 'factory', 1.5, 0, 2.50, 0],
  ['mpt_video', 'mpt/video · 视频合成', '制片', 'factory', 1.5, 0, 0.60, 0],
  ['gate_preview', '成片预览', '总编', null, null, 0, 0, 0],
  ['packaging', 'packaging · 发布打包', '包装师', 'package', 2.0, 0.15, 0, 0],
  ['gate_publish', '发布确认', '总编', null, null, 0, 0, 0],
  ['publish', 'publish · 发布上线', '发行人', 'rocket', 1.5, 0.02, 0, 0],
  ['monitoring', 'monitoring · 数据回拉', '分析师', 'chart', 1.5, 0.05, 0, 0],
]

function stageRows(upto, failAt) {
  return STAGE_ROWS.map(([key, name, agent, icon, dur, llm, mat, tts], i) => {
    let status = 'done'
    if (failAt && key === failAt) status = 'failed'
    else if (upto != null && i > upto) status = 'pending'
    return { key, name, agent, icon, duration: status === 'done' ? dur : status === 'failed' ? dur : null, llm, material: mat, tts, status }
  })
}

const SHOTS = [
  { idx: 1, narration: '100 块的降噪耳机，和 1000 块的，差距可能就一根线。', visual: '三款耳机摔在桌上，价格标签特写，手持晃动感', search: 'earbuds on desk price tag close up', duration: '3s' },
  { idx: 2, narration: '我把三款都戴上了早高峰的 2 号线。', visual: '地铁车厢内主观视角，人潮，降噪波形动画叠加', search: 'subway commute crowd pov', duration: '6s' },
  { idx: 3, narration: '最贵的那款，第一个被我摘下来。', visual: '摘下耳机特写，表情反差，字幕条弹出', search: 'take off earbuds close up', duration: '4s' },
  { idx: 4, narration: '降噪实测：三款波形对比，差距在这里。', visual: '三段分屏波形图，参数字幕条上屏', search: 'sound wave comparison graphic', duration: '9s' },
  { idx: 5, narration: '音质环节，百元档里它是唯一没糊的。', visual: '频谱仪画面 + 桌面静物旋转展示', search: 'audio spectrum product turntable', duration: '9s' },
  { idx: 6, narration: '预算两百内的答案我放评论区置顶，你站哪一款？', visual: '三款耳机全家福定格，点赞按钮动效', search: 'earbuds group shot studio light', duration: '8s' },
]

export const PROJECTS = [
  {
    id: 'p-1001',
    name: '百元降噪耳机横评：谁最能打？',
    account: 'dy-shuma',
    status: 'published',
    createdAt: '昨天 18:22',
    detail: 'full',
    config: cfg(),
    artifacts: {
      audio: 'runs/p-1001/audio/voiceover.mp3',
      subtitle: 'runs/p-1001/subtitle/final.srt',
      cover: 'runs/p-1001/cover/cover.jpg',
      final: 'runs/p-1001/video/final.mp4',
    },
    video: { duration: '00:58', ratio: '9:16', res: '1080×1920' },
    pack: {
      platform: '抖音',
      title: '百元降噪耳机横评：最贵的那款我第一个摘了',
      caption: '三款百元降噪耳机早高峰实测，结果最贵的那款第一个被我摘下来。答案在评论区置顶。',
      tags: ['数码测评', '降噪耳机', '百元好物', '618'],
    },
    stages: stageRows(),
    shots: SHOTS,
    logs: [
      '[09:41:02] run p-1001 created, account=dy-shuma',
      '[09:41:04] trend_scan ok, 3 candidates, top_heat=86.4w',
      '[09:42:10] gate_topic confirmed by operator (choice #1)',
      '[09:42:15] script_draft ok, 58s estimated, 14.2 chars/sentence',
      '[09:42:40] storyboard ok, 6 shots',
      '[09:43:31] mpt_pipeline ok in 7.5s (terms/audio/subtitle/materials/video)',
      '[09:44:02] gate_preview confirmed',
      '[09:44:10] packaging ok, title 22/30 chars',
      '[09:44:31] publish ok → 抖音 video_id=7312458801',
      '[09:45:00] monitoring scheduled: T+1h/6h/24h/7d',
    ],
    snapshots: [
      { t: 'T+1h', play: 12480, like: 936, comment: 128, share: 210 },
      { t: 'T+6h', play: 28940, like: 2310, comment: 402, share: 560 },
      { t: 'T+24h', play: 51200, like: 4020, comment: 688, share: 1140 },
      { t: 'T+7d', play: 63800, like: 4720, comment: 801, share: 1420 },
    ],
    tips: [
      '建议修改 skills/爆款脚本.md 的钩子公式：前 3 秒把「价格冲突」前置为「反直觉结论」。',
      '评论区高频词是「链接」，下一轮简介栏固定挂清单索引。',
    ],
    chat: [
      { type: 'user', text: '做一条数码赛道的短视频：百元降噪耳机横评' },
      { type: 'assistant', text: '热点扫描完成：命中数码赛道 3 个上升话题，已按「争议度 × 搜索增速 × 粉丝画像」排序。' },
      { type: 'assistant', text: '选题已锁定：「百元降噪耳机横评：谁最能打？」。编剧开始起草脚本。' },
      { type: 'assistant', text: '脚本过审。台词校对已通过（节奏 14.2 字/句，无违禁词），分镜师接手。' },
      { type: 'assistant', text: '成片确认。包装师开始生成标题、标签与封面。' },
      { type: 'assistant', text: '已发布：抖音（video_id=7312458801）。分析师接管数据监控。' },
    ],
  },
  {
    id: 'p-1002',
    name: '我把手机换成了“老人机”用了 7 天',
    account: 'dy-shuma',
    status: 'review',
    createdAt: '今天 09:18',
    detail: 'gate',
    config: cfg({ duration: '75s', material: 'Pixabay + 本地素材' }),
    artifacts: {
      audio: 'runs/p-1002/audio/voiceover.mp3',
      subtitle: 'runs/p-1002/subtitle/final.srt',
      cover: '',
      final: 'runs/p-1002/video/final.mp4',
    },
    video: { duration: '01:14', ratio: '9:16', res: '1080×1920' },
    pack: null,
    stages: stageRows(9), // through mpt_video
    shots: SHOTS.slice(0, 4),
    logs: [
      '[09:18:02] run p-1002 created, account=dy-shuma',
      '[09:18:05] trend_scan ok, top_heat=52.1w',
      '[09:18:40] gate_topic confirmed (choice #2)',
      '[09:19:12] script_draft ok, 74s estimated',
      '[09:19:50] storyboard ok, 4 shots',
      '[09:20:31] mpt_pipeline ok in 7.5s',
      '[09:20:31] gate_preview pending — waiting operator',
    ],
    snapshots: [],
    tips: [],
    chat: [
      { type: 'user', text: '做一条数码赛道的短视频' },
      { type: 'assistant', text: '选题已锁定：「我把手机换成了“老人机”用了 7 天」。编剧开始起草脚本。' },
      { type: 'assistant', text: '脚本过审。台词校对已通过，分镜师接手。' },
      { type: 'assistant', text: '制片流水线完成，成片已渲染，请总编预览确认。' },
    ],
  },
  {
    id: 'p-1003',
    name: '618 别乱买：桌面好物避雷清单',
    account: 'none',
    status: 'unpublished',
    createdAt: '周二 16:40',
    detail: 'output',
    config: cfg({ ratio: '16:9', material: 'Pexels' }),
    artifacts: {
      audio: 'runs/p-1003/audio/voiceover.mp3',
      subtitle: 'runs/p-1003/subtitle/final.srt',
      cover: 'runs/p-1003/cover/cover.jpg',
      final: 'runs/p-1003/video/final.mp4',
    },
    video: { duration: '00:47', ratio: '16:9', res: '1920×1080' },
    pack: {
      platform: '未选择账号',
      title: '618 桌面好物避雷：第 3 个全网都在推，我劝你别买',
      caption: '自掏腰包实测 5 款爆款桌面好物，2 款翻车。清单在评论区。',
      tags: ['桌面好物', '避雷', '618'],
    },
    stages: stageRows(12), // through packaging
    shots: SHOTS.slice(0, 5),
    logs: [
      '[16:40:02] run p-1003 created, account=none',
      '[16:41:20] mpt_pipeline ok in 7.4s',
      '[16:42:02] gate_preview confirmed',
      '[16:42:10] packaging ok',
      '[16:42:10] gate_publish pending — no account selected, skipped by operator',
    ],
    snapshots: [],
    tips: [],
    chat: [
      { type: 'user', text: '做一条 618 桌面好物避雷清单' },
      { type: 'assistant', text: '成片确认。包装师开始生成标题、标签与封面。' },
      { type: 'assistant', text: '打包完成。未选择发布账号，发布闸门已跳过，成片已存入 workspace。' },
    ],
  },
  {
    id: 'p-1004',
    name: '618 耳机选购攻略（自动生成中）',
    account: 'bili-xiaox',
    status: 'generating',
    createdAt: '刚刚',
    detail: 'live',
    config: cfg({ duration: '90s', voice: '云野（磁性男声）', material: 'Pexels + Pixabay' }),
    artifacts: { audio: '', subtitle: '', cover: '', final: '' },
    video: null,
    pack: null,
    stages: [],
    shots: [],
    logs: [],
    snapshots: [],
    tips: [],
    chat: [{ type: 'user', text: '做一条 618 耳机选购攻略，发 B站' }],
  },
  {
    id: 'p-1005',
    name: '机械键盘入门：轴体到底怎么选',
    account: 'bili-xiaox',
    status: 'failed',
    createdAt: '昨天 21:07',
    detail: 'failed',
    config: cfg({ ratio: '16:9', duration: '90s', voice: '云野（磁性男声）' }),
    artifacts: {
      audio: 'runs/p-1005/audio/voiceover.mp3',
      subtitle: 'runs/p-1005/subtitle/final.srt',
      cover: '',
      final: '',
    },
    video: null,
    pack: null,
    stages: stageRows(null, 'mpt_materials'),
    shots: SHOTS.slice(0, 5),
    logs: [
      '[21:07:02] run p-1005 created, account=bili-xiaox',
      '[21:07:05] trend_scan ok',
      '[21:07:44] gate_topic confirmed (choice #1)',
      '[21:08:15] script_draft ok, 88s estimated',
      '[21:08:50] storyboard ok, 5 shots',
      '[21:09:02] mpt/terms ok',
      '[21:09:04] mpt/audio ok (TTS ¥1.20)',
      '[21:09:05] mpt/subtitle ok',
      '[21:09:06] mpt/materials FAIL: Pexels API HTTP 429 rate limited (retry 3/3 exhausted)',
      '[21:09:06] ERROR stage=mpt_pipeline/materials: quota exceeded, resume token saved',
      '[21:09:06] run aborted. cost so far ¥1.85 (LLM ¥0.65 / TTS ¥1.20)',
    ],
    snapshots: [],
    tips: [],
    chat: [
      { type: 'user', text: '做一条机械键盘轴体入门，发 B站' },
      { type: 'assistant', text: '脚本过审。台词校对已通过，分镜师接手。' },
      { type: 'assistant', text: '制片流水线在「素材拉取」阶段失败：Pexels API 限流（HTTP 429）。已重试 3 次。可在配额恢复后从断点续跑。' },
    ],
  },
  {
    id: 'p-1006',
    name: '手机摄影的 5 个致命误区',
    account: 'none',
    status: 'unpublished',
    createdAt: '周一 11:03',
    detail: 'simple',
    config: cfg(),
    artifacts: {
      audio: 'runs/p-1006/audio/voiceover.mp3',
      subtitle: 'runs/p-1006/subtitle/final.srt',
      cover: 'runs/p-1006/cover/cover.jpg',
      final: 'runs/p-1006/video/final.mp4',
    },
    video: { duration: '00:52', ratio: '9:16', res: '1080×1920' },
    pack: null,
    stages: stageRows(12),
    shots: [],
    logs: [],
    snapshots: [],
    tips: [],
    chat: [{ type: 'user', text: '做一条手机摄影误区盘点' }],
  },
]

export const WORKFLOWS = [
  { id: 'wf-1', name: '数码赛道 · 每日日更', schedule: '40 7 * * *', desc: '每天 07:40 自动跑完整流水线', next: '明早 07:40', account: 'dy-shuma', enabled: true },
  { id: 'wf-2', name: '每周复盘报告', schedule: '21 21 * * 0', desc: '每周日汇总账号数据并生成复盘', next: '周日 21:21', account: 'dy-shuma', enabled: true },
  { id: 'wf-3', name: '键盘赛道 · 隔日更', schedule: '25 18 */2 * *', desc: '隔一天 18:25 生成一条', next: '后天 18:25', account: 'bili-xiaox', enabled: false },
]

// Extra published videos for the monitor board (beyond project list)
export const MONITOR_VIDEOS = [
  { id: 'v-1', title: '百元降噪耳机横评：谁最能打？', account: 'dy-shuma', play: 63800, like: 4720, comment: 801, delta: '+18%', age: '1 天前', project: 'p-1001', series: [12480, 28940, 51200, 63800] },
  { id: 'v-2', title: '我把手机调成灰度模式用了 30 天', account: 'dy-shuma', play: 41200, like: 3350, comment: 522, delta: '+9%', age: '3 天前', project: null, series: [9800, 21400, 35600, 41200] },
  { id: 'v-3', title: '键盘轴体盲测：线性 vs 段落', account: 'bili-xiaox', play: 18400, like: 1620, comment: 310, delta: '+31%', age: '2 天前', project: null, series: [4200, 9100, 14800, 18400] },
  { id: 'v-4', title: '618 桌面好物 Top5', account: 'bili-xiaox', play: 12030, like: 890, comment: 96, delta: '-6%', age: '4 天前', project: null, series: [5100, 8600, 11200, 12030] },
]

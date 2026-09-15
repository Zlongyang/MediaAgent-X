<script setup>
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import HeroView from './components/HeroView.vue'
import ChatView from './components/ChatView.vue'
import Composer from './components/Composer.vue'
import DetailsPanel from './components/DetailsPanel.vue'
import ProjectView from './components/ProjectView.vue'
import MonitorView from './components/MonitorView.vue'
import WorkflowsView from './components/WorkflowsView.vue'
import AccountView from './components/AccountView.vue'
import SettingsModal from './components/SettingsModal.vue'
import { PROJECTS, WORKFLOWS, ACCOUNTS, NO_ACCOUNT, defaultConfig } from './data/mock.js'

/* ================= theme: dark / light / system ================= */
const theme = ref('system')
try {
  const t = localStorage.getItem('max-theme')
  if (t === 'dark' || t === 'light' || t === 'system') theme.value = t
} catch (e) {}

const media = window.matchMedia('(prefers-color-scheme: dark)')

function resolvedDark() {
  return theme.value === 'dark' || (theme.value === 'system' && media.matches)
}

function applyTheme() {
  document.body.toggleAttribute('data-ds-dark-theme', resolvedDark())
  try { localStorage.setItem('max-theme', theme.value) } catch (e) {}
}

function onMediaChange() {
  if (theme.value === 'system') applyTheme()
}
media.addEventListener('change', onMediaChange)
applyTheme()

function setTheme(t) {
  theme.value = t
  applyTheme()
}

/* ================= global ui state ================= */
const view = ref('chat') // chat | monitor | workflows | project | account
const chatMode = ref('hero') // hero | run
const sidebarCollapsed = ref(false)
const detailsOpen = ref(true)
const account = ref('dy-shuma')
const apiKey = ref('')
const settingsOpen = ref(false)
const accountPageKey = ref('')
const projects = ref(PROJECTS.map((p) => ({ ...p })))
const workflows = ref(WORKFLOWS.map((w) => ({ ...w })))
const activeProjectId = ref('')

const toast = ref('')
let toastTimer = null
function showToast(text) {
  toast.value = text
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 2400)
}

/* responsive tracks */
const narrowMQ = window.matchMedia('(max-width: 1100px)')
const tinyMQ = window.matchMedia('(max-width: 860px)')
const narrow = ref(narrowMQ.matches)
const tiny = ref(tinyMQ.matches)
const onNarrow = () => (narrow.value = narrowMQ.matches)
const onTiny = () => (tiny.value = tinyMQ.matches)
narrowMQ.addEventListener('change', onNarrow)
tinyMQ.addEventListener('change', onTiny)

onBeforeUnmount(() => {
  media.removeEventListener('change', onMediaChange)
  narrowMQ.removeEventListener('change', onNarrow)
  tinyMQ.removeEventListener('change', onTiny)
  stopStatus()
})

const detailsVisible = computed(() => view.value === 'chat' && chatMode.value === 'run' && !narrow.value)
const detailsW = computed(() => (detailsVisible.value && detailsOpen.value ? 300 : 0))
const sidebarW = computed(() => (tiny.value ? 0 : sidebarCollapsed.value ? 56 : 272))
const gridCols = computed(() => `${sidebarW.value}px minmax(0, 1fr) ${detailsW.value}px`)

const activeProject = computed(() => projects.value.find((p) => p.id === activeProjectId.value) || null)

function accountLabel(key) {
  const a = [...ACCOUNTS, NO_ACCOUNT].find((x) => x.key === key)
  return a ? a.label : '—'
}

/* ================= pipeline model ================= */
function buildStages() {
  return [
    { key: 'trend_scan', name: 'trend_scan · 选题扫描', agent: '选题猎手', icon: 'target', status: 'pending', duration: null },
    { key: 'gate_topic', name: '选题确认', agent: '总编', status: 'pending', duration: null, gate: true },
    { key: 'script_draft', name: 'script_draft · 脚本草稿', agent: '编剧', icon: 'pen', status: 'pending', duration: null },
    { key: 'gate_script', name: '脚本确认', agent: '总编', status: 'pending', duration: null, gate: true },
    { key: 'storyboard', name: 'storyboard · 分镜设计', agent: '分镜师', icon: 'clapper', status: 'pending', duration: null },
    {
      key: 'mpt_pipeline', name: 'mpt_pipeline · 制片流水线', agent: '制片', icon: 'factory', status: 'pending', duration: null,
      subs: [
        { key: 'terms', name: 'terms · 提示词生成', status: 'pending', duration: null },
        { key: 'audio', name: 'audio · 配音合成', status: 'pending', duration: null },
        { key: 'subtitle', name: 'subtitle · 字幕生成', status: 'pending', duration: null },
        { key: 'materials', name: 'materials · 素材拉取', status: 'pending', duration: null },
        { key: 'video', name: 'video · 视频合成', status: 'pending', duration: null },
      ],
    },
    { key: 'gate_preview', name: '成片预览', agent: '总编', status: 'pending', duration: null, gate: true },
    { key: 'packaging', name: 'packaging · 发布打包', agent: '包装师', icon: 'package', status: 'pending', duration: null },
    { key: 'gate_publish', name: '发布确认', agent: '总编', status: 'pending', duration: null, gate: true },
    { key: 'publish', name: 'publish · 发布上线', agent: '发行人', icon: 'rocket', status: 'pending', duration: null },
    { key: 'monitoring', name: 'monitoring · 数据回拉', agent: '分析师', icon: 'chart', status: 'pending', duration: null },
    { key: 'review', name: 'review · 复盘报告', agent: '分析师', icon: 'chart', status: 'pending', duration: null },
  ]
}

const TOPIC_CANDIDATES = [
  {
    title: '百元降噪耳机横评：谁最能打？',
    source: '抖音热榜 · 数码',
    heat: '86.4w',
    reason: '争议型对比天然带评论，近 7 天搜索量 +142%，且与账号既有粉丝画像高度重合。',
  },
  {
    title: '我把手机换成了“老人机”用了 7 天',
    source: 'B站 · 科技区上升',
    heat: '52.1w',
    reason: '反差体验类内容 3s 留存高，制作成本低，适合快反；但同质化开始冒头，需要强钩子。',
  },
  {
    title: '618 别乱买：桌面好物避雷清单',
    source: '小红书 · 热点',
    heat: '38.7w',
    reason: '临近大促转化意图强，挂车收益高；风险是清单类同质化，需要“翻车实测”角度。',
  },
]

const SCRIPT_EXCERPT = `# 百元降噪耳机横评：谁最能打？（节选）

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
  你站哪一款？说错了算我的。」`

const PACK_RESULT = {
  title: '百元降噪耳机横评：最贵的那款我第一个摘了',
  titleLen: 22,
  descLen: 64,
  tags: ['数码测评', '降噪耳机', '百元好物', '618'],
}

/* ================= live run state ================= */
const items = ref([])
const stages = ref(buildStages())
const gate = ref(null)
const status = ref(null) // { text, clock }
const running = ref(false)
const finished = ref(false)

const ms = reactive({
  run_id: '—',
  stage: 'idle',
  autonomy: { topic: true, script: true, preview: true, publish: true },
  topic: '',
  cost: { llm: 0, material: 0, tts: 0, total: 0 },
  artifacts: { audio: '', subtitle: '', final: '' },
  review_report: '',
  todos: [
    { id: 1, text: '扫描赛道热点', done: false },
    { id: 2, text: '确认选题', done: false },
    { id: 3, text: '输出脚本草稿', done: false },
    { id: 4, text: '分镜与制片', done: false },
    { id: 5, text: '打包与发布', done: false },
    { id: 6, text: '数据监控与复盘', done: false },
  ],
  running: false,
})

let gateResolve = null
let statusTimer = null
let runSeq = 0
let autoMode = false
let sessionProjectId = ''

class StaleError extends Error {}

// Throw when a newer run has superseded seq — aborts stale timers silently.
function checkSeq(seq) {
  if (seq !== runSeq) throw new StaleError()
}

const sleep = (ms_) => new Promise((r) => setTimeout(r, ms_))

function startStatus(text) {
  stopStatus()
  status.value = { text, clock: 0 }
  statusTimer = setInterval(() => {
    if (status.value) status.value.clock += 1
  }, 1000)
}

function stopStatus() {
  if (statusTimer) clearInterval(statusTimer)
  statusTimer = null
  status.value = null
}

function addCost(part) {
  for (const k of ['llm', 'material', 'tts']) {
    if (part[k]) ms.cost[k] = +(ms.cost[k] + part[k]).toFixed(2)
  }
  ms.cost.total = +(ms.cost.llm + ms.cost.material + ms.cost.tts).toFixed(2)
}

function markTodo(id) {
  const t = ms.todos.find((x) => x.id === id)
  if (t) t.done = true
}

function findStage(key) {
  return stages.value.find((s) => s.key === key)
}

async function runStage(key, ms_, statusText, cost, seq) {
  const s = findStage(key)
  s.status = 'active'
  ms.stage = key
  if (statusText) startStatus(statusText)
  const t0 = performance.now()
  await sleep(ms_)
  checkSeq(seq)
  s.duration = +(((performance.now() - t0) / 1000)).toFixed(1)
  s.status = 'done'
  if (cost) addCost(cost)
  stopStatus()
}

async function runSub(key, ms_, statusText, cost, seq, after) {
  const pipe = findStage('mpt_pipeline')
  const sub = pipe.subs.find((x) => x.key === key)
  sub.status = 'active'
  ms.stage = 'mpt_pipeline/' + key
  startStatus(statusText)
  const t0 = performance.now()
  await sleep(ms_)
  checkSeq(seq)
  sub.duration = +(((performance.now() - t0) / 1000)).toFixed(1)
  sub.status = 'done'
  if (cost) addCost(cost)
  if (after) after()
  stopStatus()
}

function waitGate(g, seq) {
  checkSeq(seq)
  return new Promise((resolve) => {
    const gateStage = findStage(g.stageKey)
    gateStage.status = 'gated'
    ms.stage = g.key
    stopStatus()
    if (autoMode || !ms.autonomy[g.autonomyKey]) {
      gateStage.status = 'done'
      resolve({ action: 'confirm', payload: g.autoPayload() })
      return
    }
    gate.value = g
    gateResolve = resolve
  })
}

let gateNonce = 0

async function gateWithRerun(g, rerun, seq) {
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const res = await waitGate({ ...g, nonce: ++gateNonce }, seq)
    checkSeq(seq)
    if (res.action === 'confirm') {
      findStage(g.stageKey).status = 'done'
      return res.payload
    }
    await rerun()
  }
}

function onGateConfirm(payload) {
  if (!gateResolve) return
  gate.value = null
  const r = gateResolve
  gateResolve = null
  r({ action: 'confirm', payload })
}

function onGateReject() {
  if (!gateResolve) return
  gate.value = null
  const r = gateResolve
  gateResolve = null
  r({ action: 'reject' })
}

/* ================= run orchestration ================= */
async function startRun(text, opts = {}) {
  if (running.value) return
  const seq = ++runSeq
  autoMode = !!opts.auto
  running.value = true
  finished.value = false
  stages.value = buildStages()
  items.value = [{ type: 'user', text }]
  gate.value = null

  const rid = opts.project
    ? opts.project.id
    : 'run-' + String(new Date().getMonth() + 1).padStart(2, '0') +
      String(new Date().getDate()).padStart(2, '0') + '-' +
      Math.random().toString(16).slice(2, 6)

  // project bookkeeping
  let proj = opts.project || null
  if (!proj) {
    proj = {
      id: rid,
      name: text.length > 18 ? text.slice(0, 18) + '…' : text,
      account: account.value,
      status: 'generating',
      createdAt: '刚刚',
      detail: 'live',
      config: defaultConfig(),
      artifacts: { audio: '', subtitle: '', cover: '', final: '' },
      video: null,
      pack: null,
      stages: [],
      shots: [],
      logs: [],
      snapshots: [],
      tips: [],
      chat: [],
    }
    projects.value.unshift(proj)
    // re-fetch through the reactive array so later mutations trigger updates
    proj = projects.value[0]
  }
  proj.status = 'generating'
  sessionProjectId = rid
  activeProjectId.value = rid

  ms.run_id = rid
  ms.stage = 'queued'
  ms.topic = ''
  ms.cost = { llm: 0, material: 0, tts: 0, total: 0 }
  ms.artifacts = { audio: '', subtitle: '', final: '' }
  ms.review_report = ''
  ms.todos.forEach((t) => (t.done = false))
  ms.running = true

  try {
    await sleep(400)
    checkSeq(seq)
    items.value.push({ type: 'pipeline' })

    await runStage('trend_scan', 2000, '选题猎手 正在扫描热点…', { llm: 0.12 }, seq)
    markTodo(1)
    items.value.push({ type: 'assistant', text: '热点扫描完成：命中数码赛道 3 个上升话题，已按「争议度 × 搜索增速 × 粉丝画像」排序，请总编确认选题方向。' })

    const topic = await gateWithRerun(
      {
        key: 'gate_topic', stageKey: 'gate_topic', title: '选题确认', autonomyKey: 'topic',
        candidates: TOPIC_CANDIDATES,
        autoPayload: () => ({ choice: TOPIC_CANDIDATES[0] }),
      },
      () => runStage('trend_scan', 1400, '选题猎手 正在重新扫描热点…', { llm: 0.06 }, seq),
      seq
    )
    ms.topic = topic.choice.title
    markTodo(2)
    items.value.push({ type: 'assistant', text: `选题已锁定：「${topic.choice.title}」。编剧开始起草脚本。` })

    await runStage('script_draft', 2500, '编剧 正在撰写脚本草稿…', { llm: 0.35 }, seq)

    await gateWithRerun(
      {
        key: 'gate_script', stageKey: 'gate_script', title: '脚本确认', autonomyKey: 'script',
        script: SCRIPT_EXCERPT,
        autoPayload: () => ({}),
      },
      () => runStage('script_draft', 1600, '编剧 正在按驳回意见改写…', { llm: 0.18 }, seq),
      seq
    )
    markTodo(3)
    items.value.push({ type: 'assistant', text: '脚本过审。台词校对已通过（节奏 14.2 字/句，无违禁词），分镜师接手。' })

    await runStage('storyboard', 2000, '分镜师 正在拆分镜头…', { llm: 0.28 }, seq)

    const pipe = findStage('mpt_pipeline')
    pipe.status = 'active'
    ms.stage = 'mpt_pipeline'
    const p0 = performance.now()
    await runSub('terms', 1500, '制片 正在生成镜头提示词…', { llm: 0.10 }, seq)
    await runSub('audio', 1500, '制片 正在合成配音 (TTS)…', { tts: 1.20 }, seq, () => {
      ms.artifacts.audio = `runs/${rid}/audio/voiceover.mp3`
    })
    await runSub('subtitle', 1500, '制片 正在生成字幕…', { llm: 0.08 }, seq, () => {
      ms.artifacts.subtitle = `runs/${rid}/subtitle/final.srt`
    })
    await runSub('materials', 1500, '制片 正在拉取素材…', { material: 2.50 }, seq)
    await runSub('video', 1500, '制片 正在合成视频…', { material: 0.60 }, seq, () => {
      ms.artifacts.final = `runs/${rid}/video/final.mp4`
    })
    pipe.duration = +(((performance.now() - p0) / 1000)).toFixed(1)
    pipe.status = 'done'
    markTodo(4)

    await gateWithRerun(
      {
        key: 'gate_preview', stageKey: 'gate_preview', title: '成片预览', autonomyKey: 'preview',
        videoPath: `runs/${rid}/video/final.mp4`,
        autoPayload: () => ({}),
      },
      () => runSub('video', 1200, '制片 正在重新合成视频…', { material: 0.30 }, seq),
      seq
    )
    items.value.push({ type: 'assistant', text: '成片确认。包装师开始生成标题、标签与封面。' })

    await runStage('packaging', 2000, '包装师 正在生成标题/标签/封面…', { llm: 0.15 }, seq)

    await gateWithRerun(
      {
        key: 'gate_publish', stageKey: 'gate_publish', title: '发布确认', autonomyKey: 'publish',
        pack: PACK_RESULT,
        autoPayload: () => ({}),
      },
      () => runStage('packaging', 1200, '包装师 正在重新打包…', { llm: 0.08 }, seq),
      seq
    )

    await runStage('publish', 1500, '发行人 正在上传发布…', { llm: 0.02 }, seq)
    markTodo(5)
    const acct = accountLabel(proj.account)
    items.value.push({
      type: 'assistant',
      text: proj.account === 'none'
        ? '未选择发布账号：成片已存入 workspace，发布环节改为手动。分析师仍会排期监控位。'
        : `已发布：${acct}。分析师接管数据监控。`,
    })

    await runStage('monitoring', 1500, '分析师 正在排期数据回拉…', { llm: 0.05 }, seq)
    items.value.push({ type: 'note', text: `metrics_snapshots: 已排期 T+1h / T+6h / T+24h / T+7d 四次回拉 → runs/${rid}/metrics/` })

    await sleep(600)
    checkSeq(seq)
    const rs = findStage('review')
    rs.status = 'done'
    rs.duration = 0.6
    ms.stage = 'review'
    markTodo(6)
    ms.review_report = '达标：CTR 4.2%，3s 留存 61%；钩子公式待优化，建议已回流。'

    items.value.push({ type: 'assistant', text: '复盘完成（基于 T+1h 首次回拉数据，模拟值）：' })
    items.value.push({
      type: 'review',
      review: {
        runId: rid,
        metrics: [
          { label: '播放', value: '12,480', delta: '+18%' },
          { label: '点赞', value: '936', delta: '+24%' },
          { label: '评论', value: '128', delta: '+9%' },
        ],
        cost: { ...ms.cost },
        tips: [
          '建议修改 skills/爆款脚本.md 的钩子公式：前 3 秒把「价格冲突」前置为「反直觉结论」。',
          '评论区高频词是「链接」，下一轮简介栏固定挂清单索引。',
        ],
      },
    })
    items.value.push({ type: 'assistant', text: `本轮运行完成，总成本 ¥${ms.cost.total.toFixed(2)}。复盘建议已回流到技能库，下一轮选题会自动带上这些修正。` })

    // finalize project
    proj.status = proj.account === 'none' ? 'unpublished' : 'published'
    proj.video = { duration: '00:58', ratio: '9:16', res: '1080×1920' }
    proj.artifacts = { ...ms.artifacts, cover: `runs/${rid}/cover/cover.jpg` }
    proj.pack = {
      platform: acct,
      title: PACK_RESULT.title,
      caption: '三款百元降噪耳机早高峰实测，结果最贵的那款第一个被我摘下来。答案在评论区置顶。',
      tags: PACK_RESULT.tags,
    }
    proj.chat = items.value.filter((i) => i.type === 'user' || i.type === 'assistant')
    if (proj.status === 'published') {
      proj.snapshots = [
        { t: 'T+1h', play: 12480, like: 936, comment: 128, share: 210 },
      ]
      proj.tips = ['建议修改 skills/爆款脚本.md 的钩子公式：前 3 秒把「价格冲突」前置为「反直觉结论」。']
    }

    running.value = false
    finished.value = true
    ms.running = false
    autoMode = false
  } catch (e) {
    if (!(e instanceof StaleError)) throw e
    // superseded by a newer run — leave state to the new owner
  }
}

/* ================= input & navigation ================= */
function onSend(text) {
  if (running.value) {
    items.value.push({ type: 'user', text })
    if (gate.value) {
      items.value.push({ type: 'assistant', text: `收到催促。当前停在「${gate.value.title}」闸门，请在上方卡片里确认或驳回，流水线才会继续。` })
    } else {
      items.value.push({ type: 'assistant', text: `收到。流水线正在执行 ${ms.stage}，完成后我会汇总给你。` })
    }
    return
  }
  if (finished.value && chatMode.value === 'run') {
    items.value.push({ type: 'user', text })
    items.value.push({ type: 'assistant', text: '收到。本轮运行已完成并复盘，若要再跑一轮新任务，请点击左侧「＋ 新对话」。' })
    return
  }
  chatMode.value = 'run'
  view.value = 'chat'
  startRun(text)
}

function newVideo() {
  runSeq++
  stopStatus()
  gate.value = null
  gateResolve = null
  running.value = false
  finished.value = false
  autoMode = false
  ms.running = false
  ms.stage = 'idle'
  view.value = 'chat'
  chatMode.value = 'hero'
  activeProjectId.value = ''
}

function onNav(key) {
  view.value = key
  if (key !== 'chat') activeProjectId.value = ''
}

function openAccount(key) {
  view.value = 'account'
  accountPageKey.value = key
  activeProjectId.value = ''
}

function onProjectSend(project, text) {
  if (project.id === sessionProjectId && (running.value || finished.value)) {
    // live session: reuse the chat nudge logic
    onSend(text)
    return
  }
  project.chat = [
    ...(project.chat || []),
    { type: 'user', text },
    { type: 'assistant', text: '收到，已记录到该项目备注（演示回复，不会触发新的流水线）。' },
  ]
}

function selectProject(id) {
  activeProjectId.value = id
  const p = projects.value.find((x) => x.id === id)
  view.value = 'project'
  if (!p) return
  // live mock project: start an auto pipeline demo if the engine is free
  if (p.detail === 'live' && p.status === 'generating' && !running.value && sessionProjectId !== p.id) {
    startRun(p.chat[0] ? p.chat[0].text : p.name, { auto: true, project: p })
  } else if (p.id === sessionProjectId && (running.value || finished.value)) {
    // session project: showing live engine inside project view
  }
}

function backFromProject() {
  view.value = 'chat'
}

function publishProject(p) {
  if (p.account === 'none') {
    showToast('请先在 Hero 页选择发布账号，再发起发布')
    return
  }
  p.status = 'published'
  showToast(`已发布到 ${accountLabel(p.account)}（模拟）`)
}

function toggleWorkflow(id) {
  const w = workflows.value.find((x) => x.id === id)
  if (w) w.enabled = !w.enabled
}

function runWorkflow(wf) {
  showToast(`已手动触发「${wf.name}」，运行进入队列（模拟）`)
}

function toggleAutonomy(key) {
  if (!running.value && !finished.value) return
  ms.autonomy[key] = !ms.autonomy[key]
}

const liveForProject = computed(() => {
  if (!activeProject.value || activeProject.value.id !== sessionProjectId) return null
  if (!running.value && !finished.value) return null
  return { items: items.value, stages: stages.value, gate: gate.value, status: status.value }
})

const navKey = computed(() => (view.value === 'project' || view.value === 'account' ? '' : view.value))
</script>

<template>
  <div class="frame" :style="{ gridTemplateColumns: gridCols }" :data-tiny="tiny">
    <div class="sidebarCol">
      <Sidebar
        :collapsed="sidebarCollapsed"
        :nav="navKey"
        :projects="projects"
        :active-project-id="activeProjectId"
        @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
        @nav="onNav"
        @new-video="newVideo"
        @select-project="selectProject"
        @open-account="openAccount"
        @open-settings="settingsOpen = true"
      />
    </div>

    <div class="centerCol">
      <!-- chat view -->
      <template v-if="view === 'chat'">
        <HeroView
          v-if="chatMode === 'hero'"
          :account="account"
          @send="onSend"
          @select-account="(k) => (account = k)"
        />
        <template v-else>
          <ChatView
            :items="items"
            :stages="stages"
            :status="status"
            :gate="gate"
            @gate-confirm="onGateConfirm"
            @gate-reject="onGateReject"
          />
          <div class="composerSeat">
            <Composer @send="onSend" />
          </div>
        </template>
      </template>

      <!-- monitor board -->
      <MonitorView
        v-else-if="view === 'monitor'"
        @open-project="selectProject"
      />

      <!-- workflows -->
      <WorkflowsView
        v-else-if="view === 'workflows'"
        :workflows="workflows"
        @toggle="toggleWorkflow"
        @run="runWorkflow"
      />

      <!-- project detail -->
      <ProjectView
        v-else-if="view === 'project' && activeProject"
        :project="activeProject"
        :live="liveForProject"
        @back="backFromProject"
        @publish="publishProject"
        @gate-confirm="onGateConfirm"
        @gate-reject="onGateReject"
        @toast="showToast"
        @project-send="onProjectSend"
      />

      <!-- account page -->
      <AccountView
        v-else-if="view === 'account'"
        :account-key="accountPageKey"
        :projects="projects"
        @back="backFromProject"
        @open-project="selectProject"
      />

      <!-- details expand pill (when collapsed but available) -->
      <button
        v-if="view === 'chat' && chatMode === 'run' && !detailsOpen && !narrow"
        class="detailsPill"
        type="button"
        title="展开运行状态"
        aria-label="展开运行状态"
        @click="detailsOpen = true"
      />
    </div>

    <div
      class="detailsCol"
      :data-hidden="!detailsVisible || !detailsOpen"
    >
      <div class="detailsInner">
        <button
          class="iconButton collapseBtn"
          type="button"
          title="收起运行状态"
          aria-label="收起运行状态"
          @click="detailsOpen = false"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M4.5 2.5L9 7l-4.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <DetailsPanel :state="ms" @toggle-autonomy="toggleAutonomy" />
      </div>
    </div>

    <!-- toast -->
    <div v-if="toast" class="toast">{{ toast }}</div>

    <!-- centered settings modal -->
    <SettingsModal
      :open="settingsOpen"
      :theme="theme"
      :api-key="apiKey"
      @close="settingsOpen = false"
      @set-theme="setTheme"
      @set-api-key="(k) => (apiKey = k)"
    />
  </div>
</template>

<style>
.frame {
  position: relative;
  display: grid;
  grid-template-rows: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--dsw-alias-bg-base);
  transition: grid-template-columns var(--ds-transition-duration-slow) var(--ds-ease-in-out);

  /* shared width axis (ConversationRoot) */
  --dsh-chat-content-width: 748px;
  --dsh-composer-card-max-width: calc(var(--dsh-chat-content-width) + 32px);
  --dsh-composer-side-clearance: 16px;
}

.sidebarCol {
  min-width: 0;
  overflow: hidden;
  background: var(--dsw-specific-sidebar-fill);
  border-right: 1px solid var(--dsw-alias-border-l1);
}

.frame[data-tiny='true'] .sidebarCol {
  display: none;
}

.centerCol {
  position: relative;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detailsCol {
  min-width: 0;
  overflow: hidden;
  border-left: 1px solid var(--dsw-alias-border-l2);
}

.detailsCol[data-hidden='true'] {
  border-left: none;
}

.detailsInner {
  position: relative;
  width: 300px;
  height: 100%;
}

.collapseBtn {
  position: absolute;
  top: 14px;
  right: 8px;
  z-index: 2;
}

.iconButton {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  padding: 0;
  background: transparent;
  cursor: pointer;
  color: var(--dsw-alias-label-secondary);
}

.iconButton:hover {
  background: var(--dsw-alias-interactive-bg-hover);
}

.detailsPill {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 8;
  width: 12px;
  height: 32px;
  border: 1px solid var(--dsw-alias-border-l2-darkmode-thin);
  border-right: none;
  border-radius: 10px 0 0 10px;
  background: var(--dsw-alias-button-floating-fill);
  cursor: pointer;
  padding: 0;
}

.detailsPill:hover {
  background: var(--dsw-alias-button-floating-hover);
  border-color: var(--dsw-alias-border-l3);
}

.composerSeat {
  flex: none;
  display: flex;
  flex-direction: column;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--dsw-alias-bg-base) 0%, transparent) 0px,
    var(--dsw-alias-bg-base) 36px
  );
}

.toast {
  position: fixed;
  left: 50%;
  bottom: 40px;
  transform: translateX(-50%);
  z-index: 50;
  padding: 8px 16px;
  border-radius: 10px;
  background: var(--dsw-alias-toast-bg);
  color: var(--dsw-static-neutral-bluish-00);
  font-size: 13px;
  line-height: 20px;
  box-shadow: var(--dsw-shadow-lv2);
}

@media (prefers-reduced-motion: reduce) {
  .frame {
    transition: none;
  }
}
</style>

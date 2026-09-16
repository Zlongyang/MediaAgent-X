<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
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
import { ACCOUNTS, NO_ACCOUNT, defaultConfig } from './data/constants.js'
import * as api from './api/client.js'
import { mapGateRequest, mapProject, mapReview } from './api/mappers.js'

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
const projects = ref([])
const workflows = ref([])
const activeProjectId = ref('')

/* ================= 数据源（一律来自后端 /api，mock 模式已移除） ================= */
const monitorVideos = ref([])

async function reloadSources() {
  try {
    await api.health()
    const [p, w, v] = await Promise.all([api.listProjects(), api.listWorkflows(), api.listMonitorVideos()])
    projects.value = p.map(mapProject)
    workflows.value = w
    monitorVideos.value = v
  } catch (e) {
    // 诚实报错，不降级假数据（mock 演示模式已移除）
    showToast('后端不可达：请确认服务已启动（127.0.0.1:8000）')
  }
}

async function refreshWorkflows() {
  try {
    workflows.value = await api.listWorkflows()
  } catch (e) {}
}

onMounted(reloadSources)

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

let statusTimer = null
let runSeq = 0
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

function onGateConfirm(payload) {
  return realGateDecision('confirm', payload)
}

function onGateReject() {
  return realGateDecision('reject')
}
/* ================= real engine (SSE) ================= */
const STAGE_STATUS_TEXT = {
  trend_scan: '选题猎手 正在扫描热点…',
  script_draft: '编剧 正在撰写脚本…',
  storyboard: '分镜师 正在拆分镜头…',
  mpt_pipeline: '制片 正在执行流水线…',
  packaging: '包装师 正在生成标题/标签/封面…',
  publish: '发行人 正在上传发布…',
  monitoring: '分析师 正在排期数据回拉…',
  review: '分析师 正在生成复盘…',
}

let sseAbort = null
let runBrief = ''

function applyRunEvent(ev, proj, seq) {
  const d = ev.data || {}
  switch (ev.event) {
    case 'run_started':
      // 重连重放：服务端会补发全量历史，重置本 run 局部状态防重复累计
      stages.value = buildStages()
      ms.cost = { llm: 0, material: 0, tts: 0, total: 0 }
      ms.artifacts = { audio: '', subtitle: '', final: '' }
      ms.todos.forEach((t) => (t.done = false))
      ms.run_id = d.run_id
      ms.stage = 'queued'
      items.value = [{ type: 'user', text: runBrief }, { type: 'pipeline' }]
      gate.value = null
      break
    case 'stage_update': {
      const s = findStage(d.key)
      if (s) {
        s.status = d.status
        if (d.duration != null) s.duration = parseFloat(d.duration)
      }
      ms.stage = d.key
      if (d.status === 'active' && !d.key.startsWith('gate_')) startStatus(d.statusText || STAGE_STATUS_TEXT[d.key] || d.key)
      else stopStatus()
      break
    }
    case 'sub_update': {
      const pipe = findStage('mpt_pipeline')
      const sub = pipe && pipe.subs.find((x) => x.key === d.key)
      if (sub) {
        sub.status = d.status
        if (d.duration != null) sub.duration = parseFloat(d.duration)
      }
      ms.stage = d.parent + '/' + d.key
      if (d.status === 'active') startStatus(d.statusText || '制片 ' + d.key + '…')
      else stopStatus()
      break
    }
    case 'gate_request': {
      const s = findStage(d.key)
      if (s) s.status = 'gated'
      ms.stage = d.key
      stopStatus()
      gate.value = mapGateRequest(d)
      break
    }
    case 'gate_resolved':
      if (gate.value && gate.value.key === d.key) gate.value = null
      break
    case 'cost_add':
      addCost(d)
      break
    case 'artifact_set':
      ms.artifacts[d.key] = d.path
      break
    case 'todo_update':
      if (d.done) markTodo(d.id)
      break
    case 'message':
      items.value.push({ type: d.type, text: d.text })
      break
    case 'review_ready':
      ms.review_report = (d.tips || []).join('；') || '已生成'
      items.value.push({ type: 'review', review: mapReview(d) })
      break
    case 'error': {
      const s = findStage(d.stage)
      if (s) s.status = 'failed'
      stopStatus()
      items.value.push({ type: 'note', text: `ERROR ${d.stage}: ${d.message}` })
      break
    }
    case 'run_finished': {
      running.value = false
      finished.value = true
      ms.running = false
      stopStatus()
      gate.value = null
      if (d.project) {
        const p = mapProject(d.project)
        const i = projects.value.findIndex((x) => x.id === p.id)
        if (i >= 0) projects.value[i] = p
        else projects.value.unshift(p)
      } else if (proj && d.status === 'failed') {
        proj.status = 'failed'
      }
      // 以归档为准刷新一次（失败 run 保留会话占位）
      refreshProjectsFromArchive(seq)
      break
    }
  }
}

function refreshProjectsFromArchive(seq) {
  api.listProjects().then((list) => {
    if (seq !== runSeq) return
    const fetched = list.map(mapProject)
    const ids = new Set(fetched.map((p) => p.id))
    const keep = projects.value.filter((p) => p.id === sessionProjectId && !ids.has(p.id))
    projects.value = [...keep, ...fetched]
  }).catch(() => {})
}

function failRunStart(e) {
  running.value = false
  ms.running = false
  showToast('启动失败：' + (e.message || e))
}

async function startRun(text, opts = {}) {
  if (running.value) return
  const seq = ++runSeq
  running.value = true
  finished.value = false
  stages.value = buildStages()
  items.value = [{ type: 'user', text }]
  gate.value = null

  // 意图路由：周期任务 → 直接建工作流，不开流水线
  let route
  try {
    route = await api.chatRoute({ text, account: account.value })
  } catch (e) {
    return failRunStart(e)
  }
  checkSeq(seq)
  runBrief = text

  if (route && route.kind === 'workflow' && route.workflow) {
    const wf = route.workflow
    items.value.push({
      type: 'assistant',
      text: `收到，这是周期性任务。已创建工作流「${wf.name}」（cron: ${wf.schedule} · ${accountLabel(wf.account)}），到左侧「已安排工作流」可启停或立即运行。`,
    })
    running.value = false
    finished.value = true
    ms.running = false
    refreshWorkflows()
    return
  }

  let runId = ''
  try {
    const r = await api.createRun({
      text,
      account: account.value,
      autonomy: { ...ms.autonomy },
      autoMode: false,
    })
    runId = r.run_id
  } catch (e) {
    return failRunStart(e)
  }
  checkSeq(seq)

  // 项目簿记（与 mock 引擎一致）
  let proj = opts.project || null
  if (!proj) {
    proj = {
      id: runId,
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
    proj = projects.value[0]
  }
  proj.status = 'generating'
  sessionProjectId = runId
  activeProjectId.value = runId

  ms.run_id = runId
  ms.stage = 'queued'
  ms.topic = ''
  ms.cost = { llm: 0, material: 0, tts: 0, total: 0 }
  ms.artifacts = { audio: '', subtitle: '', final: '' }
  ms.review_report = ''
  ms.todos.forEach((t) => (t.done = false))
  ms.running = true

  items.value.push({ type: 'pipeline' })

  // SSE 消费 + 断线重连（重连由服务端重放历史，见 applyRunEvent run_started）
  sseAbort = new AbortController()
  let retries = 3
  while (seq === runSeq && !finished.value) {
    try {
      await api.streamRun(runId, {
        signal: sseAbort.signal,
        onEvent: (ev) => {
          if (seq !== runSeq) throw new StaleError()
          applyRunEvent(ev, proj, seq)
        },
      })
      break
    } catch (e) {
      if ((e && e.name === 'AbortError') || e instanceof StaleError || seq !== runSeq) return
      if (finished.value) break
      if (e.status && e.status < 500) retries = 0 // 4xx 不重试（如 run 不存在）
      if (retries-- <= 0) {
        gate.value = null
        items.value.push({ type: 'note', text: 'SSE 连接中断，运行结果以项目归档为准。' })
        running.value = false
        ms.running = false
        finished.value = true
        refreshProjectsFromArchive(seq)
        return
      }
      await sleep(800)
    }
  }
}

async function realGateDecision(action, payload) {
  const g = gate.value
  if (!g || !ms.run_id || ms.run_id === '—') return
  gate.value = null // 乐观关卡
  try {
    await api.resolveGate(ms.run_id, { nonce: g.nonce, action, payload: payload || {} })
  } catch (e) {
    gate.value = g // 失败恢复卡片
    showToast('闸门决议发送失败：' + (e.message || e))
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
  if (sseAbort) {
    sseAbort.abort()
    sseAbort = null
  }
  stopStatus()
  gate.value = null
  running.value = false
  finished.value = false
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
    { type: 'assistant', text: '收到，已记录到该项目备注（归档项目追问不会触发新的流水线）。' },
  ]
}

function selectProject(id) {
  activeProjectId.value = id
  const p = projects.value.find((x) => x.id === id)
  view.value = 'project'
  if (!p) return
  // 会话项目且引擎活着时，项目页对话 tab 展示 live 引擎（liveForProject）
}

function backFromProject() {
  view.value = 'chat'
}

async function onDeleteProject(id) {
  const p = projects.value.find((x) => x.id === id)
  if (!p) return
  try {
    await api.deleteProject(id)
  } catch (e) {
    showToast('删除失败：' + (e.message || e))
    return
  }
  projects.value = projects.value.filter((x) => x.id !== id)
  if (activeProjectId.value === id) backFromProject()
  showToast('已删除项目')
}

async function publishProject(p) {
  if (p.account === 'none') {
    showToast('请先在 Hero 页选择发布账号，再发起发布')
    return
  }
  try {
    const r = await api.publishProject(p.id)
    p.status = (r && r.status) || 'published'
    showToast(`已发布到 ${accountLabel(p.account)}`)
  } catch (e) {
    showToast('发布失败：' + (e.message || e))
  }
}

async function toggleWorkflow(id) {
  const w = workflows.value.find((x) => x.id === id)
  if (!w) return
  try {
    const r = await api.toggleWorkflow(id)
    w.enabled = !!r.enabled
  } catch (e) {
    showToast('切换失败：' + (e.message || e))
  }
}

async function runWorkflow(wf) {
  try {
    const r = await api.runWorkflow(wf.id)
    showToast(`已触发「${wf.name}」（${r.run_id}），完成后可在项目归档查看`)
  } catch (e) {
    showToast('触发失败：' + (e.message || e))
  }
}

async function onCreateWorkflow(payload) {
  try {
    await api.createWorkflow(payload)
    await refreshWorkflows()
    showToast('已新建工作流')
  } catch (e) {
    showToast('创建失败：' + (e.message || e))
  }
}

async function onDeleteWorkflow(id) {
  try {
    await api.deleteWorkflow(id)
    workflows.value = workflows.value.filter((w) => w.id !== id)
  } catch (e) {
    showToast('删除失败：' + (e.message || e))
  }
}

function toggleAutonomy(key) {
  if (!running.value && !finished.value) return
  ms.autonomy[key] = !ms.autonomy[key]
  if (running.value && ms.run_id && ms.run_id !== '—') {
    api.setAutonomy(ms.run_id, key, ms.autonomy[key]).catch(() => { showToast('闸门开关同步失败') })
  }
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
        @delete-project="onDeleteProject"
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
        :videos="monitorVideos"
        @open-project="selectProject"
      />

      <!-- workflows -->
      <WorkflowsView
        v-else-if="view === 'workflows'"
        :workflows="workflows"
        @toggle="toggleWorkflow"
        @run="runWorkflow"
        @create="onCreateWorkflow"
        @delete="onDeleteWorkflow"
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
        :videos="monitorVideos"
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

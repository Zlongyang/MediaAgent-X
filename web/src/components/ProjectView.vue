<script setup>
import { computed, ref, watch } from 'vue'
import ChatView from './ChatView.vue'
import GateCard from './GateCard.vue'
import Composer from './Composer.vue'
import WorkbenchPanel from './WorkbenchPanel.vue'
import ProjectOutput from './ProjectOutput.vue'
import ProjectDetail from './ProjectDetail.vue'
import ProjectMonitor from './ProjectMonitor.vue'
import { ACCOUNTS, NO_ACCOUNT } from '../data/mock.js'

const props = defineProps({
  project: { type: Object, required: true },
  live: { type: Object, default: null }, // { items, stages, gate, status } when generating
})

const emit = defineEmits(['back', 'publish', 'gate-confirm', 'gate-reject', 'toast', 'project-send'])

const TABS = [
  { key: 'chat', label: '对话' },
  { key: 'output', label: '视频产出' },
  { key: 'detail', label: '制作详情' },
  { key: 'monitor', label: '数据监控' },
]

const tab = ref('chat')
watch(() => props.project.id, () => { tab.value = 'chat' })

const accountLabel = computed(() => {
  const a = [...ACCOUNTS, NO_ACCOUNT].find((x) => x.key === props.project.account)
  return a ? a.label : '—'
})

const staticItems = computed(() => props.project.chat || [])

/* ---------------- workbench resize / collapse ---------------- */
const wbWidth = ref(320)
const wbLastWidth = ref(320)
const dragging = ref(false)

function onHandleDown(e) {
  e.preventDefault()
  dragging.value = true
  const startX = e.clientX
  const startW = wbWidth.value
  const move = (ev) => {
    let w = startW + (startX - ev.clientX)
    if (w < 240) w = 0 // drag past threshold → auto collapse
    else w = Math.min(520, Math.max(260, w))
    wbWidth.value = w
    if (w > 0) wbLastWidth.value = w
  }
  const up = () => {
    dragging.value = false
    window.removeEventListener('pointermove', move)
  }
  window.addEventListener('pointermove', move)
  window.addEventListener('pointerup', up, { once: true })
}

function toggleWb() {
  wbWidth.value = wbWidth.value === 0 ? wbLastWidth.value || 320 : 0
}

watch(
  () => wbWidth.value,
  (w) => {
    if (w > 0) wbLastWidth.value = w
  }
)

/* ---------------- 待审查：停在成片预览闸门（本地可交互演示） ---------------- */
const gatePhase = ref('pending') // pending | rerunning | confirmed
const gateNonce = ref(0)
const gateObj = computed(() => ({
  key: 'gate_preview',
  title: '成片预览',
  autonomyKey: 'preview',
  videoPath: props.project.artifacts.final || 'runs/-/video/final.mp4',
  nonce: gateNonce.value,
}))
const confirmedItems = ref([])

watch(() => props.project.id, () => {
  gatePhase.value = 'pending'
  confirmedItems.value = []
})

function onGateConfirm() {
  gatePhase.value = 'confirmed'
  confirmedItems.value = [
    ...confirmedItems.value,
    { type: 'assistant', text: '成片已确认，进入打包发布流程（演示：实际续跑请点击左侧「＋ 新对话」发起）。' },
  ]
  emit('toast', '成片已确认')
}

function onGateReject() {
  gatePhase.value = 'rerunning'
  setTimeout(() => {
    gatePhase.value = 'pending'
    gateNonce.value++
  }, 1400)
  emit('toast', '已驳回，正在重新合成视频…')
}

function onChatSend(text) {
  emit('project-send', props.project, text)
}
</script>

<template>
  <div class="project">
    <!-- top bar: back + tabs left-aligned, no title, no badge -->
    <header class="phead">
      <button class="iconButton backBtn" type="button" title="返回" aria-label="返回" @click="emit('back')">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M10 3.5L5.5 8l4.5 4.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <nav class="tabs">
        <button
          v-for="t in TABS"
          :key="t.key"
          class="tab"
          :class="{ on: tab === t.key }"
          type="button"
          @click="tab = t.key"
        >
          {{ t.label }}
        </button>
      </nav>
    </header>

    <!-- chat tab -->
    <div v-show="tab === 'chat'" class="tabBody chatSplit" :data-dragging="dragging">
      <div class="chatPane">
        <!-- live generating -->
        <ChatView
          v-if="props.project.detail === 'live' && props.live"
          :items="props.live.items"
          :stages="props.live.stages"
          :status="props.live.status"
          :gate="props.live.gate"
          @gate-confirm="(p) => emit('gate-confirm', p)"
          @gate-reject="() => emit('gate-reject')"
        />
        <!-- review: frozen at preview gate -->
        <div v-else-if="props.project.detail === 'gate'" class="staticChat">
          <div class="column">
            <template v-for="(m, i) in staticItems" :key="i">
              <div v-if="m.type === 'user'" class="uRow"><div class="uBubble">{{ m.text }}</div></div>
              <div v-else class="aMsg">{{ m.text }}</div>
            </template>
            <GateCard
              v-if="gatePhase === 'pending'"
              :key="gateNonce"
              :gate="gateObj"
              @confirm="onGateConfirm"
              @reject="onGateReject"
            />
            <div v-else-if="gatePhase === 'rerunning'" class="rerunNote">制片 正在重新合成视频…</div>
            <template v-for="(m, i) in confirmedItems" :key="'c' + i">
              <div class="aMsg">{{ m.text }}</div>
            </template>
          </div>
        </div>
        <!-- static log -->
        <div v-else class="staticChat">
          <div class="column">
            <template v-for="(m, i) in staticItems" :key="i">
              <div v-if="m.type === 'user'" class="uRow"><div class="uBubble">{{ m.text }}</div></div>
              <div v-else class="aMsg">{{ m.text }}</div>
            </template>
            <div v-if="props.project.detail === 'simple'" class="aMsg dim">
              该项目为演示占位条目，完整对话记录未收录。
            </div>
          </div>
        </div>
        <div class="composerSeat">
          <Composer @send="onChatSend" />
        </div>
      </div>

      <!-- workbench drag handle (8px hit strip straddling the border) -->
      <div
        v-if="wbWidth > 0"
        class="wbHandle"
        title="拖拽调整宽度"
        @pointerdown="onHandleDown"
      />

      <aside class="wbPane" :style="{ width: wbWidth + 'px' }" :data-closed="wbWidth === 0">
        <WorkbenchPanel v-if="wbWidth > 0" :config="props.project.config" :account-label="accountLabel" />
      </aside>

      <!-- edge toggle pill, visible in both states -->
      <button
        class="wbPill"
        :style="{ right: wbWidth + 'px' }"
        type="button"
        :title="wbWidth === 0 ? '展开工作台' : '收起工作台'"
        :aria-label="wbWidth === 0 ? '展开工作台' : '收起工作台'"
        @click="toggleWb"
      />
    </div>

    <!-- other tabs -->
    <div v-show="tab === 'output'" class="tabBody scroll">
      <ProjectOutput :project="props.project" @publish="emit('publish', props.project)" />
    </div>
    <div v-show="tab === 'detail'" class="tabBody scroll">
      <ProjectDetail :project="props.project" />
    </div>
    <div v-show="tab === 'monitor'" class="tabBody scroll">
      <ProjectMonitor :project="props.project" />
    </div>
  </div>
</template>

<style scoped>
.project {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
  overflow: hidden;
}

.phead {
  flex: none;
  display: flex;
  align-items: stretch;
  gap: 8px;
  height: 48px;
  padding: 0 16px;
  border-bottom: 1px solid var(--dsw-alias-border-l1);
  box-sizing: border-box;
  /* Apple 磨砂顶栏 */
  background: var(--dsw-alias-bg-translucent);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
}

.backBtn {
  align-self: center;
}

.iconButton {
  flex: none;
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

.tabs {
  display: flex;
  gap: 24px;
}

.tab {
  position: relative;
  display: flex;
  align-items: center;
  padding: 0 2px;
  border: none;
  background: transparent;
  font-size: 14px;
  line-height: 20px;
  color: var(--dsw-alias-label-tertiary);
  cursor: pointer;
}

.tab::after {
  content: '';
  position: absolute;
  right: 0;
  bottom: -1px;
  left: 0;
  height: 2px;
  border-radius: 2px;
  background: transparent;
}

.tab.on {
  color: var(--dsw-alias-label-primary);
  font-weight: 500;
}

.tab.on::after {
  background: var(--dsw-alias-state-business-primary);
}

.tabBody {
  flex: 1;
  min-height: 0;
  display: flex;
}

.tabBody.scroll {
  overflow-y: auto;
  display: block;
}

.chatSplit {
  position: relative;
  display: flex;
}

.chatPane {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  --dsh-chat-content-width: 748px;
  --dsh-composer-card-max-width: 780px;
  --dsh-composer-side-clearance: 16px;
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

.wbHandle {
  flex: none;
  width: 8px;
  margin-left: -4px;
  margin-right: -4px;
  cursor: col-resize;
  z-index: 2;
  touch-action: none;
}

.wbHandle:hover {
  background: var(--dsw-alias-interactive-bg-hover);
}

.wbPane {
  flex: none;
  border-left: 1px solid var(--dsw-alias-border-l2);
  overflow: hidden;
  transition: width var(--ds-transition-duration-slow) var(--ds-ease-in-out);
}

.wbPane[data-closed='true'] {
  border-left: none;
}

.chatSplit[data-dragging='true'] .wbPane {
  transition: none;
}

.wbPill {
  position: absolute;
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
  transition: right var(--ds-transition-duration-slow) var(--ds-ease-in-out),
    background-color var(--ds-transition-duration-fast) var(--ds-ease-in-out);
}

.chatSplit[data-dragging='true'] .wbPill {
  transition: none;
}

.wbPill:hover {
  background: var(--dsw-alias-button-floating-hover);
  border-color: var(--dsw-alias-border-l3);
}

.staticChat {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 32px;
}

.staticChat .column {
  max-width: 748px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.uRow {
  display: flex;
  justify-content: flex-end;
}

.uBubble {
  max-width: min(525px, 82%);
  background: var(--dsw-specific-bubble);
  border-radius: 22px;
  padding: 10px 16px;
  font-size: 16px;
  line-height: 24px;
  color: var(--dsw-alias-label-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.aMsg {
  font-size: 16px;
  line-height: 24px;
  color: var(--dsw-alias-label-primary);
  white-space: pre-wrap;
}

.aMsg.dim {
  color: var(--dsw-alias-label-tertiary);
  font-size: 13px;
}

.rerunNote {
  font-size: 14px;
  line-height: 22px;
  color: var(--dsw-alias-state-business-primary);
}

@media (prefers-reduced-motion: reduce) {
  .wbPane,
  .wbPill {
    transition: none;
  }
}
</style>

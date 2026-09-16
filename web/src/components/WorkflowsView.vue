<script setup>
// 栏目页 · 已安排工作流（cron 风格）
import { ref } from 'vue'
import { ACCOUNTS, NO_ACCOUNT } from '../data/constants.js'

const props = defineProps({
  workflows: { type: Array, required: true },
})

const emit = defineEmits(['toggle', 'run', 'create', 'delete'])

const acctLabel = (key) =>
  ([...ACCOUNTS, NO_ACCOUNT].find((a) => a.key === key) || {}).label || key

const runningId = ref('')
function runNow(wf) {
  runningId.value = wf.id
  emit('run', wf)
  setTimeout(() => {
    if (runningId.value === wf.id) runningId.value = ''
  }, 1600)
}

/* 新建表单 */
const showForm = ref(false)
const formErr = ref('')
const draft = ref({ name: '', desc: '', schedule: '', account: 'dy-shuma', brief: '', enabled: true })
const CRON_RE = /^\S+(\s+\S+){4}$/

function submitForm() {
  const d = draft.value
  if (!d.name.trim()) {
    formErr.value = '请填写名称'
    return
  }
  if (!CRON_RE.test(d.schedule.trim())) {
    formErr.value = 'cron 表达式必须是 5 段（分 时 日 月 周），如：40 7 * * *'
    return
  }
  formErr.value = ''
  emit('create', {
    name: d.name.trim(),
    desc: d.desc.trim(),
    schedule: d.schedule.trim(),
    account: d.account,
    brief: d.brief.trim() || d.name.trim(),
    enabled: !!d.enabled,
  })
  draft.value = { name: '', desc: '', schedule: '', account: d.account, brief: '', enabled: true }
  showForm.value = false
}

function toggleForm() {
  showForm.value = !showForm.value
  formErr.value = ''
}
function cancelForm() {
  showForm.value = false
  formErr.value = ''
}

/* 删除两步确认：先武装，3 秒内再点才执行 */
const armingId = ref('')
let armTimer = null
function onDeleteClick(id) {
  if (armingId.value === id) {
    armingId.value = ''
    clearTimeout(armTimer)
    emit('delete', id)
    return
  }
  armingId.value = id
  clearTimeout(armTimer)
  armTimer = setTimeout(() => (armingId.value = ''), 3000)
}
</script>

<template>
  <div class="wfs">
    <div class="wHead">
      <h1 class="wTitle">已安排工作流</h1>
      <div class="wSub">{{ props.workflows.filter((w) => w.enabled).length }} 个启用中 · cron 调度</div>
    </div>

    <div class="wfOps">
      <button class="newBtn" type="button" @click="toggleForm">
        {{ showForm ? '收起' : '＋ 新建工作流' }}
      </button>
    </div>

    <div v-if="showForm" class="wfForm">
      <label class="ff"><span>名称</span><input v-model="draft.name" class="fi" placeholder="数码赛道 · 每日日更" /></label>
      <label class="ff"><span>cron</span><input v-model="draft.schedule" class="fi mono" placeholder="40 7 * * *" /></label>
      <label class="ff"><span>账号</span>
        <select v-model="draft.account" class="fi">
          <option v-for="a in [...ACCOUNTS, NO_ACCOUNT]" :key="a.key" :value="a.key">{{ a.label }}</option>
        </select>
      </label>
      <label class="ff"><span>描述</span><input v-model="draft.desc" class="fi" placeholder="每天 07:40 自动跑完整流水线" /></label>
      <label class="ff"><span>任务</span><input v-model="draft.brief" class="fi" placeholder="做一条数码赛道的短视频" /></label>
      <div v-if="formErr" class="ffErr">{{ formErr }}</div>
      <div class="ffOps">
        <button class="btnGhost" type="button" @click="cancelForm">取消</button>
        <button class="btnPrimary" type="button" @click="submitForm">创建</button>
      </div>
    </div>

    <div class="rows">
      <div v-for="wf in props.workflows" :key="wf.id" class="row" :data-off="!wf.enabled">
        <div class="cell main">
          <div class="wfName">{{ wf.name }}</div>
          <div class="wfDesc">{{ wf.desc }}</div>
        </div>
        <div class="cell sched">
          <span class="cron mono">{{ wf.schedule }}</span>
        </div>
        <div class="cell next">
          <span class="k">下次运行</span>
          <span class="v">{{ wf.next }}</span>
        </div>
        <div class="cell acct">{{ acctLabel(wf.account) }}</div>
        <div class="cell ops">
          <button
            class="switch"
            :data-on="wf.enabled"
            type="button"
            :title="wf.enabled ? '停用' : '启用'"
            @click="emit('toggle', wf.id)"
          >
            <span class="knob" />
          </button>
          <button
            class="runBtn"
            type="button"
            :disabled="runningId === wf.id"
            @click="runNow(wf)"
          >
            {{ runningId === wf.id ? '已触发' : '立即运行' }}
          </button>
          <button
            class="delBtn"
            :data-armed="armingId === wf.id"
            type="button"
            :title="armingId === wf.id ? '再次点击确认删除' : '删除'"
            @click="onDeleteClick(wf.id)"
          >
            {{ armingId === wf.id ? '确认删除？' : '删除' }}
          </button>
        </div>
      </div>
      <div v-if="!props.workflows.length" class="emptyText">暂无已安排工作流。点上方「＋ 新建工作流」，或在对话框里让总编帮你建（如「每天早上 8 点做一条数码视频」）。</div>
    </div>
  </div>
</template>

<style scoped>
.wfs {
  height: 100%;
  overflow-y: auto;
  padding: 24px 32px 40px;
  box-sizing: border-box;
}

.wHead {
  max-width: 960px;
  margin: 0 auto 16px;
}

.wfOps {
  max-width: 960px;
  margin: 0 auto 12px;
}

.newBtn {
  height: 30px;
  padding: 0 14px;
  border: 1px solid var(--dsw-alias-border-l2);
  border-radius: 999px;
  background: var(--dsw-alias-button-elevated-fill);
  color: var(--dsw-alias-label-primary);
  font-size: 13px;
  cursor: pointer;
}

.wfForm {
  max-width: 960px;
  margin: 0 auto 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border: 1px solid var(--dsw-alias-border-l1);
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
}

.ff {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--dsw-alias-label-secondary);
}

.ff > span {
  flex: none;
  width: 44px;
}

.fi {
  flex: 1;
  height: 30px;
  padding: 0 10px;
  border: 1px solid var(--dsw-alias-border-l2);
  border-radius: 8px;
  background: var(--dsw-alias-bg-base);
  color: var(--dsw-alias-label-primary);
  font-size: 13px;
}

.ffErr {
  font-size: 12px;
  color: var(--dsw-alias-state-error-primary);
}

.ffOps {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btnPrimary {
  height: 30px;
  padding: 0 16px;
  border: none;
  border-radius: 999px;
  background: var(--dsw-alias-button-primary-fill);
  color: var(--dsw-alias-label-primary-foreground);
  font-size: 13px;
  cursor: pointer;
}

.btnGhost {
  height: 30px;
  padding: 0 14px;
  border: 1px solid var(--dsw-alias-border-l3);
  border-radius: 999px;
  background: transparent;
  color: var(--dsw-alias-label-secondary);
  font-size: 13px;
  cursor: pointer;
}

.delBtn {
  height: 26px;
  padding: 0 10px;
  border: 1px solid var(--dsw-alias-border-l2);
  border-radius: 999px;
  background: transparent;
  color: var(--dsw-alias-state-error-primary);
  font-size: 12px;
  cursor: pointer;
}

.newBtn:hover,
.btnGhost:hover,
.delBtn:hover {
  background: var(--dsw-alias-interactive-bg-hover);
}

.btnPrimary:hover {
  background: var(--dsw-alias-button-primary-hover);
}

.fi:focus {
  outline: none;
  border-color: var(--dsw-alias-state-business-primary);
}

.delBtn[data-armed='true'] {
  border-color: var(--dsw-alias-state-error-primary);
  background: var(--dsw-alias-state-error-primary);
  color: var(--dsw-alias-label-primary-foreground);
}

.emptyText {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 0;
  font-size: 13px;
  line-height: 20px;
  color: var(--dsw-alias-label-tertiary);
  text-align: center;
}

.wTitle {
  margin: 0;
  font-size: 20px;
  line-height: 28px;
  font-weight: 600;
  color: var(--dsw-alias-label-primary);
}

.wSub {
  margin-top: 4px;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-caption);
}

.rows {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.row {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 12px 16px;
  border: 1px solid var(--dsw-alias-border-l1);
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
}

.row[data-off='true'] .main,
.row[data-off='true'] .sched,
.row[data-off='true'] .next,
.row[data-off='true'] .acct {
  opacity: 0.5;
}

.cell.main {
  flex: 1.4;
  min-width: 0;
}

.wfName {
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  color: var(--dsw-alias-label-primary);
}

.wfDesc {
  margin-top: 2px;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-tertiary);
}

.cell.sched {
  flex: none;
}

.cron {
  padding: 3px 8px;
  border-radius: 6px;
  background: var(--dsw-alias-markdown-inline-code);
  font-family: var(--ds-font-family-code);
  font-size: 12px;
  color: var(--dsw-alias-label-secondary);
}

.cell.next {
  flex: none;
  width: 110px;
  display: flex;
  flex-direction: column;
}

.cell.next .k {
  font-size: 11px;
  line-height: 16px;
  color: var(--dsw-alias-label-caption);
}

.cell.next .v {
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-primary);
}

.cell.acct {
  flex: none;
  width: 120px;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell.ops {
  flex: none;
  display: flex;
  align-items: center;
  gap: 10px;
}

.switch {
  position: relative;
  width: 28px;
  height: 16px;
  border: none;
  border-radius: 999px;
  background: var(--dsw-alias-label-dimmed);
  cursor: pointer;
  transition: background-color var(--ds-transition-duration) var(--ds-ease-in-out);
  padding: 0;
}

.switch[data-on='true'] {
  background: var(--dsw-alias-state-business-primary);
}

.knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--dsw-static-neutral-00);
  transition: transform var(--ds-transition-duration) var(--ds-ease-in-out);
}

.switch[data-on='true'] .knob {
  transform: translateX(12px);
}

.runBtn {
  height: 28px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid var(--dsw-alias-border-l3);
  background: transparent;
  color: var(--dsw-alias-label-secondary);
  font-size: 12px;
  line-height: 18px;
  font-weight: 500;
  cursor: pointer;
}

.runBtn:hover:not(:disabled) {
  background: var(--dsw-alias-interactive-bg-hover);
}

.runBtn:disabled {
  color: var(--dsw-alias-state-success-primary);
  border-color: var(--dsw-alias-state-success-primary);
  cursor: default;
}

.mono {
  font-variant-numeric: tabular-nums;
}
</style>

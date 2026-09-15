<script setup>
// 栏目页 · 已安排工作流（cron 风格）
import { ref } from 'vue'
import { ACCOUNTS } from '../data/mock.js'

const props = defineProps({
  workflows: { type: Array, required: true },
})

const emit = defineEmits(['toggle', 'run'])

const acctLabel = (key) => (ACCOUNTS.find((a) => a.key === key) || {}).label || key

const runningId = ref('')
function runNow(wf) {
  runningId.value = wf.id
  emit('run', wf)
  setTimeout(() => { if (runningId.value === wf.id) runningId.value = '' }, 1600)
}
</script>

<template>
  <div class="wfs">
    <div class="wHead">
      <h1 class="wTitle">已安排工作流</h1>
      <div class="wSub">{{ props.workflows.filter((w) => w.enabled).length }} 个启用中 · cron 调度</div>
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
        </div>
      </div>
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

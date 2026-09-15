<script setup>
const props = defineProps({
  state: { type: Object, required: true },
})

const emit = defineEmits(['toggle-autonomy'])

const yuan = (n) => '¥' + Number(n).toFixed(2)

const GATE_LABELS = {
  topic: '选题确认',
  script: '脚本确认',
  preview: '成片预览',
  publish: '发布确认',
}
</script>

<template>
  <aside class="details">
    <div class="dTitle">运行状态</div>

    <div class="kv">
      <span class="k">run_id</span>
      <span class="v mono">{{ props.state.run_id }}</span>
    </div>
    <div class="kv">
      <span class="k">stage</span>
      <span class="v mono stageVal" :data-live="props.state.running">{{ props.state.stage }}</span>
    </div>
    <div class="kv">
      <span class="k">topic</span>
      <span class="v">{{ props.state.topic || '—' }}</span>
    </div>

    <div class="dSub">autonomy · 闸门开关</div>
    <div v-for="(on, key) in props.state.autonomy" :key="key" class="kv toggleRow">
      <span class="k">{{ key }}</span>
      <button
        class="switch"
        :data-on="on"
        type="button"
        :title="GATE_LABELS[key] + (on ? '（需人工确认）' : '（自动放行）')"
        @click="emit('toggle-autonomy', key)"
      >
        <span class="knob" />
      </button>
      <span class="v mono boolVal" :data-on="on">{{ on }}</span>
    </div>

    <div class="dSub">cost · 分阶段记账</div>
    <div class="kv"><span class="k">LLM</span><span class="v mono">{{ yuan(props.state.cost.llm) }}</span></div>
    <div class="kv"><span class="k">素材</span><span class="v mono">{{ yuan(props.state.cost.material) }}</span></div>
    <div class="kv"><span class="k">TTS</span><span class="v mono">{{ yuan(props.state.cost.tts) }}</span></div>
    <div class="kv total"><span class="k">合计</span><span class="v mono">{{ yuan(props.state.cost.total) }}</span></div>

    <div class="dSub">artifacts · 路径指针</div>
    <div class="kv"><span class="k">audio</span><span class="v mono path">{{ props.state.artifacts.audio || '—' }}</span></div>
    <div class="kv"><span class="k">subtitle</span><span class="v mono path">{{ props.state.artifacts.subtitle || '—' }}</span></div>
    <div class="kv"><span class="k">final</span><span class="v mono path">{{ props.state.artifacts.final || '—' }}</span></div>

    <div class="dSub">review_report</div>
    <div class="reviewVal mono">{{ props.state.review_report || '—' }}</div>

    <div class="dSub">todos</div>
    <ul class="todos">
      <li v-for="t in props.state.todos" :key="t.id" :data-done="t.done">
        <span class="cbx" aria-hidden="true">
          <svg v-if="t.done" width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M1.5 5.2l2.2 2.2 4.6-4.8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </span>
        <span class="todoText">{{ t.text }}</span>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
.details {
  height: 100%;
  overflow-y: auto;
  padding: 16px 16px 24px;
  box-sizing: border-box;
  font-size: 13px;
  line-height: 20px;
  color: var(--dsw-alias-label-primary);
}

.dTitle {
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-caption);
  margin-bottom: 10px;
}

.dSub {
  margin: 16px 0 6px;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-caption);
}

.kv {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 3px 0;
  min-width: 0;
}

.k {
  flex: none;
  width: 64px;
  color: var(--dsw-alias-label-tertiary);
  font-family: var(--ds-font-family-code);
  font-size: 12px;
}

.v {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mono {
  font-family: var(--ds-font-family-code);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.stageVal[data-live='true'] {
  color: var(--dsw-alias-state-business-primary);
}

.kv.total .k,
.kv.total .v {
  color: var(--dsw-alias-label-primary);
  font-weight: 600;
}

.path {
  font-size: 11px;
  color: var(--dsw-alias-label-secondary);
}

.toggleRow .switch {
  flex: none;
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

.boolVal {
  flex: none;
  width: 32px;
  color: var(--dsw-alias-label-caption);
}

.boolVal[data-on='true'] {
  color: var(--dsw-alias-state-business-primary);
}

.reviewVal {
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--dsw-alias-markdown-code-block);
  border: 1px solid var(--dsw-alias-border-l1);
  color: var(--dsw-alias-label-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

.todos {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.todos li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.cbx {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  margin-top: 3px;
  border: 1px solid var(--dsw-alias-border-l3);
  border-radius: 4px;
  color: var(--dsw-alias-label-primary-inverted);
  background: transparent;
}

body[data-ds-dark-theme] .cbx {
  color: var(--dsw-static-neutral-bluish-1000);
}

li[data-done='true'] .cbx {
  background: var(--dsw-alias-state-success-primary);
  border-color: var(--dsw-alias-state-success-primary);
}

.todoText {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  line-height: 20px;
}

li[data-done='true'] .todoText {
  color: var(--dsw-alias-label-tertiary);
  text-decoration: line-through;
}
</style>

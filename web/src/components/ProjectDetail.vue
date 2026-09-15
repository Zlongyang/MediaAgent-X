<script setup>
// 制作详情 tab：阶段耗时/成本表 + 分镜表 + 阶段日志（失败标红）
import AppIcon from './AppIcon.vue'

const props = defineProps({
  project: { type: Object, required: true },
})

const yuan = (n) => (n ? '¥' + n.toFixed(2) : '—')

function totals(stages) {
  const t = { llm: 0, material: 0, tts: 0 }
  for (const s of stages) {
    if (s.status !== 'pending') {
      t.llm += s.llm
      t.material += s.material
      t.tts += s.tts
    }
  }
  t.total = t.llm + t.material + t.tts
  return t
}
</script>

<template>
  <div class="detail">
    <div v-if="props.project.stages.length" class="card">
      <div class="cardTitle">阶段耗时与成本</div>
      <table class="tbl">
        <thead>
          <tr><th>阶段</th><th>工种</th><th>耗时</th><th>LLM</th><th>素材</th><th>TTS</th></tr>
        </thead>
        <tbody>
          <tr v-for="s in props.project.stages" :key="s.key" :data-status="s.status">
            <td class="mono stg">
              <AppIcon v-if="s.status === 'failed'" name="close" :size="11" class="failMark" />
              {{ s.name }}
            </td>
            <td class="agentCell">
              <AppIcon v-if="s.icon" :name="s.icon" :size="13" />
              {{ s.agent }}
            </td>
            <td class="mono">{{ s.duration != null ? s.duration.toFixed(1) + 's' : '—' }}</td>
            <td class="mono">{{ yuan(s.llm) }}</td>
            <td class="mono">{{ yuan(s.material) }}</td>
            <td class="mono">{{ yuan(s.tts) }}</td>
          </tr>
          <tr class="sumRow">
            <td>合计</td><td />
            <td />
            <td class="mono">{{ yuan(totals(props.project.stages).llm) }}</td>
            <td class="mono">{{ yuan(totals(props.project.stages).material) }}</td>
            <td class="mono">{{ yuan(totals(props.project.stages).tts) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="props.project.shots.length" class="card">
      <div class="cardTitle">分镜表 · {{ props.project.shots.length }} 个镜头</div>
      <table class="tbl">
        <thead>
          <tr><th>#</th><th>台词 narration</th><th>画面 visual</th><th>搜索词 search_term</th><th>时长</th></tr>
        </thead>
        <tbody>
          <tr v-for="sh in props.project.shots" :key="sh.idx">
            <td class="mono">{{ sh.idx }}</td>
            <td class="narr">{{ sh.narration }}</td>
            <td class="vis">{{ sh.visual }}</td>
            <td class="mono term">{{ sh.search }}</td>
            <td class="mono">{{ sh.duration }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="props.project.logs.length" class="card">
      <div class="cardTitle">阶段日志</div>
      <pre class="logBlock"><code
        v-for="(l, i) in props.project.logs"
        :key="i"
        :class="{ err: l.includes('ERROR') || l.includes('FAIL'), dim: l.includes('pending') }"
      >{{ l }}
</code></pre>
    </div>
  </div>
</template>

<style scoped>
.detail {
  padding: 16px 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 960px;
  margin: 0 auto;
}

.card {
  border: 1px solid var(--dsw-alias-border-l1);
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
  padding: 16px;
  overflow-x: auto;
}

.cardTitle {
  font-size: 13px;
  font-weight: 600;
  line-height: 20px;
  color: var(--dsw-alias-label-primary);
  margin-bottom: 10px;
}

.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  line-height: 20px;
  white-space: nowrap;
}

.tbl th {
  text-align: left;
  font-weight: 500;
  font-size: 12px;
  color: var(--dsw-alias-label-caption);
  padding: 4px 12px 6px 0;
  border-bottom: 1px solid var(--dsw-alias-border-l2);
}

.tbl td {
  padding: 6px 12px 6px 0;
  border-bottom: 1px solid var(--dsw-alias-border-l1);
  color: var(--dsw-alias-label-primary);
  vertical-align: top;
}

.tbl tr:last-child td {
  border-bottom: none;
}

tr[data-status='failed'] td {
  color: var(--dsw-alias-state-error-primary);
}

.failMark {
  display: inline-block;
  margin-right: 4px;
  vertical-align: -1px;
}

.agentCell {
  white-space: nowrap;
}

.agentCell svg {
  display: inline-block;
  vertical-align: -2px;
  margin-right: 4px;
}

tr[data-status='pending'] td {
  color: var(--dsw-alias-label-dimmed);
}

.sumRow td {
  font-weight: 600;
  border-top: 1px solid var(--dsw-alias-border-l2);
}

.mono {
  font-family: var(--ds-font-family-code);
  font-variant-numeric: tabular-nums;
}

.narr,
.vis {
  white-space: normal;
  min-width: 180px;
  color: var(--dsw-alias-label-secondary);
}

.term {
  color: var(--dsw-alias-label-tertiary);
  font-size: 12px;
}

.logBlock {
  margin: 0;
  padding: 12px 14px;
  border-radius: 8px;
  background: var(--dsw-alias-markdown-code-block);
  border: 1px solid var(--dsw-alias-border-l1);
  font-family: var(--ds-font-family-code);
  font-size: 12px;
  line-height: 19px;
  color: var(--dsw-alias-label-secondary);
  overflow-x: auto;
}

.logBlock code {
  display: block;
  white-space: pre;
}

.logBlock code.err {
  color: var(--dsw-alias-state-error-primary);
}

.logBlock code.dim {
  color: var(--dsw-alias-label-caption);
}
</style>

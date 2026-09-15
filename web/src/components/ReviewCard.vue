<script setup>
import AppIcon from './AppIcon.vue'

const props = defineProps({
  review: { type: Object, required: true },
})

const yuan = (n) => '¥' + Number(n).toFixed(2)
</script>

<template>
  <div class="review">
    <div class="rHead">
      <span class="rTitle"><AppIcon name="trending" :size="14" /> 复盘报告</span>
      <span class="rSub mono">{{ props.review.runId }} · T+1h 快照</span>
    </div>

    <table class="rTable">
      <thead>
        <tr>
          <th>指标</th>
          <th>数值</th>
          <th>环比账号均值</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in props.review.metrics" :key="m.label">
          <td>{{ m.label }}</td>
          <td class="mono">{{ m.value }}</td>
          <td :class="{ up: (m.delta || '').startsWith('+'), down: (m.delta || '').startsWith('-') }" class="mono">
            {{ m.delta }}
          </td>
        </tr>
      </tbody>
    </table>

    <div class="rCost">
      <span class="rCostTitle">本轮成本</span>
      <span class="mono">LLM {{ yuan(props.review.cost.llm) }}</span>
      <span class="mono">素材 {{ yuan(props.review.cost.material) }}</span>
      <span class="mono">TTS {{ yuan(props.review.cost.tts) }}</span>
      <span class="mono total">合计 {{ yuan(props.review.cost.total) }}</span>
    </div>

    <div class="rTips">
      <div class="rTipsTitle">反哺建议</div>
      <ul>
        <li v-for="t in props.review.tips" :key="t">{{ t }}</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.review {
  border: 1px solid var(--dsw-alias-border-l1);
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
  padding: 16px;
}

.rHead {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.rTitle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  line-height: 22px;
  color: var(--dsw-alias-label-primary);
}

.rSub {
  font-size: 11px;
  line-height: 16px;
  color: var(--dsw-alias-label-caption);
}

.mono {
  font-family: var(--ds-font-family-code);
  font-variant-numeric: tabular-nums;
}

.rTable {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  line-height: 20px;
}

.rTable th {
  text-align: left;
  font-weight: 500;
  font-size: 12px;
  color: var(--dsw-alias-label-caption);
  padding: 4px 8px 6px 0;
  border-bottom: 1px solid var(--dsw-alias-border-l2);
}

.rTable td {
  padding: 6px 8px 6px 0;
  border-bottom: 1px solid var(--dsw-alias-border-l1);
  color: var(--dsw-alias-label-primary);
}

.rTable tr:last-child td {
  border-bottom: none;
}

.up {
  color: var(--dsw-alias-state-success-primary);
}

.down {
  color: var(--dsw-alias-state-error-primary);
}

.rCost {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  align-items: baseline;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-secondary);
}

.rCostTitle {
  font-weight: 500;
  color: var(--dsw-alias-label-primary);
}

.rCost .total {
  color: var(--dsw-alias-label-primary);
  font-weight: 500;
}

.rTips {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--dsw-alias-state-business-tertiary);
}

.rTipsTitle {
  font-size: 12px;
  font-weight: 500;
  line-height: 18px;
  color: var(--dsw-alias-label-primary-bluish);
  margin-bottom: 4px;
}

.rTips ul {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 22px;
  color: var(--dsw-alias-label-secondary);
}
</style>

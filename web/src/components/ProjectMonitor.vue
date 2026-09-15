<script setup>
// 数据监控 tab：四次回拉快照表 + 趋势图 + 复盘建议
import { computed } from 'vue'
import LineChart from './LineChart.vue'

const props = defineProps({
  project: { type: Object, required: true },
})

const fmt = (n) => (n >= 10000 ? (n / 10000).toFixed(1) + 'w' : n.toLocaleString())

const series = computed(() => props.project.snapshots.map((s) => ({ label: s.t, value: s.play })))
</script>

<template>
  <div class="pmonitor">
    <template v-if="props.project.snapshots.length">
      <div class="card">
        <div class="cardTitle">回拉快照 · metrics_snapshots</div>
        <table class="tbl">
          <thead>
            <tr><th>回拉</th><th>播放</th><th>点赞</th><th>评论</th><th>分享</th></tr>
          </thead>
          <tbody>
            <tr v-for="s in props.project.snapshots" :key="s.t">
              <td class="mono">{{ s.t }}</td>
              <td class="mono">{{ fmt(s.play) }}</td>
              <td class="mono">{{ fmt(s.like) }}</td>
              <td class="mono">{{ fmt(s.comment) }}</td>
              <td class="mono">{{ fmt(s.share) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card">
        <div class="cardTitle">播放趋势</div>
        <LineChart :series="series" />
      </div>

      <div v-if="props.project.tips.length" class="tips">
        <div class="tipsTitle">复盘建议</div>
        <ul>
          <li v-for="t in props.project.tips" :key="t">{{ t }}</li>
        </ul>
      </div>
    </template>

    <div v-else class="card empty">
      <div class="cardTitle">回拉快照</div>
      <p class="emptyText">尚未发布或暂无回拉数据。发布后分析师将按 T+1h / T+6h / T+24h / T+7d 自动回拉。</p>
    </div>
  </div>
</template>

<style scoped>
.pmonitor {
  padding: 16px 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 860px;
  margin: 0 auto;
}

.card {
  border: 1px solid var(--dsw-alias-border-l1);
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
  padding: 16px;
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
}

.tbl tr:last-child td {
  border-bottom: none;
}

.mono {
  font-family: var(--ds-font-family-code);
  font-variant-numeric: tabular-nums;
}

.tips {
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--dsw-alias-state-business-tertiary);
}

.tipsTitle {
  font-size: 12px;
  font-weight: 500;
  line-height: 18px;
  color: var(--dsw-alias-label-primary-bluish);
  margin-bottom: 4px;
}

.tips ul {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 22px;
  color: var(--dsw-alias-label-secondary);
}

.emptyText {
  margin: 0;
  font-size: 13px;
  line-height: 20px;
  color: var(--dsw-alias-label-tertiary);
}
</style>

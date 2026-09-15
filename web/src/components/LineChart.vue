<script setup>
import { computed } from 'vue'

const props = defineProps({
  // series: [{ label, value }]
  series: { type: Array, required: true },
  height: { type: Number, default: 120 },
})

const W = 560

const geom = computed(() => {
  const vals = props.series.map((s) => s.value)
  const max = Math.max(...vals)
  const min = Math.min(...vals, 0)
  const span = max - min || 1
  const pad = 24
  const innerW = W - pad * 2
  const innerH = props.height - 34
  const pts = props.series.map((s, i) => {
    const x = pad + (innerW * i) / Math.max(props.series.length - 1, 1)
    const y = 8 + innerH * (1 - (s.value - min) / span)
    return { x, y, ...s }
  })
  const line = pts.map((p) => `${p.x},${p.y}`).join(' ')
  const area = `${pad},${8 + innerH} ${line} ${pad + innerW},${8 + innerH}`
  return { pts, line, area, max }
})

const fmt = (n) => (n >= 10000 ? (n / 10000).toFixed(1) + 'w' : String(n))
</script>

<template>
  <svg class="chart" :viewBox="`0 0 ${W} ${props.height}`" preserveAspectRatio="none" role="img">
    <polygon class="area" :points="geom.area" />
    <polyline class="line" :points="geom.line" fill="none" />
    <g v-for="p in geom.pts" :key="p.label">
      <circle class="pt" :cx="p.x" :cy="p.y" r="3" />
      <text class="val" :x="p.x" :y="p.y - 8" text-anchor="middle">{{ fmt(p.value) }}</text>
      <text class="lab" :x="p.x" :y="props.height - 8" text-anchor="middle">{{ p.label }}</text>
    </g>
  </svg>
</template>

<style scoped>
.chart {
  display: block;
  width: 100%;
  height: auto;
}

.area {
  fill: var(--dsw-alias-state-business-tertiary);
  opacity: 0.5;
}

.line {
  stroke: var(--dsw-alias-state-business-primary);
  stroke-width: 2;
  stroke-linejoin: round;
  stroke-linecap: round;
}

.pt {
  fill: var(--dsw-alias-bg-base);
  stroke: var(--dsw-alias-state-business-primary);
  stroke-width: 2;
}

.val {
  font-family: var(--ds-font-family-code);
  font-size: 11px;
  fill: var(--dsw-alias-label-secondary);
}

.lab {
  font-size: 11px;
  fill: var(--dsw-alias-label-caption);
}
</style>

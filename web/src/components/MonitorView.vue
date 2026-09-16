<script setup>
// 栏目页 · 数据监控：账号筛选 + 已发布视频卡片 + 汇总趋势
import { computed, ref } from 'vue'
import AppIcon from './AppIcon.vue'
import LineChart from './LineChart.vue'
import { ACCOUNTS } from '../data/constants.js'

const props = defineProps({
  videos: { type: Array, default: () => [] },
})

const emit = defineEmits(['open-project'])

const filter = ref('all')

const videos = computed(() =>
  props.videos.filter((v) => filter.value === 'all' || v.account === filter.value)
)

const summarySeries = computed(() => {
  // aggregate plays of filtered videos across the 4 pull points
  const pts = [0, 0, 0, 0]
  for (const v of videos.value) (v.series || []).forEach((n, i) => (pts[i] += n))
  return pts.map((value, i) => ({ label: ['T+1h', 'T+6h', 'T+24h', 'T+7d'][i], value }))
})

const acctLabel = (key) => (ACCOUNTS.find((a) => a.key === key) || {}).label || key
const fmt = (n) => (n >= 10000 ? (n / 10000).toFixed(1) + 'w' : n.toLocaleString())
</script>

<template>
  <div class="monitor">
    <div class="mHead">
      <h1 class="mTitle">数据监控</h1>
      <div class="chipRow">
        <button
          class="fchip"
          :class="{ on: filter === 'all' }"
          type="button"
          @click="filter = 'all'"
        >
          全部账号
        </button>
        <button
          v-for="a in ACCOUNTS"
          :key="a.key"
          class="fchip"
          :class="{ on: filter === a.key }"
          type="button"
          @click="filter = a.key"
        >
          {{ a.label }}
        </button>
      </div>
    </div>

    <div class="cards">
      <div
        v-for="v in videos"
        :key="v.id"
        class="vcard"
        :class="{ link: !!v.project }"
        @click="v.project && emit('open-project', v.project)"
      >
        <div class="cover">
          <svg width="28" height="28" viewBox="0 0 44 44" fill="none">
            <circle cx="22" cy="22" r="21" class="cRing" />
            <path d="M18 15.5v13l11-6.5-11-6.5Z" class="cTri" />
          </svg>
        </div>
        <div class="vbody">
          <div class="vtitle">{{ v.title }}</div>
          <div class="vmeta">{{ acctLabel(v.account) }} · {{ v.age }}</div>
          <div class="vstats mono">
            <span class="stat"><AppIcon name="play" :size="12" /> {{ fmt(v.play) }}</span>
            <span class="stat"><AppIcon name="like" :size="12" /> {{ fmt(v.like) }}</span>
            <span class="stat"><AppIcon name="comment" :size="12" /> {{ fmt(v.comment) }}</span>
            <span class="delta" :data-up="(v.delta || '').startsWith('+')">{{ v.delta }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="sumCard">
      <div class="sumTitle">汇总播放趋势（{{ filter === 'all' ? '全部账号' : acctLabel(filter) }}）</div>
      <LineChart :series="summarySeries" :height="140" />
    </div>
  </div>
</template>

<style scoped>
.monitor {
  height: 100%;
  overflow-y: auto;
  padding: 24px 32px 40px;
  box-sizing: border-box;
}

.mHead {
  max-width: 960px;
  margin: 0 auto 16px;
}

.mTitle {
  margin: 0 0 12px;
  font-size: 20px;
  line-height: 28px;
  font-weight: 600;
  color: var(--dsw-alias-label-primary);
}

.chipRow {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.fchip {
  height: 28px;
  padding: 0 12px;
  border: 1px solid var(--dsw-alias-border-l2);
  border-radius: 14px;
  background: transparent;
  color: var(--dsw-alias-label-secondary);
  font-size: 13px;
  line-height: 20px;
  font-weight: 500;
  cursor: pointer;
}

.fchip:hover {
  background: var(--dsw-alias-interactive-bg-hover);
}

.fchip.on {
  background: var(--dsw-alias-state-business-tertiary);
  border-color: var(--dsw-alias-state-business-primary);
  color: var(--dsw-alias-state-business-primary);
}

.cards {
  max-width: 960px;
  margin: 0 auto 16px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.vcard {
  border: 1px solid var(--dsw-alias-border-l1);
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
  overflow: hidden;
}

.vcard.link {
  cursor: pointer;
}

.vcard.link:hover {
  border-color: var(--dsw-alias-border-l3);
}

.cover {
  aspect-ratio: 16 / 9;
  background: var(--dsw-static-neutral-bluish-900);
  display: grid;
  place-items: center;
}

.cRing {
  stroke: var(--dsw-static-neutral-bluish-300);
  stroke-width: 1.5;
  fill: rgba(255, 255, 255, 0.08);
}

.cTri {
  fill: var(--dsw-static-neutral-bluish-00);
}

.vbody {
  padding: 10px 12px 12px;
}

.vtitle {
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  color: var(--dsw-alias-label-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.vmeta {
  margin-top: 2px;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-caption);
}

.vstats {
  margin-top: 8px;
  display: flex;
  gap: 12px;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-secondary);
}

.stat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.delta[data-up='true'] {
  color: var(--dsw-alias-state-success-primary);
}

.delta[data-up='false'] {
  color: var(--dsw-alias-state-error-primary);
}

.mono {
  font-variant-numeric: tabular-nums;
}

.sumCard {
  max-width: 960px;
  margin: 0 auto;
  border: 1px solid var(--dsw-alias-border-l1);
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
  padding: 16px;
}

.sumTitle {
  font-size: 13px;
  font-weight: 600;
  line-height: 20px;
  color: var(--dsw-alias-label-primary);
  margin-bottom: 10px;
}
</style>

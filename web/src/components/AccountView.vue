<script setup>
// 账号数据页：头部 + 汇总指标 + 视频列表 + 播放趋势
import { computed } from 'vue'
import StatusBadge from './StatusBadge.vue'
import LineChart from './LineChart.vue'
import { ACCOUNTS, NO_ACCOUNT, ACCOUNT_FANS, MONITOR_VIDEOS } from '../data/mock.js'

const props = defineProps({
  accountKey: { type: String, required: true },
  projects: { type: Array, default: () => [] },
})

const emit = defineEmits(['back', 'open-project'])

const account = computed(
  () => [...ACCOUNTS, NO_ACCOUNT].find((a) => a.key === props.accountKey) || NO_ACCOUNT
)
const isNone = computed(() => props.accountKey === 'none')
const fans = computed(() => ACCOUNT_FANS[props.accountKey] || null)

const acctProjects = computed(() => props.projects.filter((p) => p.account === props.accountKey))
const acctVideos = computed(() => MONITOR_VIDEOS.filter((v) => v.account === props.accountKey))

const totals = computed(() => {
  const t = { play: 0, like: 0, comment: 0 }
  for (const v of acctVideos.value) {
    t.play += v.play
    t.like += v.like
    t.comment += v.comment
  }
  return t
})

const publishedCount = computed(
  () => acctProjects.value.filter((p) => p.status === 'published').length
)

const trendSeries = computed(() => {
  const pts = [0, 0, 0, 0]
  for (const v of acctVideos.value) v.series.forEach((n, i) => (pts[i] += n))
  return pts.map((value, i) => ({ label: ['T+1h', 'T+6h', 'T+24h', 'T+7d'][i], value }))
})

const fmt = (n) => (n >= 10000 ? (n / 10000).toFixed(1) + 'w' : n.toLocaleString())
</script>

<template>
  <div class="acctPage">
    <div class="aWrap">
      <!-- header -->
      <div class="aHead">
        <button class="iconButton" type="button" title="返回" aria-label="返回" @click="emit('back')">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M10 3.5L5.5 8l4.5 4.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <div class="aTitles">
          <h1 class="aName">{{ account.label }}</h1>
          <div class="aSub">
            平台 {{ account.platform }}
            <template v-if="fans"> · 粉丝 {{ fans }}</template>
            <template v-if="isNone"> · 未绑定发布账号的项目</template>
          </div>
        </div>
      </div>

      <!-- summary cards -->
      <div v-if="!isNone" class="sumGrid">
        <div class="sumCard">
          <div class="sumVal mono">{{ fmt(totals.play) }}</div>
          <div class="sumKey">总播放</div>
        </div>
        <div class="sumCard">
          <div class="sumVal mono">{{ fmt(totals.like) }}</div>
          <div class="sumKey">总点赞</div>
        </div>
        <div class="sumCard">
          <div class="sumVal mono">{{ fmt(totals.comment) }}</div>
          <div class="sumKey">总评论</div>
        </div>
        <div class="sumCard">
          <div class="sumVal mono">{{ publishedCount }}</div>
          <div class="sumKey">已发布视频</div>
        </div>
      </div>

      <!-- video list -->
      <div class="card">
        <div class="cardTitle">视频 · {{ acctProjects.length }}</div>
        <div v-if="!acctProjects.length" class="emptyText">该分组下暂无项目。</div>
        <button
          v-for="p in acctProjects"
          :key="p.id"
          class="vRow"
          type="button"
          @click="emit('open-project', p.id)"
        >
          <span class="vName">{{ p.name }}</span>
          <span class="vTime">{{ p.createdAt }}</span>
          <StatusBadge :status="p.status" />
        </button>
      </div>

      <!-- trend -->
      <div v-if="!isNone && acctVideos.length" class="card">
        <div class="cardTitle">播放趋势（汇总 {{ acctVideos.length }} 条已发布视频）</div>
        <LineChart :series="trendSeries" :height="140" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.acctPage {
  height: 100%;
  overflow-y: auto;
  padding: 24px 32px 40px;
  box-sizing: border-box;
}

.aWrap {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.aHead {
  display: flex;
  align-items: center;
  gap: 10px;
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

.aName {
  margin: 0;
  font-size: 20px;
  line-height: 28px;
  font-weight: 600;
  color: var(--dsw-alias-label-primary);
}

.aSub {
  margin-top: 2px;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-caption);
}

.sumGrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.sumCard {
  border: 1px solid var(--dsw-alias-border-l1);
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
  padding: 14px 16px;
}

.sumVal {
  font-size: 20px;
  line-height: 28px;
  font-weight: 600;
  color: var(--dsw-alias-label-primary);
}

.sumKey {
  margin-top: 2px;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-caption);
}

.mono {
  font-family: var(--ds-font-family-code);
  font-variant-numeric: tabular-nums;
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
  margin-bottom: 8px;
}

.emptyText {
  font-size: 13px;
  line-height: 20px;
  color: var(--dsw-alias-label-tertiary);
}

.vRow {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 8px;
  border: none;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.vRow:hover {
  background: var(--dsw-alias-interactive-bg-hover);
}

.vName {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  line-height: 20px;
  color: var(--dsw-alias-label-primary);
}

.vTime {
  flex: none;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-caption);
}
</style>

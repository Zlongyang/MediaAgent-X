<script setup>
import { STATUS } from '../data/constants.js'

const props = defineProps({
  status: { type: String, required: true },
})
</script>

<template>
  <span class="badge" :data-kind="STATUS[props.status].kind">
    <span class="dot" />
    <span class="txt">{{ STATUS[props.status].label }}</span>
  </span>
</template>

<style scoped>
/* 低饱和状态徽章：统一浅灰底 + 次级文字，语义色只落在小圆点上（Linear 式）。 */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--dsw-alias-interactive-bg-hover);
  color: var(--dsw-alias-label-secondary);
  font-size: 11px;
  line-height: 16px;
  font-weight: 500;
  white-space: nowrap;
}

.dot {
  flex: none;
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.badge[data-kind='business'] .dot {
  background: var(--dsw-alias-state-business-primary);
  animation: pulse 1.2s ease-in-out infinite alternate;
}

.badge[data-kind='warn'] .dot {
  background: var(--dsw-alias-state-warn-primary);
}

.badge[data-kind='success'] .dot {
  background: var(--dsw-alias-state-success-primary);
}

.badge[data-kind='error'] .dot {
  background: var(--dsw-alias-state-error-primary);
}

.badge[data-kind='neutral'] .dot {
  background: var(--dsw-alias-label-caption);
}

@keyframes pulse {
  from { opacity: 0.35; }
  to { opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
  .badge[data-kind='business'] .dot {
    animation: none;
  }
}
</style>

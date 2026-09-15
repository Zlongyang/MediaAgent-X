<script setup>
import { nextTick, ref, watch } from 'vue'
import PipelineCard from './PipelineCard.vue'
import GateCard from './GateCard.vue'
import ReviewCard from './ReviewCard.vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  status: { type: Object, default: null }, // { text, clock }
  stages: { type: Array, default: () => [] },
  gate: { type: Object, default: null },
})

const emit = defineEmits(['gate-confirm', 'gate-reject'])

const scroller = ref(null)

function scrollBottom() {
  nextTick(() => {
    const el = scroller.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

watch(() => props.items.length, scrollBottom)
watch(() => props.status && props.status.text, scrollBottom)
watch(() => props.gate && props.gate.nonce, scrollBottom)
watch(
  () => props.stages.map((s) => s.status).join(','),
  scrollBottom
)

function fmtClock(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

defineExpose({ scrollBottom })
</script>

<template>
  <div class="chat">
    <div ref="scroller" class="scroll">
      <div class="column">
        <template v-for="(item, i) in props.items" :key="i">
          <!-- user bubble -->
          <div v-if="item.type === 'user'" class="userRow">
            <div class="userStack">
              <div class="bubble">{{ item.text }}</div>
            </div>
          </div>

          <!-- assistant plain text -->
          <div v-else-if="item.type === 'assistant'" class="assistant">{{ item.text }}</div>

          <!-- pipeline -->
          <PipelineCard v-else-if="item.type === 'pipeline'" :stages="props.stages" />

          <!-- gate -->
          <GateCard
            v-else-if="item.type === 'gate'"
            :gate="item.gate"
            @confirm="(p) => emit('gate-confirm', p)"
            @reject="() => emit('gate-reject')"
          />

          <!-- review -->
          <ReviewCard v-else-if="item.type === 'review'" :review="item.review" />

          <!-- dim note line -->
          <div v-else-if="item.type === 'note'" class="note mono">{{ item.text }}</div>
        </template>

        <!-- pending gate card (live) -->
        <GateCard
          v-if="props.gate"
          :key="props.gate.nonce"
          :gate="props.gate"
          @confirm="(p) => emit('gate-confirm', p)"
          @reject="() => emit('gate-reject')"
        />

        <!-- working status shimmer -->
        <div v-if="props.status" class="turnStatus">
          <span class="statusText">{{ props.status.text }}</span>
          <span class="turnStatusClock">{{ fmtClock(props.status.clock) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1 1 auto;
}

.scroll {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 16px calc(var(--dsh-composer-side-clearance) + 16px);
}

.column {
  max-width: var(--dsh-chat-content-width);
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.userRow {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.userStack {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  min-width: 0;
  max-width: min(525px, 82%);
}

.bubble {
  max-width: 100%;
  background: var(--dsw-specific-bubble);
  border-radius: 22px;
  padding: 10px 16px;
  font-size: 16px;
  line-height: 24px;
  color: var(--dsw-alias-label-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.assistant {
  font-size: 16px;
  line-height: 24px;
  color: var(--dsw-alias-label-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.note {
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-tertiary);
}

.turnStatus {
  align-self: flex-start;
  flex: none;
  display: inline-flex;
  align-items: center;
  height: 26px;
  font: var(--dsw-font-s-strong-14);
  white-space: nowrap;
  background: linear-gradient(
    90deg,
    var(--dsw-static-deepseek-500) 0%,
    var(--dsw-static-deepseek-500) 40%,
    var(--dsw-static-deepseek-200) 50%,
    var(--dsw-static-deepseek-500) 60%,
    var(--dsw-static-deepseek-500) 100%
  );
  background-position: 100% 0;
  background-size: 250% 100%;
  background-clip: text;
  color: transparent;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: dsh-turn-status-shimmer 1.8s linear infinite;
}

.turnStatusClock {
  margin-left: 8px;
  font: var(--dsw-font-xs-13);
  font-weight: 400;
  font-variant-numeric: tabular-nums;
  color: var(--dsw-alias-label-caption);
  -webkit-text-fill-color: var(--dsw-alias-label-caption);
}

@keyframes dsh-turn-status-shimmer {
  to {
    background-position: 0 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .turnStatus {
    background-position: 0 0;
    background-size: 100% 100%;
    animation: none;
  }
}
</style>

<script setup>
import AppIcon from './AppIcon.vue'

const props = defineProps({
  stages: { type: Array, default: () => [] },
})

function fmt(sec) {
  if (sec == null) return ''
  return sec.toFixed(1) + 's'
}
</script>

<template>
  <div class="pipeline">
    <div class="pipelineHead">
      <span class="pipelineTitle">主工作流</span>
      <span class="pipelineSub">trend_scan → … → review</span>
    </div>
    <ol class="nodes">
      <template v-for="(s, i) in props.stages" :key="s.key">
        <li class="node" :data-status="s.status">
          <span v-if="i > 0" class="conn" aria-hidden="true" />
          <span class="icon" aria-hidden="true">
            <!-- done -->
            <svg v-if="s.status === 'done'" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="7" class="okBg" />
              <path d="M5 8.2l2 2 4-4.4" class="okTick" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
            </svg>
            <!-- active spinner -->
            <svg v-else-if="s.status === 'active'" class="spin" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6.5" class="spinTrack" stroke-width="1.8" />
              <path d="M14.5 8a6.5 6.5 0 0 0-6.5-6.5" class="spinArc" stroke-width="1.8" stroke-linecap="round" />
            </svg>
            <!-- gate wait -->
            <AppIcon v-else-if="s.status === 'gated'" name="gate" :size="14" class="gateMark" />
            <!-- pending -->
            <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6.5" class="todoRing" stroke-width="1.5" />
            </svg>
          </span>
          <span class="stageName">
            {{ s.name }}
            <span v-if="s.gate" class="gateTag">GATE</span>
          </span>
          <span class="stageAgent">
            <AppIcon v-if="s.icon" :name="s.icon" :size="13" />
            {{ s.agent }}
          </span>
          <span class="stageDur mono">{{ s.status === 'gated' ? '等待确认' : fmt(s.duration) }}</span>
        </li>
        <li v-if="s.subs && s.subs.length" class="subs" :data-status="s.status">
          <ol>
            <li v-for="sub in s.subs" :key="sub.key" class="node sub" :data-status="sub.status">
              <span class="conn subConn" aria-hidden="true" />
              <span class="icon" aria-hidden="true">
                <svg v-if="sub.status === 'done'" width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="7" class="okBg" />
                  <path d="M5 8.2l2 2 4-4.4" class="okTick" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
                </svg>
                <svg v-else-if="sub.status === 'active'" class="spin" width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="6.5" class="spinTrack" stroke-width="1.8" />
                  <path d="M14.5 8a6.5 6.5 0 0 0-6.5-6.5" class="spinArc" stroke-width="1.8" stroke-linecap="round" />
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="6.5" class="todoRing" stroke-width="1.5" />
                </svg>
              </span>
              <span class="stageName subName">{{ sub.name }}</span>
              <span class="stageDur mono">{{ fmt(sub.duration) }}</span>
            </li>
          </ol>
        </li>
      </template>
    </ol>
  </div>
</template>

<style scoped>
.pipeline {
  border: 1px solid var(--dsw-alias-border-l1);
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
  padding: 16px;
}

.pipelineHead {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 12px;
}

.pipelineTitle {
  font-size: 14px;
  font-weight: 600;
  line-height: 22px;
  color: var(--dsw-alias-label-primary);
}

.pipelineSub {
  font-family: var(--ds-font-family-code);
  font-size: 11px;
  line-height: 16px;
  color: var(--dsw-alias-label-caption);
}

.nodes,
.subs ol {
  list-style: none;
  margin: 0;
  padding: 0;
}

.node {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 28px;
  padding: 3px 0;
  font-size: 14px;
  line-height: 20px;
}

.conn {
  position: absolute;
  left: 7.5px;
  top: -4px;
  width: 1px;
  height: 12px;
  background: var(--dsw-alias-border-l2);
}

.icon {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
}

.okBg {
  fill: var(--dsw-alias-state-success-primary);
}

.okTick {
  stroke: var(--dsw-alias-label-primary-inverted);
}

body[data-ds-dark-theme] .okTick {
  stroke: var(--dsw-static-neutral-bluish-1000);
}

.todoRing {
  stroke: var(--dsw-alias-label-dimmed);
  fill: none;
}

.spinTrack {
  stroke: var(--dsw-alias-border-l3);
  fill: none;
}

.spinArc {
  stroke: var(--dsw-alias-state-business-primary);
  fill: none;
}

.spin {
  animation: rot 0.9s linear infinite;
}

@keyframes rot {
  to { transform: rotate(360deg); }
}

.gateMark {
  color: var(--dsw-alias-state-warn-label);
}

.gateTag {
  margin-left: 6px;
  padding: 0 6px;
  border-radius: 4px;
  background: var(--dsw-alias-state-warn-tertiary);
  color: var(--dsw-alias-state-warn-label);
  font-family: var(--ds-font-family-code);
  font-size: 10px;
  line-height: 16px;
  font-weight: 500;
  vertical-align: 1px;
}

.stageName {
  color: var(--dsw-alias-label-primary);
  white-space: nowrap;
}

.node[data-status='pending'] .stageName {
  color: var(--dsw-alias-label-tertiary);
}

.node[data-status='gated'] .stageName {
  color: var(--dsw-alias-state-warn-label);
}

.stageAgent {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--dsw-alias-label-tertiary);
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.stageDur {
  flex: none;
  color: var(--dsw-alias-label-caption);
  font-size: 12px;
}

.mono {
  font-family: var(--ds-font-family-code);
  font-variant-numeric: tabular-nums;
}

.subs {
  margin-left: 24px;
}

.sub {
  min-height: 24px;
  font-size: 13px;
}

.subName {
  font-size: 13px;
}

.sub .subConn {
  left: 6.5px;
  height: 12px;
}

@media (prefers-reduced-motion: reduce) {
  .spin {
    animation: none;
  }
}
</style>

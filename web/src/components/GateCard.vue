<script setup>
import { ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  gate: { type: Object, required: true },
})

const emit = defineEmits(['confirm', 'reject'])

const picked = ref(0)

watch(
  () => props.gate && props.gate.nonce,
  () => {
    picked.value = 0
  }
)

function confirm() {
  if (props.gate.key === 'gate_topic') {
    emit('confirm', { choice: props.gate.candidates[picked.value] })
  } else {
    emit('confirm', {})
  }
}
</script>

<template>
  <div class="gate">
    <div class="gateHead">
      <span class="gateTitle"><AppIcon name="gate" :size="14" /> 闸门 · {{ props.gate.title }}</span>
      <span class="gateHint">autonomy.{{ props.gate.autonomyKey }} = true · 等待人工确认</span>
    </div>

    <!-- 选题确认 -->
    <div v-if="props.gate.key === 'gate_topic'" class="gateBody">
      <label
        v-for="(c, i) in props.gate.candidates"
        :key="c.title"
        class="cand"
        :class="{ picked: picked === i }"
      >
        <input v-model="picked" type="radio" name="topic" :value="i" />
        <span class="candMain">
          <span class="candTitle">{{ c.title }}</span>
          <span class="candReason">{{ c.reason }}</span>
        </span>
        <span class="candMeta">
          <span class="candSrc">{{ c.source }}</span>
          <span class="candHeat mono"><AppIcon name="flame" :size="12" /> {{ c.heat }}</span>
        </span>
      </label>
    </div>

    <!-- 脚本确认 -->
    <div v-else-if="props.gate.key === 'gate_script'" class="gateBody">
      <pre class="scriptBlock">{{ props.gate.script }}</pre>
    </div>

    <!-- 成片预览 -->
    <div v-else-if="props.gate.key === 'gate_preview'" class="gateBody">
      <video
        v-if="props.gate.videoUrl"
        class="videoReal"
        :src="props.gate.videoUrl"
        controls
        preload="metadata"
      />
      <div v-else class="videoStub">
        <svg class="play" width="44" height="44" viewBox="0 0 44 44" fill="none">
          <circle cx="22" cy="22" r="21" class="playRing" />
          <path d="M18 15.5v13l11-6.5-11-6.5Z" class="playTri" />
        </svg>
        <span class="videoMeta mono">{{ props.gate.videoPath }}</span>
        <span class="videoMeta sub mono">00:58 · 1080×1920 · H.264</span>
      </div>
    </div>

    <!-- 发布确认 -->
    <div v-else-if="props.gate.key === 'gate_publish'" class="gateBody">
      <div class="pack">
        <div class="cover">
          <span class="coverText mono">cover.jpg</span>
        </div>
        <div class="packMeta">
          <div class="packTitle">{{ props.gate.pack.title }}</div>
          <div class="packTags">
            <span v-for="t in props.gate.pack.tags" :key="t" class="tag mono">#{{ t }}</span>
          </div>
          <div class="packRow mono">标题 {{ props.gate.pack.titleLen }}/30 · 简介 {{ props.gate.pack.descLen }}/100 · 封面 9:16</div>
        </div>
      </div>
    </div>

    <div class="gateFoot">
      <button class="btnGhost" type="button" @click="emit('reject')">驳回重跑</button>
      <button class="btnPrimary" type="button" @click="confirm">确认放行</button>
    </div>
  </div>
</template>

<style scoped>
.gate {
  border: 1px solid var(--dsw-alias-border-l1);
  border-left: 3px solid var(--dsw-alias-state-warn-primary);
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
  padding: 16px;
}

.gateHead {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.gateTitle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  line-height: 22px;
  color: var(--dsw-alias-label-primary);
}

.gateHint {
  font-family: var(--ds-font-family-code);
  font-size: 11px;
  line-height: 16px;
  color: var(--dsw-alias-state-warn-label);
}

.gateBody {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cand {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--dsw-alias-border-l2);
  border-radius: 10px;
  cursor: pointer;
  transition: border-color var(--ds-transition-duration-fast) var(--ds-ease-in-out),
    background-color var(--ds-transition-duration-fast) var(--ds-ease-in-out);
}

.cand:hover {
  background: var(--dsw-alias-interactive-bg-hover);
}

.cand.picked {
  border-color: var(--dsw-alias-state-business-primary);
  background: var(--dsw-alias-state-business-tertiary);
}

.cand input {
  margin: 3px 0 0;
  accent-color: var(--dsw-alias-state-business-primary);
}

.candMain {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.candTitle {
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
  color: var(--dsw-alias-label-primary);
}

.candReason {
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-tertiary);
}

.candMeta {
  flex: none;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.candSrc {
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-secondary);
}

.candHeat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-state-warn-label);
}

.mono {
  font-family: var(--ds-font-family-code);
  font-variant-numeric: tabular-nums;
}

.scriptBlock {
  margin: 0;
  padding: 12px 14px;
  border-radius: 8px;
  background: var(--dsw-alias-markdown-code-block);
  border: 1px solid var(--dsw-alias-border-l1);
  font-family: var(--ds-font-family-code);
  font-size: 12px;
  line-height: 19px;
  color: var(--dsw-alias-label-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

.videoStub {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  aspect-ratio: 16 / 9;
  border-radius: 10px;
  background: var(--dsw-static-neutral-bluish-900);
  border: 1px solid var(--dsw-alias-border-l1);
}

.videoReal {
  display: block;
  width: 100%;
  max-height: 420px;
  border-radius: 10px;
  background: var(--dsw-static-neutral-bluish-900);
  border: 1px solid var(--dsw-alias-border-l1);
}

.playRing {
  stroke: var(--dsw-static-neutral-bluish-300);
  stroke-width: 1.5;
  fill: rgba(255, 255, 255, 0.08);
}

.playTri {
  fill: var(--dsw-static-neutral-bluish-00);
}

.videoMeta {
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-static-neutral-bluish-300);
}

.videoMeta.sub {
  color: var(--dsw-static-neutral-bluish-500);
  margin-top: -4px;
}

.pack {
  display: flex;
  gap: 12px;
}

.cover {
  flex: none;
  width: 84px;
  aspect-ratio: 9 / 16;
  border-radius: 8px;
  background: var(--dsw-alias-bg-skeleton);
  border: 1px solid var(--dsw-alias-border-l2);
  display: grid;
  place-items: center;
}

.coverText {
  font-size: 10px;
  color: var(--dsw-alias-label-caption);
}

.packMeta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.packTitle {
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
  color: var(--dsw-alias-label-primary);
}

.packTags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  padding: 1px 8px;
  border-radius: 10px;
  background: var(--dsw-alias-state-business-tertiary);
  color: var(--dsw-alias-label-primary-bluish);
  font-size: 11px;
  line-height: 16px;
}

.packRow {
  font-size: 11px;
  line-height: 16px;
  color: var(--dsw-alias-label-caption);
}

.gateFoot {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btnPrimary,
.btnGhost {
  height: 32px;
  padding: 0 16px;
  border-radius: 999px;
  font-size: 13px;
  line-height: 20px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background-color var(--ds-transition-duration-fast) var(--ds-ease-in-out);
}

.btnPrimary {
  background: var(--dsw-alias-button-primary-fill);
  color: var(--dsw-alias-label-primary-foreground);
}

.btnPrimary:hover {
  background: var(--dsw-alias-button-primary-hover);
}

.btnGhost {
  background: transparent;
  border-color: var(--dsw-alias-border-l3);
  color: var(--dsw-alias-label-secondary);
}

.btnGhost:hover {
  background: var(--dsw-alias-interactive-bg-hover);
}
</style>

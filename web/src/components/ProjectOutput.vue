<script setup>
// 视频产出 tab：成片播放器占位 + 工件列表 + 平台打包结果
import AppIcon from './AppIcon.vue'

const props = defineProps({
  project: { type: Object, required: true },
})

const emit = defineEmits(['publish'])

const ARTIFACT_LABELS = { audio: 'audio · 配音', subtitle: 'subtitle · 字幕', cover: 'cover · 封面', final: 'final · 成片' }
</script>

<template>
  <div class="output">
    <!-- player -->
    <div class="playerCard">
      <div v-if="props.project.video" class="videoStub">
        <svg class="play" width="48" height="48" viewBox="0 0 44 44" fill="none">
          <circle cx="22" cy="22" r="21" class="playRing" />
          <path d="M18 15.5v13l11-6.5-11-6.5Z" class="playTri" />
        </svg>
        <span class="durBadge mono">{{ props.project.video.duration }}</span>
        <span class="videoMeta mono">{{ props.project.artifacts.final }}</span>
        <span class="videoMeta sub mono">{{ props.project.video.res }} · H.264</span>
      </div>
      <div v-else class="videoStub empty">
        <span class="videoMeta">成片尚未生成</span>
      </div>
      <div class="playerFoot">
        <span class="pfName">{{ props.project.name }}</span>
        <button
          v-if="props.project.status === 'unpublished'"
          class="btnPrimary"
          type="button"
          @click="emit('publish')"
        >
          <AppIcon name="rocket" :size="13" /> 发布
        </button>
      </div>
    </div>

    <div class="outGrid">
      <!-- artifacts -->
      <div class="card">
        <div class="cardTitle">工件</div>
        <div v-for="(label, key) in ARTIFACT_LABELS" :key="key" class="artRow">
          <span class="artLabel">{{ label }}</span>
          <span class="artPath mono">{{ props.project.artifacts[key] || '—' }}</span>
          <button
            class="iconButton"
            type="button"
            :disabled="!props.project.artifacts[key]"
            title="下载"
            aria-label="下载"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 2v7M3.8 6.2L7 9.4l3.2-3.2M2.5 11.5h9" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
      </div>

      <!-- pack result -->
      <div v-if="props.project.pack" class="card">
        <div class="cardTitle">打包结果 · {{ props.project.pack.platform }}</div>
        <div class="packTitle">{{ props.project.pack.title }}</div>
        <div class="packCaption">{{ props.project.pack.caption }}</div>
        <div class="packTags">
          <span v-for="t in props.project.pack.tags" :key="t" class="tag mono">#{{ t }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.output {
  padding: 16px 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1080px;
  margin: 0 auto;
}

.outGrid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.outGrid .card {
  min-width: 0;
}

.playerCard,
.card {
  border: 1px solid var(--dsw-alias-border-l1);
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
  padding: 16px;
}

.videoStub {
  position: relative;
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

.videoStub.empty {
  background: var(--dsw-alias-bg-skeleton);
}

.videoStub.empty .videoMeta {
  color: var(--dsw-alias-label-caption);
}

.playRing {
  stroke: var(--dsw-static-neutral-bluish-300);
  stroke-width: 1.5;
  fill: rgba(255, 255, 255, 0.08);
}

.playTri {
  fill: var(--dsw-static-neutral-bluish-00);
}

.durBadge {
  position: absolute;
  right: 10px;
  bottom: 10px;
  padding: 1px 6px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.55);
  color: var(--dsw-static-neutral-bluish-00);
  font-size: 11px;
  line-height: 16px;
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

.mono {
  font-family: var(--ds-font-family-code);
  font-variant-numeric: tabular-nums;
}

.playerFoot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
}

.pfName {
  font-size: 14px;
  font-weight: 500;
  line-height: 22px;
  color: var(--dsw-alias-label-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btnPrimary {
  flex: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 16px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: var(--dsw-alias-button-primary-fill);
  color: var(--dsw-alias-label-primary-foreground);
  font-size: 13px;
  line-height: 20px;
  font-weight: 500;
  cursor: pointer;
}

.btnPrimary:hover {
  background: var(--dsw-alias-button-primary-hover);
}

.cardTitle {
  font-size: 13px;
  font-weight: 600;
  line-height: 20px;
  color: var(--dsw-alias-label-primary);
  margin-bottom: 10px;
}

.artRow {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 0;
}

.artLabel {
  flex: none;
  width: 110px;
  font-size: 13px;
  color: var(--dsw-alias-label-secondary);
}

.artPath {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: var(--dsw-alias-label-tertiary);
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

.iconButton:hover:not(:disabled) {
  background: var(--dsw-alias-interactive-bg-hover);
}

.iconButton:disabled {
  opacity: 0.35;
  cursor: default;
}

.packTitle {
  font-size: 14px;
  font-weight: 500;
  line-height: 22px;
  color: var(--dsw-alias-label-primary);
}

.packCaption {
  margin-top: 6px;
  font-size: 13px;
  line-height: 20px;
  color: var(--dsw-alias-label-secondary);
}

.packTags {
  margin-top: 8px;
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
</style>

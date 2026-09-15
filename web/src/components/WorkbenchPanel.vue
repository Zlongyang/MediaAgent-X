<script setup>
// 对话 tab 右侧「工作台」：该 run 的生成参数（只读展示，输入框样式）
const props = defineProps({
  config: { type: Object, required: true },
  accountLabel: { type: String, default: '—' },
})

const GROUPS = [
  {
    title: '发布',
    fields: [{ label: '发布账号 / 平台', get: (c, p) => p.accountLabel }],
  },
  {
    title: '画面',
    fields: [
      { label: '视频比例', get: (c) => c.ratio },
      { label: '目标时长', get: (c) => c.duration },
      { label: '生成数量', get: (c) => String(c.count) },
    ],
  },
  {
    title: '配音',
    fields: [
      { label: '声音', get: (c) => c.voice },
      { label: '语速', get: (c) => c.voiceRate },
      { label: '音量', get: (c) => c.voiceVol },
    ],
  },
  {
    title: '背景音乐',
    fields: [
      { label: '来源', get: (c) => c.bgm.src },
      { label: '音量', get: (c) => c.bgm.vol },
    ],
  },
  {
    title: '字幕',
    fields: [
      { label: '字号', get: (c) => c.subtitle.size },
      { label: '颜色', get: (c) => c.subtitle.color },
      { label: '位置', get: (c) => c.subtitle.pos },
    ],
  },
  {
    title: '素材',
    fields: [{ label: '素材来源', get: (c) => c.material }],
  },
]
</script>

<template>
  <div class="workbench">
    <div class="wbTitle">工作台 · 生成参数</div>
    <div v-for="g in GROUPS" :key="g.title" class="wbCard">
      <div class="wbCardTitle">{{ g.title }}</div>
      <label v-for="f in g.fields" :key="f.label" class="wbField">
        <span class="wbLabel">{{ f.label }}</span>
        <input
          class="wbInput"
          type="text"
          :value="f.get(props.config, { accountLabel: props.accountLabel })"
          readonly
        />
      </label>
    </div>
  </div>
</template>

<style scoped>
.workbench {
  height: 100%;
  overflow-y: auto;
  padding: 12px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.wbTitle {
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-caption);
  padding: 0 2px;
}

.wbCard {
  border: 1px solid var(--dsw-alias-border-l1);
  border-radius: 12px;
  background: var(--dsw-alias-bg-layer-1);
  padding: 10px 12px;
}

.wbCardTitle {
  font-size: 12px;
  font-weight: 600;
  line-height: 18px;
  color: var(--dsw-alias-label-secondary);
  margin-bottom: 8px;
}

.wbField {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 8px;
  padding: 3px 0;
}

.wbLabel {
  flex: 1 1 72px;
  min-width: 60px;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-tertiary);
}

.wbInput {
  flex: 1 1 120px;
  min-width: 0;
  height: 28px;
  padding: 3px 8px;
  border-radius: 8px;
  border: 1px solid var(--dsw-alias-border-l2);
  background: var(--dsw-specific-input-major);
  color: var(--dsw-alias-label-primary);
  font-size: 12px;
  line-height: 18px;
  outline: none;
  box-sizing: border-box;
}

.wbInput:read-only {
  color: var(--dsw-alias-label-secondary);
}
</style>

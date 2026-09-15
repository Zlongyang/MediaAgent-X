<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  theme: { type: String, default: 'system' },
  apiKey: { type: String, default: '' },
  demo: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'set-theme', 'set-api-key', 'set-demo'])

const THEMES = [
  { key: 'dark', label: '暗色' },
  { key: 'light', label: '冷色' },
  { key: 'system', label: '跟随系统' },
]

const MODES = [
  { key: 'real', label: '真实', value: false },
  { key: 'demo', label: '演示', value: true },
]

const keyDraft = ref(props.apiKey)
watch(
  () => props.open,
  (v) => {
    if (v) keyDraft.value = props.apiKey
  }
)
</script>

<template>
  <div v-if="props.open" class="mask" @click.self="emit('close')">
    <div class="modal" role="dialog" aria-label="设置" @keydown.esc="emit('close')">
      <div class="mHead">
        <span class="mTitle">设置</span>
        <button class="iconButton" type="button" title="关闭" aria-label="关闭" @click="emit('close')">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
          </svg>
        </button>
      </div>

      <div class="setGroup">
        <div class="setLabel">API</div>
        <label class="setField">
          <span class="setFieldLabel">DeepSeek API Key</span>
          <input
            v-model="keyDraft"
            class="setInput mono"
            type="password"
            placeholder="sk-…"
            @change="emit('set-api-key', keyDraft)"
          />
        </label>
      </div>

      <div class="setGroup">
        <div class="setLabel">风格</div>
        <div class="segmented">
          <button
            v-for="t in THEMES"
            :key="t.key"
            class="segBtn"
            :class="{ on: props.theme === t.key }"
            type="button"
            @click="emit('set-theme', t.key)"
          >
            {{ t.label }}
          </button>
        </div>
      </div>

      <div class="setGroup">
        <div class="setLabel">模式</div>
        <div class="segmented">
          <button
            v-for="m in MODES"
            :key="m.key"
            class="segBtn"
            :class="{ on: props.demo === m.value }"
            type="button"
            @click="emit('set-demo', m.value)"
          >
            {{ m.label }}
          </button>
        </div>
        <div class="setHint">真实模式连接本地后端（/api）；演示模式使用内置 Mock 数据</div>
      </div>

      <div class="setGroup">
        <div class="setLabel">储存位置</div>
        <div class="storageRow">
          <span class="storagePath mono">D:\MediaAgent-X\workspace</span>
          <button class="ghostBtn" type="button">更改</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--dsw-alias-bg-mask-1);
  padding: 24px;
}

.modal {
  width: 400px;
  max-width: 100%;
  padding: 16px 18px 18px;
  border-radius: 18px;
  border: 1px solid var(--dsw-alias-border-l2);
  background: var(--dsw-specific-menu);
  box-shadow: var(--dsw-shadow-lv2);
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: var(--dsw-alias-label-primary);
}

.mHead {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mTitle {
  font-size: 15px;
  font-weight: 600;
  line-height: 22px;
}

.iconButton {
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

.setLabel {
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-caption);
  margin-bottom: 6px;
}

.setHint {
  margin-top: 6px;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-caption);
}

.setField {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.setFieldLabel {
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-secondary);
}

.setInput {
  height: 32px;
  padding: 4px 10px;
  border-radius: 8px;
  border: 1px solid var(--dsw-alias-border-l2);
  background: var(--dsw-specific-input-major);
  color: var(--dsw-alias-label-primary);
  font-size: 13px;
  outline: none;
  width: 100%;
  box-sizing: border-box;
}

.setInput:focus {
  border-color: var(--dsw-alias-state-business-primary);
}

.mono {
  font-family: var(--ds-font-family-code);
}

.segmented {
  display: flex;
  gap: 2px;
  padding: 2px;
  border-radius: 10px;
  background: var(--dsw-specific-selector);
}

.segBtn {
  flex: 1;
  height: 26px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--dsw-alias-label-secondary);
  font-size: 12px;
  line-height: 18px;
  font-weight: 500;
  cursor: pointer;
}

.segBtn.on {
  background: var(--dsw-alias-button-elevated-fill);
  color: var(--dsw-alias-label-primary);
  box-shadow: var(--dsw-shadow-lv2);
}

.storageRow {
  display: flex;
  align-items: center;
  gap: 8px;
}

.storagePath {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  color: var(--dsw-alias-label-secondary);
  direction: rtl;
  text-align: left;
}

.ghostBtn {
  flex: none;
  height: 26px;
  padding: 0 10px;
  border-radius: 8px;
  border: 1px solid var(--dsw-alias-border-l3);
  background: transparent;
  color: var(--dsw-alias-label-secondary);
  font-size: 12px;
  cursor: pointer;
}

.ghostBtn:hover {
  background: var(--dsw-alias-interactive-bg-hover);
}
</style>

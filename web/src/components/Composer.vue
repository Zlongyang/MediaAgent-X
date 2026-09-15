<script setup>
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  hero: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
})

const emit = defineEmits(['send'])

const draft = ref('')
const ta = ref(null)

const empty = computed(() => draft.value.trim().length === 0)

function autogrow() {
  const el = ta.value
  if (!el) return
  el.style.height = 'auto'
  // cap at ~8 lines of 24px + top padding
  const max = 8 * 24 + 4
  el.style.height = Math.min(el.scrollHeight, max) + 'px'
  el.style.overflowY = el.scrollHeight > max ? 'auto' : 'hidden'
}

watch(draft, () => nextTick(autogrow))

function submit() {
  const text = draft.value.trim()
  if (!text) return
  emit('send', text)
  draft.value = ''
  nextTick(autogrow)
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    submit()
  }
}

defineExpose({
  focus: () => ta.value && ta.value.focus(),
})
</script>

<template>
  <div class="composer" :class="{ hero: props.hero }">
    <div class="card">
      <div class="scroll">
        <textarea
          ref="ta"
          v-model="draft"
          class="input"
          rows="1"
          placeholder="给总编派个任务，比如：做一条数码赛道的短视频…"
          @keydown="onKeydown"
          @input="autogrow"
        />
      </div>
      <div class="row">
        <div class="tools">
          <button class="add" type="button" title="添加附件" aria-label="添加附件">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 1.75v10.5M1.75 7h10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
            </svg>
          </button>
          <button class="chip" type="button">
            <span>自动模式</span>
            <svg class="chev" width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
        <div class="trailing">
          <button class="chip mono" type="button">
            <span>deepseek-v4-pro</span>
            <svg class="chev" width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
          <button
            class="primary"
            type="button"
            :disabled="empty"
            title="发送"
            aria-label="发送"
            @click="submit"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 12.5v-9M3.5 7L8 2.5L12.5 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.composer {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding: 0 var(--dsh-composer-side-clearance) 8px;
}

.composer.hero {
  padding: 0 var(--dsh-composer-side-clearance);
}

.card {
  box-sizing: border-box;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  max-width: var(--dsh-composer-card-max-width);
  padding-top: 10px;
  border: 1px solid var(--dsw-alias-border-l2-darkmode-thin);
  border-radius: 22px;
  background: var(--dsw-specific-input-major);
  box-shadow: var(--dsw-shadow-lv2);
  font-size: 16px;
  line-height: 24px;
}

.scroll {
  max-height: 196px;
  overflow-y: auto;
}

.input {
  display: block;
  width: 100%;
  box-sizing: border-box;
  resize: none;
  border: none;
  outline: none;
  background: transparent;
  padding: 4px 12px 0 16px;
  font-family: var(--dsw-font-family);
  font-size: inherit;
  line-height: inherit;
  color: var(--dsw-alias-label-primary);
  caret-color: var(--dsw-alias-state-business-primary);
  overflow: hidden;
}

.hero .input {
  min-height: 52px;
}

.input::placeholder {
  color: var(--dsw-alias-label-caption);
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 2px 8px 6px;
  min-width: 0;
}

.tools,
.trailing {
  display: flex;
  align-items: center;
  min-width: 0;
}

.tools {
  gap: 16px;
}

.trailing {
  flex: none;
  gap: 12px;
}

.add {
  display: grid;
  place-items: center;
  flex: none;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 999px;
  background: var(--dsw-specific-selector);
  color: var(--dsw-alias-label-primary);
  cursor: pointer;
}

.add:hover {
  background: var(--dsw-alias-interactive-bg-hover-solid);
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  max-width: 220px;
  height: 28px;
  padding: 0 6px 0 8px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--dsw-alias-label-secondary);
  font-size: 13px;
  line-height: 20px;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
}

.chip:hover {
  background: var(--dsw-alias-interactive-bg-hover);
}

.chip .chev {
  color: var(--dsw-alias-label-caption);
  flex: none;
}

.chip.mono span {
  font-family: var(--ds-font-family-code);
  font-size: 12px;
}

.primary {
  display: grid;
  place-items: center;
  flex: none;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 999px;
  background: var(--dsw-alias-button-info-fill);
  color: var(--dsw-static-neutral-00);
  cursor: pointer;
  transition: background-color var(--ds-transition-duration-fast) ease;
  transform: translateY(-2px);
}

.primary:hover:not(:disabled) {
  background: var(--dsw-alias-button-info-hover);
}

.primary:disabled {
  opacity: 0.4;
  cursor: default;
}
</style>

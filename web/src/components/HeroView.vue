<script setup>
import { computed, ref } from 'vue'
import AppLogo from './AppLogo.vue'
import Composer from './Composer.vue'
import { ACCOUNTS, NO_ACCOUNT } from '../data/constants.js'

const props = defineProps({
  account: { type: String, default: 'none' },
})

const emit = defineEmits(['send', 'select-account'])

const menuOpen = ref(false)
const options = [...ACCOUNTS, NO_ACCOUNT]
const current = computed(() => options.find((a) => a.key === props.account) || NO_ACCOUNT)

function pick(key) {
  emit('select-account', key)
  menuOpen.value = false
}
</script>

<template>
  <div class="hero">
    <div class="stack">
      <div class="headline">
        <span class="fishHitbox">
          <AppLogo class="fish" :size="34" />
        </span>
        <span class="headlineText">MediaAgent-X</span>
        <span class="previewBadge">developer preview</span>
      </div>
      <div class="body">
        <div class="workspaceRow">
          <div class="acctAnchor">
            <button
              class="workspace"
              type="button"
              :aria-expanded="menuOpen"
              @click="menuOpen = !menuOpen"
            >
              <span class="workspaceLabel">{{ current.label }}</span>
              <svg class="chevron" width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
            <div v-if="menuOpen" class="acctMask" @click="menuOpen = false" />
            <div v-if="menuOpen" class="acctMenu" role="menu">
              <div class="acctMenuTitle">发布账号</div>
              <button
                v-for="a in options"
                :key="a.key"
                class="acctOption"
                :class="{ on: a.key === props.account }"
                type="button"
                role="menuitem"
                @click="pick(a.key)"
              >
                <span class="acctLabel">{{ a.label }}</span>
                <svg v-if="a.key === props.account" class="acctCheck" width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M2 6.2l2.6 2.6L10 3.4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        <Composer hero @send="(t) => emit('send', t)" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.hero {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-width: 0;
  padding: 0 24px;
}

.stack {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
  width: 100%;
  max-width: var(--dsh-composer-card-max-width);
  padding-bottom: 32px;
}

.headline {
  display: grid;
  grid-template-columns: 34px auto auto;
  column-gap: 10px;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  line-height: 32px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--dsw-alias-label-primary);
}

.headlineText {
  grid-row: 1;
  grid-column: 2;
}

.previewBadge {
  grid-row: 1;
  grid-column: 3;
  align-self: start;
  margin-top: 2px;
  margin-left: -3px;
  padding: 1px 7px 0;
  border: 1px solid var(--dsw-alias-interactive-bg-hover);
  border-radius: 24px;
  background: var(--dsw-alias-state-business-tertiary);
  color: var(--dsw-alias-label-primary-bluish);
  font-family: var(--ds-font-family-code);
  font-size: 12px;
  line-height: 18px;
  font-weight: 500;
  white-space: nowrap;
}

.fishHitbox {
  grid-row: 1;
  grid-column: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.fish {
  color: var(--dsw-alias-label-primary);
  transform-origin: 50% 60%;
}

@keyframes hero-fish-swim {
  0%, 100% {
    transform: translate(0, 0) rotate(0deg);
  }
  35% {
    transform: translate(-1px, -1px) rotate(-5deg);
  }
  70% {
    transform: translate(1px, 0) rotate(3deg);
  }
}

@media (hover: hover) and (prefers-reduced-motion: no-preference) {
  .fishHitbox:hover .fish {
    animation: hero-fish-swim var(--ds-transition-duration-slow) var(--ds-ease-in-out);
  }
}

.body {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.workspaceRow {
  display: flex;
  align-items: center;
  min-width: 0;
  padding-left: 20px;
}

.acctAnchor {
  position: relative;
}

.workspace {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: min(100%, 360px);
  min-height: 28px;
  padding: 0 8px;
  border: none;
  border-radius: 16px;
  background: transparent;
  color: var(--dsw-alias-label-primary);
  font-size: 13px;
  line-height: 20px;
  font-weight: 500;
  cursor: pointer;
}

.workspace:hover,
.workspace[aria-expanded='true'] {
  background: var(--dsw-alias-interactive-bg-hover);
}

.workspaceLabel {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chevron {
  flex: none;
  color: var(--dsw-alias-label-caption);
}

.acctMask {
  position: fixed;
  inset: 0;
  z-index: 30;
}

.acctMenu {
  position: absolute;
  top: 32px;
  left: 0;
  z-index: 31;
  min-width: 220px;
  padding: 6px;
  border-radius: 12px;
  border: 1px solid var(--dsw-alias-border-l2);
  background: var(--dsw-specific-menu);
  box-shadow: var(--dsw-shadow-lv2);
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.acctMenuTitle {
  padding: 4px 8px 6px;
  font-size: 11px;
  line-height: 16px;
  color: var(--dsw-alias-label-caption);
}

.acctOption {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 8px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--dsw-alias-label-primary);
  font-size: 13px;
  line-height: 18px;
  cursor: pointer;
  text-align: left;
}

.acctOption:hover {
  background: var(--dsw-alias-interactive-bg-hover);
}

.acctOption.on {
  background: var(--dsw-specific-sidebar-nav-item-active);
}

.acctLabel {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.acctCheck {
  flex: none;
  color: var(--dsw-alias-state-business-primary);
}
</style>

<script setup>
import { computed, reactive } from 'vue'
import AppLogo from './AppLogo.vue'
import StatusBadge from './StatusBadge.vue'
import { ACCOUNTS, NO_ACCOUNT } from '../data/mock.js'

const props = defineProps({
  collapsed: { type: Boolean, default: false },
  nav: { type: String, default: 'chat' }, // chat | monitor | workflows
  projects: { type: Array, default: () => [] },
  activeProjectId: { type: String, default: '' },
})

const emit = defineEmits(['toggle-collapse', 'nav', 'new-video', 'select-project', 'open-account', 'open-settings'])

const NAV = [
  { key: 'monitor', label: '数据监控' },
  { key: 'workflows', label: '已安排工作流' },
]

/* group projects by account folder, unassigned last */
const folders = computed(() => {
  const groups = ACCOUNTS.map((a) => ({ ...a, items: [] }))
  const none = { ...NO_ACCOUNT, items: [] }
  for (const p of props.projects) {
    const g = groups.find((x) => x.key === p.account) || none
    g.items.push(p)
  }
  return [...groups.filter((g) => g.items.length), ...(none.items.length ? [none] : [])]
})

const closedFolders = reactive({})
function toggleFolder(key) {
  closedFolders[key] = !closedFolders[key]
}

</script>

<template>
  <aside class="sidebar" :class="{ rail: props.collapsed }">
    <!-- logo row -->
    <div class="logoRow">
      <div class="brand">
        <AppLogo :size="24" />
        <span v-if="!props.collapsed" class="wordmark">MediaAgent-X</span>
      </div>
      <button
        class="iconButton toggle"
        type="button"
        :title="props.collapsed ? '展开侧栏' : '收起侧栏'"
        :aria-label="props.collapsed ? '展开侧栏' : '收起侧栏'"
        @click="emit('toggle-collapse')"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect x="2" y="2.5" width="12" height="11" rx="2.5" stroke="currentColor" stroke-width="1.4" />
          <path d="M6.5 3.5v9" stroke="currentColor" stroke-width="1.4" />
        </svg>
      </button>
    </div>

    <!-- new conversation -->
    <button
      class="newSession"
      type="button"
      :title="props.collapsed ? '新对话' : undefined"
      @click="emit('new-video')"
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M7 1.75v10.5M1.75 7h10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
      </svg>
      <span class="newSessionLabel">新对话</span>
    </button>

    <!-- nav -->
    <nav class="navList">
      <button
        v-for="n in NAV"
        :key="n.key"
        class="navItem"
        :class="{ active: props.nav === n.key }"
        type="button"
        :title="props.collapsed ? n.label : undefined"
        @click="emit('nav', n.key)"
      >
        <svg v-if="n.key === 'monitor'" class="navIcon" width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2.5 13.5h11M3.5 10.5l3-4 2.5 2.5 3.5-5.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <svg v-else class="navIcon" width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.4" />
          <path d="M8 4.5V8l2.5 1.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
        </svg>
        <span class="navLabel">{{ n.label }}</span>
      </button>
    </nav>

    <!-- generated videos -->
    <div v-if="!props.collapsed" class="region">
      <div class="sectionTitle">已生成视频</div>
      <div v-for="f in folders" :key="f.key" class="folder">
        <div
          class="folderHead"
          role="button"
          tabindex="0"
          @click="emit('open-account', f.key)"
          @keydown.enter="emit('open-account', f.key)"
        >
          <span class="folderName">{{ f.label }}</span>
          <span class="folderCount">{{ f.items.length }}</span>
          <button
            class="chevBtn"
            type="button"
            :title="closedFolders[f.key] ? '展开' : '收起'"
            :aria-label="closedFolders[f.key] ? '展开' : '收起'"
            @click.stop="toggleFolder(f.key)"
          >
            <svg
              class="folderChev"
              :data-open="!closedFolders[f.key]"
              width="10" height="10" viewBox="0 0 10 10" fill="none"
            >
              <path d="M2 3.5L5 6.5L8 3.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
        <div v-show="!closedFolders[f.key]" class="folderBody">
          <button
            v-for="p in f.items"
            :key="p.id"
            class="projItem"
            :class="{ active: props.activeProjectId === p.id }"
            :data-id="p.id"
            type="button"
            @click="emit('select-project', p.id)"
          >
            <span class="projName">{{ p.name }}</span>
            <StatusBadge :status="p.status" />
          </button>
        </div>
      </div>
    </div>

    <!-- footer: settings -->
    <div class="foot">
      <button
        class="iconButton"
        type="button"
        title="设置"
        aria-label="设置"
        @click="emit('open-settings')"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="2.2" stroke="currentColor" stroke-width="1.4" />
          <path d="M8 1.8l.7 1.7 1.8-.3 1 1.5-1.2 1.4 1.2 1.4-1 1.5-1.8-.3L8 14.2l-.7-1.7-1.8.3-1-1.5 1.2-1.4-1.2-1.4 1-1.5 1.8.3L8 1.8Z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round" />
        </svg>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 6px 12px;
  box-sizing: border-box;
  background: var(--dsw-specific-sidebar-fill);
  color: var(--dsw-alias-label-primary);
  font-size: 14px;
  overflow: hidden;
}

.sidebar.rail {
  padding: 18px 10px 6px;
  align-items: center;
}

.logoRow {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  height: 60px;
  padding: 8px 0 8px 4px;
  margin-bottom: 8px;
  box-sizing: border-box;
  width: 100%;
}

.rail .logoRow {
  height: 36px;
  padding: 0;
  margin-bottom: 12px;
  justify-content: center;
  width: auto;
}

.brand {
  flex: 1;
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  color: var(--dsw-alias-label-primary);
}

.rail .brand {
  display: none;
}

.rail .toggle {
  width: 36px;
  height: 36px;
  color: var(--dsw-alias-label-primary);
}

.wordmark {
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
  white-space: nowrap;
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

.newSession {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 38px;
  width: 100%;
  padding: 8px 16px;
  margin: 0 2px 8px;
  box-sizing: border-box;
  border: 1px solid var(--dsw-alias-border-l2);
  border-radius: 999px;
  background: var(--dsw-alias-button-elevated-fill);
  color: var(--dsw-alias-label-primary);
  font-size: 14px;
  font-weight: 500;
  line-height: 22px;
  cursor: pointer;
}

.newSession:hover {
  background: var(--dsw-alias-button-floating-hover);
}

.rail .newSession {
  width: 36px;
  height: 36px;
  padding: 0;
  margin: 0 0 12px;
  gap: 0;
  border-radius: 50%;
}

.rail .newSessionLabel {
  display: none;
}

.navList {
  flex: none;
  display: flex;
  flex-direction: column;
  gap: 1px;
  width: 100%;
}

.navItem {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 8px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--dsw-alias-label-primary);
  font-size: 14px;
  line-height: 20px;
  text-align: left;
  cursor: pointer;
}

.navItem:hover {
  background: var(--dsw-specific-sidebar-nav-item-hover);
}

.navItem.active {
  background: var(--dsw-specific-sidebar-nav-item-active);
}

.navIcon {
  flex: none;
  color: var(--dsw-alias-label-secondary);
}

.navItem.active .navIcon {
  color: var(--dsw-alias-label-primary);
}

.rail .navItem {
  width: 36px;
  height: 36px;
  padding: 0;
  justify-content: center;
}

.rail .navLabel {
  display: none;
}

.region {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  margin: 8px -4px 0;
  padding: 0 4px;
  width: 100%;
}

.sectionTitle {
  padding: 8px 8px 4px;
  font-size: 12px;
  line-height: 18px;
  color: var(--dsw-alias-label-caption);
}

.folderHead {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 5px 8px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--dsw-alias-label-secondary);
  font-size: 13px;
  line-height: 18px;
  cursor: pointer;
  text-align: left;
}

.folderHead:hover {
  background: var(--dsw-specific-sidebar-nav-item-hover);
}

.folderChev {
  flex: none;
  color: var(--dsw-alias-label-caption);
  transition: transform var(--ds-transition-duration-fast) var(--ds-ease-in-out);
  transform: rotate(-90deg);
}

.folderChev[data-open='true'] {
  transform: rotate(0deg);
}

.chevBtn {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 50%;
  padding: 0;
  background: transparent;
  cursor: pointer;
  color: var(--dsw-alias-label-caption);
}

.chevBtn:hover {
  background: var(--dsw-alias-interactive-bg-hover);
  color: var(--dsw-alias-label-secondary);
}

.folderName {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.folderCount {
  flex: none;
  font-size: 11px;
  color: var(--dsw-alias-label-caption);
  font-variant-numeric: tabular-nums;
}

.folderBody {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 1px 0 4px;
}

.projItem {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 8px 6px 24px;
  border: none;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.projItem:hover {
  background: var(--dsw-specific-sidebar-nav-item-hover);
}

.projItem.active {
  background: var(--dsw-specific-sidebar-nav-item-active);
}

.projName {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  line-height: 18px;
  color: var(--dsw-alias-label-primary);
}

.foot {
  flex: none;
  display: flex;
  align-items: center;
  gap: 4px;
  padding-top: 6px;
  width: 100%;
}

.rail .foot {
  width: auto;
  justify-content: center;
}

.rail .foot .iconButton {
  width: 36px;
  height: 36px;
}
</style>

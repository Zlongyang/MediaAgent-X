<script setup>
// MediaAgent-X 定稿 logo：调度网络 X（方案 2）
// 中心枢纽向四节点辐射 —— 总编调度工种的拓扑；X 由连线自然成形。
// 方形 viewBox，颜色跟 currentColor 走，亮暗主题自动适配。
defineProps({
  size: { type: Number, default: 24 },
})
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 48 48"
    fill="none"
    aria-hidden="true"
  >
    <g stroke="currentColor" stroke-width="3.4" stroke-linecap="round">
      <line x1="24" y1="24" x2="10.5" y2="10.5" />
      <line x1="24" y1="24" x2="37.5" y2="10.5" />
      <line x1="24" y1="24" x2="10.5" y2="37.5" />
      <line x1="24" y1="24" x2="37.5" y2="37.5" />
    </g>
    <circle cx="10.5" cy="10.5" r="3.4" fill="currentColor" />
    <circle cx="37.5" cy="10.5" r="3.4" fill="currentColor" />
    <circle cx="10.5" cy="37.5" r="3.4" fill="currentColor" />
    <circle cx="37.5" cy="37.5" r="3.4" fill="currentColor" />
    <circle cx="24" cy="24" r="5.6" fill="currentColor" />
  </svg>
</template>

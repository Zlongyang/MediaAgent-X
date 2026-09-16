<script setup>
// 全站统一的手绘风内联 SVG 图标：currentColor + 圆头描边，风格对齐 Sidebar
defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 14 },
})
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- 靶心：选题猎手 -->
    <g v-if="name === 'target'">
      <circle cx="12" cy="12" r="8.5" />
      <circle cx="12" cy="12" r="4.5" />
      <circle cx="12" cy="12" r="1.2" fill="currentColor" stroke="none" />
    </g>
    <!-- 斜笔触钢笔：编剧 -->
    <g v-else-if="name === 'pen'">
      <path d="M4 20l1.1-4.1L16.6 4.4a2.12 2.12 0 0 1 3 3L8.1 18.9 4 20Z" />
      <path d="M14.5 6.5l3 3" />
    </g>
    <!-- 场记板：分镜师 -->
    <g v-else-if="name === 'clapper'">
      <path d="M4 10.5h16V18a1.6 1.6 0 0 1-1.6 1.6H5.6A1.6 1.6 0 0 1 4 18v-7.5Z" />
      <path d="M4.3 10.5L3.9 6.3A1.6 1.6 0 0 1 5.6 4.5l13.9 1.5.5 4.5" />
      <path d="M8.2 5.1l1.7 4.9M12.6 5.6l1.7 4.9M16.9 6.1l1.7 4.9" />
    </g>
    <!-- 厂房轮廓：制片 -->
    <g v-else-if="name === 'factory'">
      <path d="M3.5 20V9.5L9 13V9.5l5.5 3.5V7l2.3-2.5h3.7V20" />
      <path d="M3.5 20h17" />
      <path d="M7.5 15.5h1.5M12 15.5h1.5M16.5 15.5H18" />
    </g>
    <!-- 纸箱：包装师 -->
    <g v-else-if="name === 'package'">
      <path d="M4 7.5L12 3.5l8 4v9l-8 4-8-4v-9Z" />
      <path d="M4 7.5l8 4 8-4" />
      <path d="M12 11.5v9" />
      <path d="M8 5.6l8 3.9" />
    </g>
    <!-- 火箭：发行人 -->
    <g v-else-if="name === 'rocket'">
      <path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2.1-.1-2.9a2.18 2.18 0 0 0-2.9-.1Z" />
      <path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2Z" />
      <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" />
      <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" />
    </g>
    <!-- 柱状图：分析师 -->
    <g v-else-if="name === 'chart'">
      <path d="M3.5 20.5h17" />
      <path d="M7 16.5v-5M12 16.5v-9M17 16.5v-7" />
    </g>
    <!-- 禁止通行：闸门 -->
    <g v-else-if="name === 'gate'">
      <path d="M8.6 3.5h6.8l5.1 5.1v6.8l-5.1 5.1H8.6l-5.1-5.1V8.6l5.1-5.1Z" />
      <path d="M8 12h8" />
    </g>
    <!-- 火焰：热度 -->
    <g v-else-if="name === 'flame'">
      <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14-.22-4.05 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.15.43-2.29 1-3a2.5 2.5 0 0 0 2.5 2.5Z" />
    </g>
    <!-- 点赞手势 -->
    <g v-else-if="name === 'like'">
      <path d="M7 10v12" />
      <path d="M15 5.88L14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z" />
    </g>
    <!-- 对话气泡 -->
    <g v-else-if="name === 'comment'">
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5Z" />
    </g>
    <!-- 上升折线箭头 -->
    <g v-else-if="name === 'trending'">
      <path d="M3.5 17.5l5.5-5.5 3.5 3.5 7.5-7.5" />
      <path d="M14.5 8H20v5.5" />
    </g>
    <!-- 三角感叹号 -->
    <g v-else-if="name === 'warn'">
      <path d="M10.3 4.1L2.6 17.5a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 4.1a2 2 0 0 0-3.4 0Z" />
      <path d="M12 9v4.5" />
      <path d="M12 17h.01" />
    </g>
    <!-- 对勾 -->
    <g v-else-if="name === 'check'">
      <path d="M4.5 12.5l5 5 10-11" />
    </g>
    <!-- 叉 -->
    <g v-else-if="name === 'close'">
      <path d="M6 6l12 12M18 6L6 18" />
    </g>
    <!-- 垃圾桶：删除 -->
    <g v-else-if="name === 'trash'">
      <path d="M4 7h16" />
      <path d="M9 7V4.8A1.3 1.3 0 0 1 10.3 3.5h3.4A1.3 1.3 0 0 1 15 4.8V7" />
      <path d="M6.5 7l.9 12.1A1.6 1.6 0 0 0 9 20.5h6a1.6 1.6 0 0 0 1.6-1.4L17.5 7" />
      <path d="M10 11v5.5M14 11v5.5" />
    </g>
    <!-- 三角播放 -->
    <g v-else-if="name === 'play'">
      <path d="M7 4.8v14.4c0 .9.98 1.45 1.76.97l11-7.2a1.15 1.15 0 0 0 0-1.94l-11-7.2A1.15 1.15 0 0 0 7 4.8Z" />
    </g>
  </svg>
</template>

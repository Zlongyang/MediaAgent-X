// 全站静态配置（非 mock）：账号定义、状态徽章文案、生成配置默认值。
// 演示数据集（PROJECTS/WORKFLOWS/MONITOR_VIDEOS）已随 mock 模式一并移除——
// 运行数据一律来自后端 /api。

export const ACCOUNTS = [
  { key: 'dy-shuma', label: '抖音 · 数码小X', platform: '抖音' },
  { key: 'bili-xiaox', label: 'B站 · 小X评测', platform: 'B站' },
]

export const NO_ACCOUNT = { key: 'none', label: '暂不选择 / 未安排', platform: '—' }

export const STATUS = {
  generating: { label: '生成中', kind: 'business' },
  review: { label: '待审查', kind: 'warn' },
  unpublished: { label: '未发布', kind: 'success' },
  published: { label: '已发布', kind: 'neutral' },
  failed: { label: '生成失败', kind: 'error' },
}

const BASE_CONFIG = {
  ratio: '9:16',
  duration: '60s',
  count: 1,
  voice: '云希（青年男声）',
  voiceRate: '1.0x',
  voiceVol: '100%',
  bgm: { src: '卡点榜 · 轻快电子', vol: '20%' },
  subtitle: { size: '16px', color: '白色描边', pos: '底部 12%' },
  material: 'Pexels + AI 生成',
}

export function defaultConfig() {
  return {
    ...BASE_CONFIG,
    bgm: { ...BASE_CONFIG.bgm },
    subtitle: { ...BASE_CONFIG.subtitle },
  }
}

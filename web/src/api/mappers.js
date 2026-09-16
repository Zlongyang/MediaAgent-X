// 后端 → 前端的形状翻译（spec §4.2）。
import { defaultConfig } from '../data/constants.js'

// 工件绝对/相对路径 → 前端可播的 HTTP URL（后端 /api/runs/{id}/artifacts/ 服务）
export function artifactUrl(p) {
  if (!p) return ''
  const m = String(p).replace(/\\/g, '/').match(/runs\/([^/]+)\/(.+)$/)
  return m ? `/api/runs/${m[1]}/artifacts/${m[2]}` : ''
}

// gate_request.data → GateCard 需要的 gate 对象
export function mapGateRequest(d) {
  const view = d.view || {}
  return {
    key: d.key,
    title: d.title,
    autonomyKey: d.autonomyKey,
    nonce: d.nonce,
    candidates: view.candidates,
    script: view.excerpt,
    videoPath: view.video,
    videoUrl: artifactUrl(view.video),
    pack: view.pack,
  }
}

// review_ready.data → ReviewCard 形状。后端 metrics 是监控快照 [{t,play,like,comment,share}]，
// 取首个快照（T+1h，对齐卡片副标题）；无账号均值基线，delta 恒空串。
export function mapReview(d) {
  const snap = Array.isArray(d.metrics) && d.metrics.length ? d.metrics[0] : null
  const rows = snap
    ? [
        ['播放', snap.play],
        ['点赞', snap.like],
        ['评论', snap.comment],
      ]
        .filter(([, v]) => typeof v === 'number')
        .map(([label, v]) => ({ label, value: v.toLocaleString('en-US'), delta: '' }))
    : []
  return {
    runId: d.runId || '',
    metrics: rows,
    cost: { llm: 0, material: 0, tts: 0, total: 0, ...(d.cost || {}) },
    tips: Array.isArray(d.tips) ? d.tips : [],
  }
}

// 后端 project.json → 前端项目形状（补 ProjectView 四 tab 需要的缺省字段）
export function mapProject(p) {
  const artifacts = { audio: '', subtitle: '', cover: '', final: '', ...(p.artifacts || {}) }
  return {
    id: p.id,
    name: p.name || p.id,
    account: p.account || 'none',
    status: p.status || 'unpublished',
    createdAt: p.createdAt || '',
    detail: p.detail || 'full',
    config: p.config || defaultConfig(),
    artifacts,
    video: p.video || null,
    videoUrl: p.videoUrl || artifactUrl(artifacts.final),
    pack: p.pack || null,
    stages: p.stages || [],
    shots: p.shots || [],
    logs: p.logs || [],
    snapshots: p.snapshots || [],
    // 真实 tips 未持久化，归档项目恒空数组（live 期间由 review_ready 事件驱动）
    tips: Array.isArray(p.tips) ? p.tips : [],
    chat: (p.chat || []).filter((m) => m && (m.type === 'user' || m.type === 'assistant')),
    cost: p.cost || null,
    review_report: p.review_report || '',
  }
}

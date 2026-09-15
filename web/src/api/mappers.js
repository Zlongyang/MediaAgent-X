// 后端 → 前端的形状翻译（spec §4.2）。
import { defaultConfig } from '../data/mock.js'

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
    pack: view.pack,
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
    pack: p.pack || null,
    stages: p.stages || [],
    shots: p.shots || [],
    logs: p.logs || [],
    snapshots: p.snapshots || [],
    tips: p.tips || (p.review_report ? [String(p.review_report).split('\n')[0]] : []),
    chat: (p.chat || []).filter((m) => m && (m.type === 'user' || m.type === 'assistant')),
    cost: p.cost || null,
    review_report: p.review_report || '',
  }
}

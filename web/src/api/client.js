// 唯一与后端通信的模块（spec §4.1）。全部走相对路径 /api（vite proxy 转发）。
// 非 2xx 统一抛 Error（带 status）；SSE 用 fetch + ReadableStream 逐帧解析。

const BASE = '/api'

async function req(path, opts = {}) {
  let res
  try {
    res = await fetch(BASE + path, {
      headers: { 'Content-Type': 'application/json' },
      ...opts,
    })
  } catch (e) {
    throw new Error('网络错误：' + (e.message || e))
  }
  if (!res.ok) {
    let msg = 'HTTP ' + res.status
    try {
      const j = await res.json()
      if (j && j.detail) msg = typeof j.detail === 'string' ? j.detail : msg
    } catch (e) {}
    const err = new Error(msg)
    err.status = res.status
    throw err
  }
  return res.json()
}

export const health = () => req('/health')

export const createRun = ({ text, account, autonomy, autoMode }) =>
  req('/runs', { method: 'POST', body: JSON.stringify({ text, account, autonomy, autoMode }) })

export const resolveGate = (runId, { nonce, action, payload }) =>
  req(`/runs/${runId}/gate`, { method: 'POST', body: JSON.stringify({ nonce, action, payload }) })

export const setAutonomy = (runId, key, enabled) =>
  req(`/runs/${runId}/autonomy`, { method: 'POST', body: JSON.stringify({ key, enabled }) })

export const fetchState = (runId) => req(`/runs/${runId}/state`)

export const listProjects = () => req('/projects')
export const getProject = (id) => req(`/projects/${id}`)
export const publishProject = (id) => req(`/projects/${id}/publish`, { method: 'POST', body: '{}' })

export const listWorkflows = () => req('/workflows')
export const createWorkflow = (wf) =>
  req('/workflows', { method: 'POST', body: JSON.stringify(wf) })
export const deleteWorkflow = (id) => req(`/workflows/${id}`, { method: 'DELETE' })
export const toggleWorkflow = (id) => req(`/workflows/${id}/toggle`, { method: 'POST', body: '{}' })
export const runWorkflow = (id) => req(`/workflows/${id}/run`, { method: 'POST', body: '{}' })

export const listMonitorVideos = (account) =>
  req('/monitor/videos' + (account ? `?account=${encodeURIComponent(account)}` : ''))

export const chatRoute = ({ text, account }) =>
  req('/chat', { method: 'POST', body: JSON.stringify({ text, account }) })

// SSE 消费：逐帧回调 {event, data}；AbortError 上抛（调用方识别主动中断）。
export async function streamRun(runId, { onEvent, signal }) {
  const res = await fetch(`${BASE}/runs/${runId}/events`, { signal })
  if (!res.ok || !res.body) {
    const err = new Error('SSE HTTP ' + res.status)
    err.status = res.status
    throw err
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buf = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    let idx
    while ((idx = buf.indexOf('\n\n')) >= 0) {
      const frame = buf.slice(0, idx)
      buf = buf.slice(idx + 2)
      let event = ''
      let data = ''
      for (const line of frame.split('\n')) {
        if (line.startsWith('event: ')) event = line.slice(7).trim()
        else if (line.startsWith('data: ')) data += line.slice(6)
      }
      if (event && data) {
        let parsed
        try {
          parsed = JSON.parse(data)
        } catch (e) {
          continue
        }
        onEvent({ event, data: parsed })
      }
    }
  }
}

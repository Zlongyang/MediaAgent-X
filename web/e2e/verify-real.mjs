/* E2E verify-real: 真实模式（前端 → 真实后端 SSE）全链路验收。
   前置：后端已起（MockChat，无 key）且 vite dev 已起（proxy → 后端）。
   Usage: BASE_URL=http://localhost:5302/ node e2e/verify-real.mjs */
import puppeteer from 'puppeteer-core'
import { mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const BASE = process.env.BASE_URL || 'http://localhost:5302/'
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const SHOTS = fileURLToPath(new URL('./shots/', import.meta.url))
mkdirSync(SHOTS, { recursive: true })

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// 按行文本定位工作流行内的按钮（避免操作到既有/残留行）
const wfRowBtn = (name, btnClass) =>
  page.$$eval('.rows .row', (rows, n, b) => {
    const row = rows.find((r) => r.textContent.includes(n))
    if (!row) throw new Error('工作流行不存在: ' + n)
    return row.querySelector(b).click()
  }, name, btnClass)

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: 'new',
  args: ['--no-sandbox', '--disable-gpu', '--window-size=1440,900'],
  defaultViewport: { width: 1440, height: 900 },
})

const page = await browser.newPage()
page.on('pageerror', (e) => console.error('PAGE ERROR:', e.message))

let step = 'load'
try {
  await page.goto(BASE, { waitUntil: 'networkidle0' })

  // 0. 确保真实模式（默认即是；清掉可能的本地残留）
  step = 'real-mode'
  await page.evaluate(() => localStorage.setItem('max-demo-mode', '0'))
  await page.reload({ waitUntil: 'networkidle0' })

  // 1. hero → 发任务
  step = 'send'
  await page.waitForSelector('textarea.input', { timeout: 8000 })
  await page.click('textarea.input')
  await page.type('textarea.input', '做一条数码赛道的短视频')
  await page.click('button.primary')

  // 2. 管线 + 选题闸门（真实后端 MockChat，秒级）
  step = 'gate_topic'
  await page.waitForSelector('.pipeline', { timeout: 15000 })
  await page.waitForSelector('.gate', { timeout: 15000 })
  await page.screenshot({ path: SHOTS + 'vr-01-gate-topic.png' })
  await page.$$eval('.cand input', (els) => els[1].click())
  await page.$$eval('.gateFoot .btnPrimary', (els) => els[0].click())

  // 3. 脚本闸门：驳回一次 → 重弹 → 确认（验证 nonce++ 与 rerun 回边）
  step = 'gate_script'
  await page.waitForFunction(
    () => document.querySelector('.gateTitle') && document.querySelector('.gateTitle').textContent.includes('脚本确认'),
    { timeout: 20000 }
  )
  await page.$$eval('.gateFoot .btnGhost', (els) => els[0].click())
  await page.waitForFunction(() => !document.querySelector('.gate'), { timeout: 8000 })
  await page.waitForFunction(
    () => document.querySelector('.gateTitle') && document.querySelector('.gateTitle').textContent.includes('脚本确认'),
    { timeout: 20000 }
  )
  await page.screenshot({ path: SHOTS + 'vr-02-gate-script-reject-rerun.png' })
  await page.$$eval('.gateFoot .btnPrimary', (els) => els[0].click())
  // 坐实 nonce++：驳回后第二次弹窗确认，nonce 应为 2。POST /gate 仅入队 resume，
  // 检查点异步提交，故轮询 /state 直到落定（fetch 走页面上下文，proxy 同源无跨域）
  const runId = await page.evaluate(() => {
    const kv = [...document.querySelectorAll('.details .kv')].find((e) => e.textContent.includes('run_id'))
    return kv ? kv.querySelector('.v').textContent.trim() : ''
  })
  if (!runId) throw new Error('右栏 run_id 为空')
  let nonces = {}
  for (let i = 0; i < 20; i++) {
    const st = await page.evaluate((rid) => fetch(`/api/runs/${rid}/state`).then((r) => r.json()), runId)
    nonces = st.gate_nonces || {}
    if (nonces.gate_script === 2) break
    await sleep(300)
  }
  if (nonces.gate_script !== 2) throw new Error('gate_script nonce 应为 2，实际 ' + JSON.stringify(nonces))

  // 4. 成片预览闸门 → 确认（mock 色卡 mp4 经 /artifacts 服务渲染为真 <video>）
  step = 'gate_preview'
  await page.waitForFunction(
    () => document.querySelector('.gateTitle') && document.querySelector('.gateTitle').textContent.includes('成片预览'),
    { timeout: 30000 }
  )
  await page.waitForSelector('.gate video.videoReal', { timeout: 8000 })
  await page.screenshot({ path: SHOTS + 'vr-03b-gate-preview-video.png' })
  await page.$$eval('.gateFoot .btnPrimary', (els) => els[0].click())

  // 5. 发布闸门 → 确认
  step = 'gate_publish'
  await page.waitForFunction(
    () => document.querySelector('.gateTitle') && document.querySelector('.gateTitle').textContent.includes('发布确认'),
    { timeout: 20000 }
  )
  await page.screenshot({ path: SHOTS + 'vr-03-gate-publish.png' })
  await page.$$eval('.gateFoot .btnPrimary', (els) => els[0].click())

  // 6. 复盘卡 + 成本 > 0（真实 cost_add 事件驱动）
  step = 'review'
  await page.waitForSelector('.review', { timeout: 30000 })
  const reviewTxt = await page.evaluate(() => document.querySelector('.review').textContent)
  if (!reviewTxt.includes('12,480')) throw new Error('复盘卡指标缺失（mapReview 回归）: ' + reviewTxt.slice(0, 120))
  const panelTxt = await page.evaluate(() => (document.querySelector('.details') || { textContent: '' }).textContent)
  const m = panelTxt.match(/合计\s*¥([\d.]+)/)
  if (!m || !(parseFloat(m[1]) > 0)) throw new Error('成本合计未更新: ' + panelTxt.slice(0, 120))
  await page.screenshot({ path: SHOTS + 'vr-04-review.png' })

  // 7. 侧栏出现真实项目（id 为 r-xxxx），点进项目页四 tab
  // 归档项目名 = 选题（非 brief），故以右栏 run_id 精确定位本 run 的侧栏项
  step = 'project'
  await page.waitForSelector(`.projItem[data-id="${runId}"]`, { timeout: 8000 })
  await page.click(`.projItem[data-id="${runId}"]`)
  await page.waitForFunction(
    () => [...document.querySelectorAll('.tab')].length === 4,
    { timeout: 8000 }
  )
  // 视频产出 tab
  await page.$$eval('.tab', (els) => els.find((e) => e.textContent === '视频产出').click())
  await page.waitForFunction(() => document.body.textContent.includes('工件'), { timeout: 5000 })
  await page.waitForSelector('.playerCard video.videoReal', { timeout: 8000 })
  await page.screenshot({ path: SHOTS + 'vr-05a-project-output-video.png' })
  // 制作详情 tab：分镜表来自真实 shots
  await page.$$eval('.tab', (els) => els.find((e) => e.textContent === '制作详情').click())
  await page.waitForFunction(() => document.body.textContent.includes('分镜'), { timeout: 5000 })
  await page.screenshot({ path: SHOTS + 'vr-05-project-detail.png' })

  // 8. 工作流：新建 → 列表出现 → toggle → 立即运行 toast → 删除（两步确认）
  step = 'workflows'
  await page.$$eval('.navItem', (els) => els.find((e) => e.textContent.includes('已安排工作流')).click())
  await page.waitForSelector('.newBtn', { timeout: 5000 })
  await page.click('.newBtn')
  await page.waitForSelector('.wfForm', { timeout: 5000 })
  // .fi 顺序 = 名称/cron/账号(select)/描述/任务：inputs[0]名称 inputs[1]cron inputs[3]描述（brief 留空走前端兜底）
  const inputs = await page.$$('.wfForm .fi')
  await inputs[0].type('e2e 日更数码')
  await inputs[1].type('40 7 * * *')
  await inputs[3].type('e2e 验证用')
  await page.$$eval('.wfForm .btnPrimary', (els) => els[0].click())
  await page.waitForFunction(
    () => document.body.textContent.includes('e2e 日更数码'),
    { timeout: 8000 }
  )
  await page.screenshot({ path: SHOTS + 'vr-06-workflow-created.png' })
  await wfRowBtn('e2e 日更数码', '.switch')
  await sleep(400)
  await wfRowBtn('e2e 日更数码', '.runBtn')
  await page.waitForFunction(
    () => document.body.textContent.includes('已触发'),
    { timeout: 8000 }
  )
  // 删除是两步确认：第一次点武装，第二次点才真删（行域等待，不用固定 sleep）
  await wfRowBtn('e2e 日更数码', '.delBtn')
  await page.waitForFunction(
    (n) => [...document.querySelectorAll('.rows .row')].some((r) => r.textContent.includes(n) && r.querySelector('.delBtn').dataset.armed === 'true'),
    { timeout: 3000 }, 'e2e 日更数码'
  )
  await wfRowBtn('e2e 日更数码', '.delBtn')
  await page.waitForFunction(
    (n) => ![...document.querySelectorAll('.rows .row')].some((r) => r.textContent.includes(n)),
    { timeout: 5000 }, 'e2e 日更数码'
  )

  console.log('VERIFY-REAL OK · steps passed through:', step)
} catch (err) {
  console.error('VERIFY-REAL FAILED at step:', step, '-', err.message)
  await page.screenshot({ path: SHOTS + 'vr-99-fail.png' }).catch(() => {})
  process.exitCode = 1
} finally {
  await browser.close()
}

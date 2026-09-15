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

  // 4. 成片预览闸门 → 确认
  step = 'gate_preview'
  await page.waitForFunction(
    () => document.querySelector('.gateTitle') && document.querySelector('.gateTitle').textContent.includes('成片预览'),
    { timeout: 30000 }
  )
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
  const panelTxt = await page.evaluate(() => (document.querySelector('.details') || { textContent: '' }).textContent)
  const m = panelTxt.match(/合计\s*¥([\d.]+)/)
  if (!m || !(parseFloat(m[1]) > 0)) throw new Error('成本合计未更新: ' + panelTxt.slice(0, 120))
  await page.screenshot({ path: SHOTS + 'vr-04-review.png' })

  // 7. 侧栏出现真实项目（id 为 r-xxxx），点进项目页四 tab
  // 归档项目名 = 选题（非 brief），故以右栏 run_id 精确定位本 run 的侧栏项
  step = 'project'
  const runId = await page.evaluate(() => {
    const kv = [...document.querySelectorAll('.details .kv')].find((e) => e.textContent.includes('run_id'))
    return kv ? kv.querySelector('.v').textContent.trim() : ''
  })
  if (!runId) throw new Error('右栏 run_id 为空')
  await page.waitForSelector(`.projItem[data-id="${runId}"]`, { timeout: 8000 })
  await page.click(`.projItem[data-id="${runId}"]`)
  await page.waitForFunction(
    () => [...document.querySelectorAll('.tab')].length === 4,
    { timeout: 8000 }
  )
  // 视频产出 tab
  await page.$$eval('.tab', (els) => els.find((e) => e.textContent === '视频产出').click())
  await page.waitForFunction(() => document.body.textContent.includes('工件'), { timeout: 5000 })
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
  await page.$$eval('.row .switch', (els) => els[0].click())
  await sleep(400)
  await page.$$eval('.row .runBtn', (els) => els[0].click())
  await page.waitForFunction(
    () => document.body.textContent.includes('已触发'),
    { timeout: 8000 }
  )
  // 删除是两步确认：第一次点武装，第二次点才真删
  await page.$$eval('.row .delBtn', (els) => els[0].click())
  await sleep(300)
  await page.$$eval('.row .delBtn', (els) => els[0].click())
  await sleep(500)
  // 只断言行列表（.rows）：「已触发」toast 含工作流名且驻留数秒，body 级断言会被它污染
  const wfGone = await page.evaluate(
    () => ![...document.querySelectorAll('.rows .row')].some((r) => r.textContent.includes('e2e 日更数码'))
  )
  if (!wfGone) throw new Error('工作流删除后仍在列表')

  console.log('VERIFY-REAL OK · steps passed through:', step)
} catch (err) {
  console.error('VERIFY-REAL FAILED at step:', step, '-', err.message)
  await page.screenshot({ path: SHOTS + 'vr-99-fail.png' }).catch(() => {})
  process.exitCode = 1
} finally {
  await browser.close()
}

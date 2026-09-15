/* E2E smoke test: drives the full simulated run in headless Chrome.
   Usage: node e2e/smoke.mjs  (expects `vite preview` on :5199 already running)
   Screenshots land in e2e/shots/. */
import puppeteer from 'puppeteer-core'
import { mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const BASE = process.env.BASE_URL || 'http://localhost:5199/'
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
page.on('console', (m) => {
  if (m.type() === 'error') console.error('CONSOLE ERROR:', m.text())
})

let step = 'load'
try {
  await page.goto(BASE, { waitUntil: 'networkidle0' })

  // 1. hero visible
  step = 'hero'
  await page.waitForSelector('.fishHitbox', { timeout: 5000 })
  await page.waitForSelector('.previewBadge', { timeout: 5000 })
  await page.hover('.fishHitbox')
  await sleep(400)
  await page.screenshot({ path: SHOTS + '01-hero-light.png' })

  // 2. send a task
  step = 'send'
  await page.click('textarea.input')
  await page.type('textarea.input', '做一条数码赛道的短视频')
  await page.click('button.primary')

  // 3. pipeline + first gate
  step = 'gate_topic'
  await page.waitForSelector('.pipeline', { timeout: 8000 })
  await sleep(1200)
  await page.screenshot({ path: SHOTS + '02-pipeline-running.png' })
  await page.waitForSelector('.gate', { timeout: 8000 })
  await page.screenshot({ path: SHOTS + '03-gate-topic.png' })

  // pick 2nd candidate then confirm
  await page.$$eval('.cand input', (els) => els[1].click())
  await page.$$eval('.gateFoot .btnPrimary', (els) => els[0].click())

  // 4. script gate -> reject once -> confirm
  step = 'gate_script'
  await page.waitForFunction(
    () => document.querySelector('.gateTitle') && document.querySelector('.gateTitle').textContent.includes('脚本确认'),
    { timeout: 12000 }
  )
  await page.screenshot({ path: SHOTS + '04-gate-script.png' })
  await page.$$eval('.gateFoot .btnGhost', (els) => els[0].click()) // 驳回重跑
  await page.waitForFunction(() => !document.querySelector('.gate'), { timeout: 5000 })
  await page.waitForFunction(
    () => document.querySelector('.gateTitle') && document.querySelector('.gateTitle').textContent.includes('脚本确认'),
    { timeout: 12000 }
  )
  await page.$$eval('.gateFoot .btnPrimary', (els) => els[0].click())

  // 5. dark mode mid-run (headless Chrome may start dark via prefers-color-scheme)
  step = 'dark-toggle'
  const initialDark = await page.evaluate(() => document.body.hasAttribute('data-ds-dark-theme'))
  await page.$$eval('.foot .iconButton', (els) => els[0].click())
  await sleep(500)
  const flipped = await page.evaluate(() => document.body.hasAttribute('data-ds-dark-theme'))
  if (flipped === initialDark) throw new Error('theme toggle did not flip the attribute')
  // ensure we end up in dark for the dark screenshots
  if (!flipped) {
    await page.$$eval('.foot .iconButton', (els) => els[0].click())
    await sleep(500)
  }
  const darkOn = await page.evaluate(() => document.body.hasAttribute('data-ds-dark-theme'))
  if (!darkOn) throw new Error('dark theme attribute missing')

  // 6. preview gate
  step = 'gate_preview'
  await page.waitForFunction(
    () => document.querySelector('.gateTitle') && document.querySelector('.gateTitle').textContent.includes('成片预览'),
    { timeout: 20000 }
  )
  await page.screenshot({ path: SHOTS + '05-gate-preview-dark.png' })
  await page.$$eval('.gateFoot .btnPrimary', (els) => els[0].click())

  // 7. publish gate
  step = 'gate_publish'
  await page.waitForFunction(
    () => document.querySelector('.gateTitle') && document.querySelector('.gateTitle').textContent.includes('发布确认'),
    { timeout: 12000 }
  )
  await page.screenshot({ path: SHOTS + '06-gate-publish-dark.png' })
  await page.$$eval('.gateFoot .btnPrimary', (els) => els[0].click())

  // 8. review done
  step = 'review'
  await page.waitForSelector('.review', { timeout: 20000 })
  await sleep(1500)
  await page.screenshot({ path: SHOTS + '07-review-dark.png' })

  // 9. details panel final state
  step = 'panel'
  const stageTxt = await page.$$eval('.details .kv .v', (els) => els.map((e) => e.textContent))
  const stage = await page.$eval('.stageVal', (e) => e.textContent.trim())
  if (stage !== 'review') throw new Error('final stage != review, got ' + stage)
  const costTxt = await page.evaluate(() => document.querySelector('.details').textContent)
  const m = costTxt.match(/合计¥([\d.]+)/) || costTxt.match(/合计 ¥([\d.]+)/)
  if (!m) throw new Error('total cost not found in panel')
  const total = parseFloat(m[1])
  if (!(total > 5.45)) throw new Error('total cost too low: ' + total)

  // 10. back to light, post-run message
  step = 'post-run'
  await page.$$eval('.foot .iconButton', (els) => els[0].click()) // light again
  await page.click('textarea.input')
  await page.type('textarea.input', '再跑一轮')
  await page.click('button.primary')
  await sleep(600)
  const tail = await page.evaluate(() => document.querySelector('.column').textContent)
  if (!tail.includes('新任务')) throw new Error('post-run reply missing')

  // 11. new task button returns to hero
  step = 'new-task'
  await page.$$eval('.newSession', (els) => els[0].click())
  await page.waitForSelector('.fishHitbox', { timeout: 5000 })
  await page.screenshot({ path: SHOTS + '08-hero-again.png' })

  console.log('SMOKE OK · final stage =', stage, '· total cost =', total, '· steps passed:', step)
} catch (err) {
  console.error('SMOKE FAILED at step:', step, '-', err.message)
  await page.screenshot({ path: SHOTS + '99-fail.png' }).catch(() => {})
  process.exitCode = 1
} finally {
  await browser.close()
}

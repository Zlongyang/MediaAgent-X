/* E2E round 2: sidebar/nav/settings/projects/monitor/workflows + full new-video flow.
   Expects `vite preview` on :5199. Screenshots → e2e/shots/. */
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

async function setTheme(mode) {
  await page.evaluate((m) => {
    localStorage.setItem('max-theme', m)
  }, mode)
  await page.reload({ waitUntil: 'networkidle0' })
}

async function clickProject(name) {
  await page.$$eval('.projItem', (els, n) => {
    const el = els.find((e) => e.textContent.includes(n))
    if (!el) throw new Error('project not found: ' + n)
    el.click()
  }, name)
}

async function clickTab(label) {
  await page.$$eval('.tabs .tab', (els, l) => {
    const el = els.find((e) => e.textContent.trim() === l)
    if (!el) throw new Error('tab not found: ' + l)
    el.click()
  }, label)
  await sleep(300)
}

async function confirmGate(title) {
  await page.waitForFunction(
    (t) => document.querySelector('.gateTitle') && document.querySelector('.gateTitle').textContent.includes(t),
    { timeout: 20000 },
    title
  )
  await page.$$eval('.gateFoot .btnPrimary', (els) => els[0].click())
}

let step = 'init'
try {
  await page.goto(BASE, { waitUntil: 'networkidle0' })
  await setTheme('light')

  // 1. hero + account chip
  step = 'hero+account'
  await page.waitForSelector('.fishHitbox', { timeout: 6000 })
  await page.click('.workspace')
  await page.waitForSelector('.acctMenu', { timeout: 3000 })
  await page.screenshot({ path: SHOTS + 'r2-01-hero-account-menu.png' })
  await page.$$eval('.acctOption', (els) => els[1].click()) // B站
  await sleep(300)
  const chipTxt = await page.$eval('.workspaceLabel', (e) => e.textContent)
  if (!chipTxt.includes('B站')) throw new Error('account chip not switched: ' + chipTxt)

  // 2. sidebar collapse / expand
  step = 'sidebar-collapse'
  await page.click('.logoRow .toggle')
  await sleep(500)
  const railW = await page.$eval('.sidebarCol', (e) => e.getBoundingClientRect().width)
  if (railW > 80) throw new Error('sidebar not collapsed: ' + railW)
  await page.screenshot({ path: SHOTS + 'r2-02-sidebar-rail.png' })
  await page.click('.logoRow .toggle')
  await sleep(500)

  // 3. settings popover
  step = 'settings'
  await page.click('.foot .iconButton')
  await page.waitForSelector('.settingsPop', { timeout: 3000 })
  await page.screenshot({ path: SHOTS + 'r2-03-settings.png' })
  await page.$$eval('.segBtn', (els) => els[0].click()) // 暗色
  await sleep(300)
  const darkOn = await page.evaluate(() => document.body.hasAttribute('data-ds-dark-theme'))
  if (!darkOn) throw new Error('dark not applied from segmented')
  await page.$$eval('.segBtn', (els) => els[1].click()) // 冷色
  await sleep(300)
  await page.click('.foot .iconButton') // close popover
  await sleep(200)

  // 4. monitor board
  step = 'monitor-view'
  await page.$$eval('.navItem', (els) => els[1].click())
  await page.waitForSelector('.vcard', { timeout: 3000 })
  await page.screenshot({ path: SHOTS + 'r2-04-monitor.png' })
  await page.$$eval('.fchip', (els) => els[2].click()) // B站 filter
  await sleep(300)

  // 5. workflows
  step = 'workflows'
  await page.$$eval('.navItem', (els) => els[2].click())
  await page.waitForSelector('.wfs .row', { timeout: 3000 })
  await page.$$eval('.wfs .switch', (els) => els[2].click()) // enable wf-3
  await page.$$eval('.runBtn', (els) => els[0].click()) // 立即运行
  await page.waitForSelector('.toast', { timeout: 3000 })
  await page.screenshot({ path: SHOTS + 'r2-05-workflows.png' })
  await sleep(2600)

  // 6. published project (p-1001) — all tabs
  step = 'project-published'
  await clickProject('百元降噪耳机横评')
  await page.waitForSelector('.phead', { timeout: 3000 })
  await sleep(400)
  await page.screenshot({ path: SHOTS + 'r2-06-project-chat-workbench.png' })
  await clickTab('视频产出')
  await page.screenshot({ path: SHOTS + 'r2-07-project-output.png' })
  await clickTab('制作详情')
  await page.waitForSelector('.tbl', { timeout: 3000 })
  await page.screenshot({ path: SHOTS + 'r2-08-project-detail.png' })
  await clickTab('数据监控')
  await page.waitForSelector('.pmonitor .chart', { timeout: 3000 })
  await page.screenshot({ path: SHOTS + 'r2-09-project-monitor.png' })

  // 7. failed project
  step = 'project-failed'
  await clickProject('机械键盘入门')
  await clickTab('制作详情')
  await page.waitForSelector("tr[data-status='failed']", { timeout: 3000 })
  await page.screenshot({ path: SHOTS + 'r2-10-project-failed.png' })

  // 8. review project — gate confirm
  step = 'project-review'
  await clickProject('老人机')
  await page.waitForSelector('.staticChat .gate', { timeout: 3000 })
  await page.screenshot({ path: SHOTS + 'r2-11-project-review-gate.png' })
  await page.$$eval('.staticChat .gateFoot .btnPrimary', (els) => els[0].click())
  await sleep(400)
  const confirmed = await page.evaluate(() => document.querySelector('.staticChat').textContent.includes('成片已确认'))
  if (!confirmed) throw new Error('review gate confirm did not append message')

  // 9. generating project — live auto pipeline
  step = 'project-generating'
  await clickProject('618 耳机选购攻略')
  await page.waitForSelector('.chatPane .pipeline', { timeout: 8000 })
  await sleep(3500)
  await page.screenshot({ path: SHOTS + 'r2-12-project-generating-live.png' })

  // 10. new video full flow (light)
  step = 'full-flow'
  await page.$$eval('.newSession', (els) => els[0].click()) // aborts auto run, back to hero
  await page.waitForSelector('.fishHitbox', { timeout: 4000 })
  await page.click('textarea.input')
  await page.type('textarea.input', '做一条数码赛道的短视频')
  await page.click('button.primary')
  await page.waitForSelector('.pipeline', { timeout: 8000 })
  await confirmGate('选题确认')
  await sleep(800)
  // right details panel live + collapse/expand
  step = 'details-collapse'
  const stg = await page.$eval('.stageVal', (e) => e.textContent.trim())
  if (!stg) throw new Error('details panel stage empty')
  await page.click('.collapseBtn')
  await sleep(500)
  await page.waitForSelector('.detailsPill', { timeout: 3000 })
  await page.click('.detailsPill')
  await sleep(500)
  const w = await page.$eval('.detailsCol', (e) => e.getBoundingClientRect().width)
  if (w < 200) throw new Error('details did not reopen')
  await page.screenshot({ path: SHOTS + 'r2-13-run-mid-light.png' })
  await confirmGate('脚本确认')
  await confirmGate('成片预览')
  await confirmGate('发布确认')
  await page.waitForSelector('.review', { timeout: 25000 })
  await sleep(1200)
  await page.screenshot({ path: SHOTS + 'r2-14-run-done-light.png' })
  // new project landed in B站 folder as 已发布
  const projOk = await page.evaluate(() => {
    const items = [...document.querySelectorAll('.projItem')]
    return items.some((e) => e.textContent.includes('做一条数码赛道') && e.textContent.includes('已发布'))
  })
  if (!projOk) throw new Error('session project not published in sidebar')

  // 11. dark pass: hero + run-done view
  step = 'dark-pass'
  await setTheme('dark')
  await page.waitForSelector('.fishHitbox', { timeout: 4000 })
  await page.screenshot({ path: SHOTS + 'r2-15-hero-dark.png' })
  await clickProject('百元降噪耳机横评')
  await clickTab('数据监控')
  await page.screenshot({ path: SHOTS + 'r2-16-project-monitor-dark.png' })

  console.log('SMOKE2 OK · last step =', step)
} catch (err) {
  console.error('SMOKE2 FAILED at step:', step, '-', err.message)
  await page.screenshot({ path: SHOTS + 'r2-99-fail.png' }).catch(() => {})
  process.exitCode = 1
} finally {
  await browser.close()
}

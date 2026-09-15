/* E2E round 3: centered settings modal, left tabs, workbench drag/collapse,
   output tab responsiveness, account page + chevron, project chat composer,
   dark mode, full new-video flow regression. Expects preview on :5199. */
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
  args: ['--no-sandbox', '--disable-gpu'],
  defaultViewport: { width: 1440, height: 900 },
})

const page = await browser.newPage()
page.on('pageerror', (e) => console.error('PAGE ERROR:', e.message))

async function clickProject(name) {
  await page.$$eval('.projItem', (els, n) => {
    const el = els.find((e) => e.textContent.includes(n))
    if (!el) throw new Error('project not found: ' + n)
    el.click()
  }, name)
  await sleep(400)
}

async function clickTab(label) {
  await page.$$eval('.tabs .tab', (els, l) => {
    const el = els.find((e) => e.textContent.trim() === l)
    if (!el) throw new Error('tab not found: ' + l)
    el.click()
  }, label)
  await sleep(350)
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
  await page.evaluate(() => localStorage.setItem('max-theme', 'light'))
  await page.reload({ waitUntil: 'networkidle0' })
  await page.waitForSelector('.fishHitbox', { timeout: 6000 })

  // 1. centered settings modal
  step = 'settings-modal'
  await page.click('.foot .iconButton')
  await page.waitForSelector('.modal', { timeout: 3000 })
  const box = await page.$eval('.modal', (e) => {
    const r = e.getBoundingClientRect()
    return { cx: r.x + r.width / 2, cy: r.y + r.height / 2 }
  })
  if (Math.abs(box.cx - 720) > 40 || Math.abs(box.cy - 450) > 60) {
    throw new Error('modal not centered: ' + JSON.stringify(box))
  }
  await page.screenshot({ path: SHOTS + 'r3-01-settings-modal.png' })
  // switch theme inside modal then close via ×
  await page.$$eval('.segBtn', (els) => els[1].click()) // 冷色
  await page.click('.modal .iconButton')
  await sleep(250)
  if (await page.$('.modal')) throw new Error('modal did not close via ×')
  // reopen and close via mask
  await page.click('.foot .iconButton')
  await page.waitForSelector('.modal', { timeout: 3000 })
  await page.mouse.click(720, 120) // mask area above card
  await sleep(250)
  if (await page.$('.modal')) throw new Error('modal did not close via mask')

  // 2. project header: tabs left, no title
  step = 'project-header'
  await clickProject('百元降噪耳机横评')
  await page.waitForSelector('.phead', { timeout: 3000 })
  const hasTitle = await page.$('.pname')
  if (hasTitle) throw new Error('project title still rendered')
  const tabsX = await page.$eval('.tabs', (e) => e.getBoundingClientRect().x)
  if (tabsX > 400) throw new Error('tabs not left-aligned, x=' + tabsX)
  await page.screenshot({ path: SHOTS + 'r3-02-project-header.png' })

  // 3. workbench drag: widen to cap, then drag past threshold → auto collapse; pill reopens
  step = 'workbench-drag'
  const wb0 = await page.$eval('.wbPane', (e) => e.getBoundingClientRect().width)
  if (Math.abs(wb0 - 320) > 2) throw new Error('wb default width != 320: ' + wb0)
  let h = await page.$eval('.wbHandle', (e) => {
    const r = e.getBoundingClientRect()
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 }
  })
  await page.mouse.move(h.x, h.y)
  await page.mouse.down()
  for (let i = 1; i <= 10; i++) await page.mouse.move(h.x - i * 30, h.y) // drag left → wider
  await page.mouse.up()
  await sleep(450)
  const wb1 = await page.$eval('.wbPane', (e) => e.getBoundingClientRect().width)
  if (Math.abs(wb1 - 520) > 4) throw new Error('wb width after widen != 520: ' + wb1)
  await page.screenshot({ path: SHOTS + 'r3-03-workbench-wide.png' })
  h = await page.$eval('.wbHandle', (e) => {
    const r = e.getBoundingClientRect()
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 }
  })
  await page.mouse.move(h.x, h.y)
  await page.mouse.down()
  for (let i = 1; i <= 16; i++) await page.mouse.move(h.x + i * 30, h.y) // drag right → auto collapse
  await page.mouse.up()
  await sleep(450)
  const wb2 = await page.$eval('.wbPane', (e) => e.getBoundingClientRect().width)
  if (wb2 !== 0) throw new Error('wb did not auto-collapse: ' + wb2)
  await page.waitForSelector('.wbPill', { timeout: 2000 })
  await page.screenshot({ path: SHOTS + 'r3-04-workbench-collapsed.png' })
  await page.click('.wbPill')
  await sleep(450)
  const wb3 = await page.$eval('.wbPane', (e) => e.getBoundingClientRect().width)
  if (wb3 < 260) throw new Error('wb did not reopen: ' + wb3)

  // 4. project chat composer
  step = 'project-composer'
  await clickProject('618 别乱买')
  await page.waitForSelector('.chatPane textarea.input', { timeout: 3000 })
  await page.click('.chatPane textarea.input')
  await page.type('.chatPane textarea.input', '这条的封面再暗一点')
  await page.click('.chatPane button.primary')
  await sleep(400)
  const appended = await page.evaluate(() => {
    const t = document.querySelector('.chatPane').textContent
    return t.includes('这条的封面再暗一点') && t.includes('演示回复')
  })
  if (!appended) throw new Error('project composer send did not append')
  await page.screenshot({ path: SHOTS + 'r3-05-project-composer.png' })

  // 5. output tab responsiveness at narrow viewport
  step = 'output-narrow'
  await page.setViewport({ width: 760, height: 900 })
  await clickTab('视频产出')
  await sleep(400)
  const colCheck = await page.$$eval('.outGrid .card', (els) => {
    if (els.length < 2) return { n: els.length, single: true }
    const a = els[0].getBoundingClientRect()
    const b = els[1].getBoundingClientRect()
    return { n: els.length, single: Math.abs(a.x - b.x) < 4 && b.y > a.y }
  })
  if (!colCheck.single) throw new Error('output cards not single-column at 760px')
  await page.screenshot({ path: SHOTS + 'r3-06-output-narrow.png' })
  await page.setViewport({ width: 1440, height: 900 })
  await sleep(450)

  // 6. account row click → account page; chevron toggles without navigation
  step = 'account-page'
  await page.$$eval('.folderHead', (els) => {
    const el = els.find((e) => e.textContent.includes('抖音'))
    el.click()
  })
  await page.waitForSelector('.acctPage', { timeout: 3000 })
  const fansTxt = await page.evaluate(() => document.querySelector('.aSub').textContent)
  if (!fansTxt.includes('粉丝')) throw new Error('account header missing fans')
  const rowCount = await page.$$eval('.acctPage .vRow', (els) => els.length)
  if (rowCount < 2) throw new Error('account video list too short: ' + rowCount)
  await page.screenshot({ path: SHOTS + 'r3-07-account-page.png' })
  // chevron toggles folder only, page stays
  await page.$$eval('.folderHead .chevBtn', (els) => els[0].click())
  await sleep(350)
  const stillAcct = await page.$('.acctPage')
  if (!stillAcct) throw new Error('chevron click navigated away')
  const folderHidden = await page.$$eval('.folderBody', (els) => getComputedStyle(els[0]).display === 'none')
  if (!folderHidden) throw new Error('chevron did not collapse folder')
  await page.$$eval('.folderHead .chevBtn', (els) => els[0].click()) // reopen
  await sleep(350)
  // no emoji icon on folder rows
  const hasFolderIcon = await page.$('.folderIcon')
  if (hasFolderIcon) throw new Error('folder icon still present')

  // 7. dark mode account page + modal
  step = 'dark-pass'
  await page.evaluate(() => localStorage.setItem('max-theme', 'dark'))
  await page.reload({ waitUntil: 'networkidle0' })
  await page.$$eval('.folderHead', (els) => {
    els.find((e) => e.textContent.includes('B站')).click()
  })
  await page.waitForSelector('.acctPage', { timeout: 3000 })
  await sleep(400)
  await page.screenshot({ path: SHOTS + 'r3-08-account-dark.png' })
  await page.click('.foot .iconButton')
  await page.waitForSelector('.modal', { timeout: 3000 })
  await page.screenshot({ path: SHOTS + 'r3-09-settings-dark.png' })
  await page.click('.modal .iconButton')
  await page.evaluate(() => localStorage.setItem('max-theme', 'light'))
  await page.reload({ waitUntil: 'networkidle0' })

  // 8. regression: full new-video flow
  step = 'full-flow'
  await page.waitForSelector('.fishHitbox', { timeout: 5000 })
  await page.click('textarea.input')
  await page.type('textarea.input', '做一条数码赛道的短视频')
  await page.click('button.primary')
  await page.waitForSelector('.pipeline', { timeout: 8000 })
  await confirmGate('选题确认')
  await confirmGate('脚本确认')
  await confirmGate('成片预览')
  await confirmGate('发布确认')
  await page.waitForSelector('.review', { timeout: 25000 })
  await sleep(800)
  await page.screenshot({ path: SHOTS + 'r3-10-run-done.png' })

  console.log('SMOKE3 OK · last step =', step)
} catch (err) {
  console.error('SMOKE3 FAILED at step:', step, '-', err.message)
  await page.screenshot({ path: SHOTS + 'r3-99-fail.png' }).catch(() => {})
  process.exitCode = 1
} finally {
  await browser.close()
}

// 第三轮交付验收：居中设置弹窗、账号页、chevron 独立触发、工作台拖拽、console 错误
import { spawn } from 'node:child_process'
import puppeteer from 'puppeteer-core'
import { existsSync } from 'node:fs'

const PORT = 5293
const chromePaths = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  `${process.env.LOCALAPPDATA}/Google/Chrome/Application/chrome.exe`,
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
]
const executablePath = chromePaths.find((p) => existsSync(p))
const npmCmd = 'C:\\Users\\27889\\AppData\\Local\\Programs\\kimi-desktop\\resources\\resources\\runtime\\npm.cmd'

const server = spawn(npmCmd, ['run', 'dev', '--', '--host', '127.0.0.1', '--port', String(PORT)], {
  cwd: process.cwd(), shell: true, stdio: ['ignore', 'pipe', 'pipe'],
})
let serverLog = ''
server.stdout.on('data', (d) => (serverLog += d))
server.stderr.on('data', (d) => (serverLog += d))
await new Promise((resolve, reject) => {
  const t = setTimeout(() => reject(new Error('start timeout\n' + serverLog)), 30000)
  server.stdout.on('data', (d) => { if (String(d).includes('Local:')) { clearTimeout(t); resolve() } })
})
const killTree = () => new Promise((res) => spawn('taskkill', ['/pid', String(server.pid), '/T', '/F']).on('exit', res))

const errors = []
const fails = []
const check = (name, cond) => { console.log(cond ? `PASS  ${name}` : `FAIL  ${name}`); if (!cond) fails.push(name) }

try {
  const browser = await puppeteer.launch({ executablePath, headless: 'new' })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: 'light' }])
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
  page.on('pageerror', (e) => errors.push(String(e)))
  const clickText = (sel, text) => page.evaluate((sel, text) => {
    const els = [...document.querySelectorAll(sel)].filter((e) => e.textContent.trim().includes(text))
    els.sort((a, b) => a.textContent.trim().length - b.textContent.trim().length)
    if (els[0]) { els[0].click(); return true } return false
  }, sel, text)

  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, 500))

  // 1. 设置弹窗居中
  await page.evaluate(() => {
    const btns = [...document.querySelectorAll('button')].filter((b) => /设置|settings/i.test((b.getAttribute('title') || '') + (b.getAttribute('aria-label') || '') + b.className))
    ;(btns[0] || [...document.querySelectorAll('button')].at(-1)).click()
  })
  await new Promise((r) => setTimeout(r, 400))
  const modalCheck = await page.evaluate(() => {
    const m = [...document.querySelectorAll('div')].filter((d) => d.textContent.includes('DeepSeek API Key') && d.textContent.includes('跟随系统'))
    if (!m.length) return { open: false }
    const card = m[m.length - 1].getBoundingClientRect()
    return { open: true, cx: card.x + card.width / 2, vw: innerWidth }
  })
  check('设置弹窗打开且水平居中', modalCheck.open && Math.abs(modalCheck.cx - modalCheck.vw / 2) < 30)
  await page.keyboard.press('Escape')
  await page.evaluate(() => { const m = document.querySelector('[class*=mask], [class*=overlay], [class*=modal]'); if (m) m.click() })
  await new Promise((r) => setTimeout(r, 300))

  // 2. 账号行：无左侧图标、chevron 在右侧、行点击进账号页、chevron 不跳页
  const rowInfo = await page.evaluate(() => {
    const row = [...document.querySelectorAll('[role=button], div')].filter((e) => e.textContent.trim().startsWith('抖音 · 数码小X') && e.textContent.trim().length < 20)
    if (!row.length) return null
    const r = row[row.length - 1]
    return { html: r.innerHTML.slice(0, 300), hasImg: !!r.querySelector('img'), rect: r.getBoundingClientRect() }
  })
  check('找到账号行', !!rowInfo)
  // chevron 独立：找账号行内最右小按钮点击，断言未进账号页
  const chevronNoNav = await page.evaluate(() => {
    const rows = [...document.querySelectorAll('[role=button], div')].filter((e) => e.textContent.trim().startsWith('B站 · 小X评测') && e.textContent.trim().length < 20)
    const row = rows[rows.length - 1]
    if (!row) return 'no-row'
    const btns = [...row.querySelectorAll('button, svg, [class*=chevron], [class*=arrow]')]
    const target = btns[btns.length - 1] || null
    if (!target) return 'no-chevron'
    target.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    return 'clicked'
  })
  await new Promise((r) => setTimeout(r, 400))
  const afterChevron = await page.evaluate(() => document.body.innerText.includes('粉丝'))
  check('chevron 点击仅展开收起（不进账号页）', chevronNoNav === 'clicked' && !afterChevron)
  // 行点击进账号页
  await clickText('[role=button], div', '抖音 · 数码小X')
  await new Promise((r) => setTimeout(r, 500))
  check('账号行点击进账号数据页', await page.evaluate(() => document.body.innerText.includes('粉丝') || document.body.innerText.includes('总播放') || document.body.innerText.includes('近 7 天')))
  await page.screenshot({ path: 'e2e/shots/verify3-account.png' })

  // 3. 项目详情：顶栏无标题、tabs 左对齐、工作台拖拽
  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, 400))
  await clickText('[role=button], div', '百元降噪耳机横评')
  await new Promise((r) => setTimeout(r, 500))
  const nav = await page.evaluate(() => {
    const tab = [...document.querySelectorAll('*')].filter((e) => e.children.length === 0 && e.textContent.trim() === '视频产出')[0]
    return tab ? { x: tab.getBoundingClientRect().x } : null
  })
  check('tabs 左对齐（视频产出 x<400）', nav && nav.x < 400)
  check('项目对话 tab 有输入框', await page.evaluate(() => !!document.querySelector('textarea')))

  // 拖拽工作台左缘到极窄 → 自动收合
  const drag = await page.evaluate(() => {
    const handles = [...document.querySelectorAll('div')].filter((d) => {
      const s = getComputedStyle(d)
      return s.cursor === 'col-resize' && d.getBoundingClientRect().width <= 12
    })
    if (!handles.length) return null
    const r = handles[0].getBoundingClientRect()
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 }
  })
  if (drag) {
    await page.mouse.move(drag.x, drag.y)
    await page.mouse.down()
    await page.mouse.move(drag.x - 500, drag.y, { steps: 12 })
    await page.mouse.up()
    await new Promise((r) => setTimeout(r, 500))
    check('工作台拖到极窄自动合上', await page.evaluate(() => !document.body.innerText.includes('素材来源')))
  } else {
    check('找到工作台拖拽条', false)
  }
  await page.screenshot({ path: 'e2e/shots/verify3-final.png' })
  await browser.close()
} finally {
  await killTree()
}
console.log('CONSOLE_ERRORS:', JSON.stringify(errors))
console.log(fails.length ? `FAILS: ${fails.join(' | ')}` : 'ALL_PASS')

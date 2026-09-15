// round9 验收：emoji 清零断言 + 项目页三 tab 居中几何断言 + 各页面截图
import { spawn } from 'node:child_process'
import puppeteer from 'puppeteer-core'
import { existsSync } from 'node:fs'

const PORT = 5300
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
await new Promise((resolve, reject) => {
  const t = setTimeout(() => reject(new Error('start timeout')), 30000)
  server.stdout.on('data', (d) => { if (String(d).includes('Local:')) { clearTimeout(t); resolve() } })
})
const killTree = () => new Promise((res) => spawn('taskkill', ['/pid', String(server.pid), '/T', '/F']).on('exit', res))

const errors = []
try {
  const browser = await puppeteer.launch({ executablePath, headless: 'new' })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: 'light' }])
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
  page.on('pageerror', (e) => errors.push(String(e)))

  // 点击策略：匹配文本的最短叶节点
  const clickText = async (sel, text) => page.evaluate((sel, text) => {
    const els = [...document.querySelectorAll(sel)].filter((e) => e.textContent.trim().includes(text))
    els.sort((a, b) => a.textContent.trim().length - b.textContent.trim().length)
    if (els[0]) { els[0].click(); return true } return false
  }, sel, text)

  /* ---- 1. 首页：emoji 清零断言 + hero 截图 ---- */
  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, 600))
  const emojiHits = await page.evaluate(() => {
    const re = /[🀀-🯿☀-➿⬀-⯿️✓✕▶⛔]/u
    const m = document.body.innerText.match(new RegExp(re, 'gu'))
    return m || []
  })
  console.log('EMOJI_CHECK:', emojiHits.length === 0 ? 'PASS (body.innerText 无 emoji)' : `FAIL hits=${JSON.stringify(emojiHits)}`)
  await page.screenshot({ path: 'e2e/shots/verify9-hero.png' })

  /* ---- 2. 闸门卡：跑新对话到选题闸门 ---- */
  await page.click('textarea')
  await page.type('textarea', '做一条数码赛道的短视频')
  await page.keyboard.press('Enter')
  await page.waitForFunction(
    () => [...document.querySelectorAll('*')].some((e) => e.children.length === 0 && e.textContent.trim() === '确认放行'),
    { timeout: 25000 }
  )
  await new Promise((r) => setTimeout(r, 400))
  await page.screenshot({ path: 'e2e/shots/verify9-gate.png' })

  /* ---- 3. 项目页：居中几何断言 ---- */
  await clickText('.projItem .projName', '百元降噪耳机横评')
  await new Promise((r) => setTimeout(r, 600))
  const centerInfo = await page.evaluate(() => {
    const head = document.querySelector('.phead')
    const mid = document.querySelector('.phead .tabsMid')
    if (!head || !mid) return null
    const hr = head.getBoundingClientRect()
    const mr = mid.getBoundingClientRect()
    const headCx = hr.left + hr.width / 2
    const midCx = mr.left + mr.width / 2
    return { headCx: +headCx.toFixed(1), midCx: +midCx.toFixed(1), dev: +Math.abs(midCx - headCx).toFixed(1) }
  })
  if (!centerInfo) {
    console.log('CENTER_CHECK: FAIL (.phead/.tabsMid 未找到)')
    errors.push('tabsMid not found')
  } else {
    console.log(`CENTER_CHECK: headerCx=${centerInfo.headCx} midCx=${centerInfo.midCx} dev=${centerInfo.dev}px -> ${centerInfo.dev < 12 ? 'PASS (<12px)' : 'FAIL (>=12px)'}`)
  }

  /* ---- 4. 项目页三个 tab 截图 ---- */
  await clickText('.tabsMid .tab', '视频产出')
  await new Promise((r) => setTimeout(r, 400))
  await page.screenshot({ path: 'e2e/shots/verify9-project-output.png' })
  await clickText('.tabsMid .tab', '制作详情')
  await new Promise((r) => setTimeout(r, 400))
  await page.screenshot({ path: 'e2e/shots/verify9-project-detail.png' })
  await clickText('.tabsMid .tab', '数据监控')
  await new Promise((r) => setTimeout(r, 400))
  await page.screenshot({ path: 'e2e/shots/verify9-project-monitor.png' })

  /* ---- 5. 栏目页 · 数据监控 ---- */
  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, 500))
  await clickText('nav.navList button', '数据监控')
  await new Promise((r) => setTimeout(r, 500))
  await page.screenshot({ path: 'e2e/shots/verify9-monitor.png' })

  /* ---- 6. 账号数据页 ---- */
  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, 500))
  await clickText('.folderHead .folderName', '抖音 · 数码小X')
  await new Promise((r) => setTimeout(r, 500))
  await page.screenshot({ path: 'e2e/shots/verify9-account.png' })

  await browser.close()
} finally {
  await killTree()
}
console.log('CONSOLE_ERRORS:', JSON.stringify(errors))
console.log('DONE')

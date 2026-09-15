// 内容居中验收：三 tab 内容水平居中 + 顶栏恢复左对齐
import { spawn } from 'node:child_process'
import puppeteer from 'puppeteer-core'
import { existsSync } from 'node:fs'

const PORT = 5301
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
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
  page.on('pageerror', (e) => errors.push(String(e)))
  const clickText = async (sel, text) => page.evaluate((sel, text) => {
    const els = [...document.querySelectorAll(sel)].filter((e) => e.textContent.trim().includes(text))
    els.sort((a, b) => a.textContent.trim().length - b.textContent.trim().length)
    if (els[0]) { els[0].click(); return true } return false
  }, sel, text)

  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, 400))
  await clickText('[role=button], div, span', '百元降噪耳机横评')
  await new Promise((r) => setTimeout(r, 500))

  // 顶栏：全部 tab 在一个左对齐 nav 里
  console.log('TABS_LAYOUT:', await page.evaluate(() => {
    const navs = [...document.querySelectorAll('.phead nav')]
    const first = document.querySelector('.phead .tab')
    return `navs=${navs.length} firstTabLeft=${Math.round(first.getBoundingClientRect().left)}`
  }))

  const checkCentered = async (tabLabel, rootSel, name) => {
    await clickText('.phead .tab', tabLabel)
    await new Promise((r) => setTimeout(r, 400))
    console.log(`CENTER ${name}:`, await page.evaluate((rootSel) => {
      const host = document.querySelector('.tabBody.scroll:not([style*="display: none"])') || [...document.querySelectorAll('.tabBody.scroll')].find((e) => e.getBoundingClientRect().height > 0)
      const el = host.querySelector(rootSel)
      const hr = host.getBoundingClientRect(), er = el.getBoundingClientRect()
      const leftGap = Math.round(er.left - hr.left), rightGap = Math.round(hr.right - er.right)
      return `leftGap=${leftGap} rightGap=${rightGap} dev=${Math.abs(leftGap - rightGap)}px`
    }, rootSel))
    await page.screenshot({ path: `e2e/shots/verify10-${name}.png` })
  }

  await checkCentered('视频产出', '.output', 'output')
  await checkCentered('制作详情', '.detail', 'detail')
  await checkCentered('数据监控', '.pmonitor', 'monitor')
  await browser.close()
} finally {
  await killTree()
}
console.log('CONSOLE_ERRORS:', JSON.stringify(errors))
console.log('DONE')

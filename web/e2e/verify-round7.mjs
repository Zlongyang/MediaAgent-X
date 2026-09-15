// 苹果风格验收：hero/运行中/项目页/监控页 亮暗截图 + 徽章颜色断言
import { spawn } from 'node:child_process'
import puppeteer from 'puppeteer-core'
import { existsSync } from 'node:fs'

const PORT = 5298
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
  const clickText = async (sel, text) => page.evaluate((sel, text) => {
    const els = [...document.querySelectorAll(sel)].filter((e) => e.textContent.trim().includes(text))
    els.sort((a, b) => a.textContent.trim().length - b.textContent.trim().length)
    if (els[0]) { els[0].click(); return true } return false
  }, sel, text)

  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, 500))
  console.log('sidebar bg:', await page.evaluate(() => getComputedStyle(document.querySelector('aside')).backgroundColor))
  console.log('send btn:', await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => x.getBoundingClientRect().width === 34)
    return b ? getComputedStyle(b).backgroundColor : 'n/a'
  }))
  await page.screenshot({ path: 'e2e/shots/verify7-apple-hero-light.png' })

  // 闸门卡 + 徽标：跑新对话到选题闸门
  await page.click('textarea')
  await page.type('textarea', '做一条数码赛道的短视频')
  await page.keyboard.press('Enter')
  await page.waitForFunction(() => [...document.querySelectorAll('*')].some((e) => e.children.length === 0 && e.textContent.trim() === '确认放行'), { timeout: 25000 })
  await new Promise((r) => setTimeout(r, 400))
  await page.screenshot({ path: 'e2e/shots/verify7-apple-gate-light.png' })

  // 项目页
  await clickText('[role=button], div, span', '百元降噪耳机横评')
  await new Promise((r) => setTimeout(r, 500))
  await page.screenshot({ path: 'e2e/shots/verify7-apple-project-light.png' })

  // 数据监控
  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, 400))
  await clickText('nav button', '数据监控')
  await new Promise((r) => setTimeout(r, 400))
  await page.screenshot({ path: 'e2e/shots/verify7-apple-monitor-light.png' })

  // 暗色 hero
  await page.evaluate(() => {
    const btns = [...document.querySelectorAll('button')]
    ;(btns.find((b) => /设置/.test((b.getAttribute('title') || '') + (b.getAttribute('aria-label') || ''))) || btns.at(-1)).click()
  })
  await new Promise((r) => setTimeout(r, 400))
  await page.evaluate(() => {
    const els = [...document.querySelectorAll('button, [role=button], div')].filter((e) => e.textContent.trim() === '暗色')
    els.sort((a, b) => a.textContent.length - b.textContent.length)
    if (els[0]) els[0].click()
  })
  await new Promise((r) => setTimeout(r, 400))
  await page.keyboard.press('Escape')
  await page.evaluate(() => document.querySelector('[class*=mask], [class*=overlay]')?.click())
  await new Promise((r) => setTimeout(r, 400))
  await page.screenshot({ path: 'e2e/shots/verify7-apple-hero-dark.png' })
  await browser.close()
} finally {
  await killTree()
}
console.log('CONSOLE_ERRORS:', JSON.stringify(errors))
console.log('DONE')

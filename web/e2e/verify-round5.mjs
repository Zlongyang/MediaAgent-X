// Logo 替换验收：hero + 侧栏新标渲染（亮/暗）
import { spawn } from 'node:child_process'
import puppeteer from 'puppeteer-core'
import { existsSync } from 'node:fs'

const PORT = 5296
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
  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, 500))
  // hero 区新 logo 应为方形 svg（34x34）
  console.log('hero logo square:', await page.evaluate(() => {
    const s = document.querySelector('.headline svg, .fishHitbox svg, .fish')
    if (!s) return 'MISSING'
    const r = s.getBoundingClientRect()
    return `${Math.round(r.width)}x${Math.round(r.height)}`
  }))
  await page.screenshot({ path: 'e2e/shots/verify5-logo-light.png' })
  // 暗色
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
  await page.screenshot({ path: 'e2e/shots/verify5-logo-dark.png' })
  await browser.close()
} finally {
  await killTree()
}
console.log('CONSOLE_ERRORS:', JSON.stringify(errors))
console.log('DONE')

// Logo 画廊验收：打开 /logo-gallery.html 截全页图
import { spawn } from 'node:child_process'
import puppeteer from 'puppeteer-core'
import { existsSync } from 'node:fs'

const PORT = 5295
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
  await page.setViewport({ width: 1200, height: 1000 })
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
  page.on('pageerror', (e) => errors.push(String(e)))
  const res = await page.goto(`http://127.0.0.1:${PORT}/logo-gallery.html`, { waitUntil: 'networkidle0' })
  console.log('HTTP', res.status())
  await new Promise((r) => setTimeout(r, 500))
  console.log('cards:', await page.evaluate(() => document.querySelectorAll('.card').length))
  await page.screenshot({ path: 'e2e/shots/logo-gallery-full.png', fullPage: true })
  // 再截一张视口大小方便聊天内查看
  await page.screenshot({ path: 'e2e/shots/logo-gallery.png' })
  await browser.close()
} finally {
  await killTree()
}
console.log('CONSOLE_ERRORS:', JSON.stringify(errors))
console.log('DONE')

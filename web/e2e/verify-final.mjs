// 交付验收：启动 vite dev server（模拟 Kimi Work 的 --host --port 转发），
// 强制亮色主题截图首屏与会话页，抓 console 错误，结束后杀掉所有子进程。
import { spawn } from 'node:child_process'
import puppeteer from 'puppeteer-core'
import { existsSync, readdirSync } from 'node:fs'

const PORT = 5291
const chromePaths = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  `${process.env.LOCALAPPDATA}/Google/Chrome/Application/chrome.exe`,
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
]
const executablePath = chromePaths.find((p) => existsSync(p))
if (!executablePath) throw new Error('no chrome/edge found')

// 与 Kimi Work 相同的启动方式：npm run dev -- --host --port <port>
const server = spawn('npm', ['run', 'dev', '--', '--host', '127.0.0.1', '--port', String(PORT)], {
  cwd: process.cwd(),
  shell: true,
  stdio: ['ignore', 'pipe', 'pipe'],
})
let serverLog = ''
server.stdout.on('data', (d) => (serverLog += d))
server.stderr.on('data', (d) => (serverLog += d))

const waitForServer = new Promise((resolve, reject) => {
  const t = setTimeout(() => reject(new Error('server start timeout\n' + serverLog)), 30000)
  server.stdout.on('data', (d) => {
    if (String(d).includes('Local:')) { clearTimeout(t); resolve() }
  })
})

const killTree = () => new Promise((resolve) => {
  spawn('taskkill', ['/pid', String(server.pid), '/T', '/F'], { shell: true }).on('exit', resolve)
})

try {
  await waitForServer
  const browser = await puppeteer.launch({ executablePath, headless: 'new', args: ['--force-color-profile=srgb'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: 'light' }])
  const errors = []
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
  page.on('pageerror', (e) => errors.push(String(e)))

  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, 600))
  await page.screenshot({ path: 'e2e/shots/verify-01-hero-light.png' })

  // 发送任务，跑到选题闸门
  await page.click('textarea')
  await page.type('textarea', '做一条数码赛道的短视频')
  await page.keyboard.press('Enter')
  await page.waitForFunction(
    () => document.body.innerText.includes('选题确认'),
    { timeout: 25000 },
  )
  await new Promise((r) => setTimeout(r, 400))
  await page.screenshot({ path: 'e2e/shots/verify-02-gate-light.png' })

  console.log('CONSOLE_ERRORS:', JSON.stringify(errors))
  await browser.close()
} finally {
  await killTree()
}
console.log('VERIFY_DONE')

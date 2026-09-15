// 第四轮验收：对话导航已删、新对话按钮、项目顶栏无状态徽章
import { spawn } from 'node:child_process'
import puppeteer from 'puppeteer-core'
import { existsSync } from 'node:fs'

const PORT = 5294
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

  check('按钮已改名「新对话」', await page.evaluate(() => document.body.innerText.includes('新对话')))
  check('侧栏无「对话」导航项', await page.evaluate(() => {
    const nav = document.querySelector('nav')
    return nav && ![...nav.querySelectorAll('button')].some((b) => b.textContent.trim() === '对话')
  }))
  check('侧栏仍有两个栏目', await page.evaluate(() => {
    const nav = document.querySelector('nav')
    return nav && nav.textContent.includes('数据监控') && nav.textContent.includes('已安排工作流')
  }))
  await page.screenshot({ path: 'e2e/shots/verify4-sidebar.png' })

  // 新对话按钮可回 hero（从栏目页切回）
  await clickText('nav button', '数据监控')
  await new Promise((r) => setTimeout(r, 400))
  await clickText('button', '新对话')
  await new Promise((r) => setTimeout(r, 400))
  check('新对话按钮回到 hero', await page.evaluate(() => (document.querySelector('textarea')?.placeholder || '').includes('给总编')))

  // 项目顶栏无状态徽章
  const clicked = await clickText('[role=button], div, span', '百元降噪耳机横评')
  await new Promise((r) => setTimeout(r, 600))
  const headInfo = await page.evaluate(() => {
    const head = document.querySelector('header.phead') || document.querySelector('header')
    return head ? { text: head.textContent } : { text: null, body: document.body.innerText.slice(0, 200) }
  })
  console.log('clicked project:', clicked, '| header:', JSON.stringify(headInfo).slice(0, 300))
  check('项目顶栏无发布状态徽章', !!(headInfo.text && !headInfo.text.includes('已发布') && !headInfo.text.includes('待审查')))
  check('项目顶栏 tabs 完整', !!(headInfo.text && ['对话', '视频产出', '制作详情', '数据监控'].every((t) => headInfo.text.includes(t))))
  await page.screenshot({ path: 'e2e/shots/verify4-project.png' })
  await browser.close()
} finally {
  await killTree()
}
console.log('CONSOLE_ERRORS:', JSON.stringify(errors))
console.log(fails.length ? `FAILS: ${fails.join(' | ')}` : 'ALL_PASS')

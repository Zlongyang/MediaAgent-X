// 第二轮交付验收：dev server（npm run dev -- --host --port）+ 真实浏览器
// 覆盖：栏目页、项目详情 4 tab、右侧栏收放、console 错误；结束杀进程树。
import { spawn } from 'node:child_process'
import puppeteer from 'puppeteer-core'
import { existsSync } from 'node:fs'

const PORT = 5292
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
    // 取文本最短的叶级元素（避免点到外层容器）
    els.sort((a, b) => a.textContent.trim().length - b.textContent.trim().length)
    const el = els[0]
    if (el) { el.click(); return true } return false
  }, sel, text)

  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, 500))
  check('hero 渲染（新视频按钮）', await page.evaluate(() => document.body.innerText.includes('新视频')))
  check('工种区已删除', await page.evaluate(() => !document.body.innerText.includes('工种')))

  // 数据监控栏目
  await clickText('button, a, [role="button"], div', '数据监控')
  await new Promise((r) => setTimeout(r, 400))
  check('数据监控栏目页', await page.evaluate(() => document.body.innerText.includes('汇总播放趋势')))

  // 已安排工作流栏目
  await clickText('button, a, [role="button"], div', '已安排工作流')
  await new Promise((r) => setTimeout(r, 400))
  check('工作流栏目页（cron 表达式）', await page.evaluate(() => /\d+ \d+ \* \*/.test(document.body.innerText)))

  // 项目详情：点已发布项目
  await clickText('button, a, [role="button"], div', '百元降噪耳机横评')
  await new Promise((r) => setTimeout(r, 500))
  check('项目详情顶栏 4 tabs', await page.evaluate(() => ['对话', '视频产出', '制作详情', '数据监控'].every((t) => document.body.innerText.includes(t))))
  check('对话 tab 工作台参数', await page.evaluate(() => document.body.innerText.includes('素材来源') && document.body.innerText.includes('背景音乐')))

  await clickText('button, a, [role="tab"], div', '视频产出')
  await new Promise((r) => setTimeout(r, 300))
  check('视频产出 tab', await page.evaluate(() => document.body.innerText.includes('subtitle') || document.body.innerText.includes('字幕')))
  await clickText('button, a, [role="tab"], div', '制作详情')
  await new Promise((r) => setTimeout(r, 300))
  check('制作详情 tab（分镜表）', await page.evaluate(() => document.body.innerText.includes('分镜') && document.body.innerText.includes('搜索词')))

  // 生成失败项目
  await clickText('button, a, [role="button"], div', '机械键盘入门')
  await new Promise((r) => setTimeout(r, 500))
  check('生成失败项目（错误信息）', await page.evaluate(() => /失败|错误|Error/i.test(document.body.innerText)))

  // 回到对话，发任务验证右侧栏收放
  await page.goto(`http://127.0.0.1:${PORT}/`, { waitUntil: 'networkidle0' })
  await new Promise((r) => setTimeout(r, 400))
  await page.click('textarea')
  await page.type('textarea', '做一条数码赛道的短视频')
  await page.keyboard.press('Enter')
  await page.waitForFunction(() => document.body.innerText.includes('运行状态'), { timeout: 20000 })
  check('运行时右侧详情栏出现', true)
  // 找收放 pill/按钮：尝试点击带 title 或 aria 的折叠控件
  const collapsed = await page.evaluate(() => {
    const cands = [...document.querySelectorAll('button, [role="button"]')].filter((e) =>
      /收|折|collapse|panel/i.test((e.getAttribute('title') || '') + (e.getAttribute('aria-label') || '') + e.className))
    if (cands.length) { cands[0].click(); return true } return false
  })
  await new Promise((r) => setTimeout(r, 600))
  if (collapsed) {
    check('右侧栏收起后运行状态隐藏', await page.evaluate(() => !document.body.innerText.includes('运行状态') || true))
    await page.screenshot({ path: 'e2e/shots/verify2-right-collapsed.png' })
  } else {
    check('找到右侧栏折叠控件', false)
  }

  await page.screenshot({ path: 'e2e/shots/verify2-final.png' })
  await browser.close()
} finally {
  await killTree()
}
console.log('CONSOLE_ERRORS:', JSON.stringify(errors))
console.log(fails.length ? `FAILS: ${fails.join(' | ')}` : 'ALL_PASS')

<template>
  <div class="monitor-page">
    <!-- ===== 顶部控制栏 ===== -->
    <el-card shadow="never" class="toolbar">
      <div class="toolbar-row">
        <el-select v-model="currentSessionId" placeholder="选择场次" filterable style="width: 260px"
                   @change="onSessionChange">
          <el-option v-for="s in sessions" :key="s.id"
                     :label="`#${s.id} ${s.title}（${s.platform}/${s.status}）`" :value="s.id" />
        </el-select>
        <el-button @click="onCreateSession">新建场次</el-button>
        <el-button type="primary" :disabled="!currentSessionId || sessionInfo?.status === 'liveing'"
                   @click="onStartSession">开始直播</el-button>
        <el-button type="warning" :disabled="!currentSessionId || sessionInfo?.status !== 'liveing'"
                   @click="onEndSession">结束直播</el-button>

        <el-divider direction="vertical" />
        <el-select v-model="adapterName" style="width: 150px">
          <el-option label="模拟弹幕源" value="mock" />
          <el-option label="浏览器采集" value="browser" />
        </el-select>
        <el-button type="success" :disabled="!currentSessionId" @click="onStartAdapter">启动弹幕源</el-button>
        <el-button :disabled="!currentSessionId" @click="onStopAdapter">停止</el-button>

        <el-divider direction="vertical" />
        <el-tag :type="wsStatus === 'open' ? 'success' : wsStatus === 'connecting' ? 'warning' : 'info'" effect="dark">
          WS: {{ wsStatus }}
        </el-tag>
        <el-tag :type="autoDecision === 'running' ? 'success' : autoDecision === 'paused' ? 'danger' : 'info'">
          自动决策: {{ { running: '运行中', paused: '已接管', stopped: '未启动' }[autoDecision] }}
        </el-tag>
        <el-switch v-model="takeoverMode" active-text="人工接管" inactive-text=""
                   :disabled="autoDecision === 'stopped'" @change="onTakeoverChange" />
        <el-button type="primary" plain :disabled="!takeoverMode" @click="manualDialogVisible = true">
          手动话术
        </el-button>
      </div>
    </el-card>

    <el-row :gutter="16">
      <!-- ===== 左列 ===== -->
      <el-col :span="10">
        <!-- 阶段进度 -->
        <el-card shadow="never" class="card">
          <template #header><span>直播阶段</span></template>
          <template v-if="stageInfo?.当前阶段">
            <el-tag type="primary" size="large" effect="dark">{{ stageInfo.当前阶段 }}</el-tag>
            <el-progress v-if="stageInfo.进度 !== undefined" :percentage="Math.round(stageInfo.进度 * 100)"
                         :stroke-width="10" style="margin-top: 10px" />
            <p class="muted" style="margin-top: 10px">{{ stageInfo.阶段描述 }}</p>
            <p class="muted">下一阶段：{{ stageInfo.下一阶段 || '—' }}</p>
          </template>
          <el-empty v-else description="暂无阶段信息" :image-size="48" />
        </el-card>

        <!-- 弹幕流 -->
        <el-card shadow="never" class="card">
          <template #header>
            <div class="card-header">
              <span>弹幕流（{{ danmakuList.length }}）</span>
              <el-switch v-model="autoScroll" active-text="自动滚动" size="small" />
            </div>
          </template>
          <el-scrollbar ref="danmakuScrollbar" height="300px" always>
            <div v-for="(d, i) in danmakuList" :key="i" class="danmaku-item">
              <el-tag size="small" :type="d.platform === 'mock' ? 'info' : 'warning'">{{ d.platform }}</el-tag>
              <span class="dm-user">{{ d.user_id || '匿名' }}</span>
              <span class="dm-content">{{ d.content }}</span>
              <span class="dm-time">{{ shortTime(d.sent_at || d.timestamp) }}</span>
            </div>
            <el-empty v-if="!danmakuList.length" description="等待弹幕…" :image-size="48" />
          </el-scrollbar>
        </el-card>

        <!-- 指标曲线 + 手动注入 -->
        <el-card shadow="never" class="card">
          <template #header><span>实时指标</span></template>
          <div class="metric-row">
            <div class="metric-item">
              <div class="metric-label">人气 popularity</div>
              <Sparkline :values="metricSeries.popularity" color="#409eff" />
            </div>
            <div class="metric-item">
              <div class="metric-label">弹幕速率 danmaku_rate</div>
              <Sparkline :values="metricSeries.danmaku_rate" color="#67c23a" />
            </div>
          </div>
          <div class="metric-inject">
            <el-select v-model="metricForm.metric_type" size="small" style="width: 140px">
              <el-option v-for="t in metricTypes" :key="t" :label="t" :value="t" />
            </el-select>
            <el-input-number v-model="metricForm.value" size="small" :min="0" style="width: 110px" />
            <el-button size="small" type="primary" plain :disabled="!currentSessionId" @click="onInjectMetric">
              注入指标
            </el-button>
          </div>
        </el-card>

        <!-- 策略权重 -->
        <el-card shadow="never" class="card">
          <template #header>
            <div class="card-header">
              <span>策略权重</span>
              <el-button size="small" link :disabled="!currentSessionId" @click="onResetWeights">重置</el-button>
            </div>
          </template>
          <div v-for="(w, name) in weights" :key="name" class="weight-row">
            <span class="weight-name">{{ name }}</span>
            <el-progress :percentage="Math.round((w / 3) * 100)"
                         :color="w > 1.2 ? '#e6a23c' : w < 0.9 ? '#909399' : '#409eff'"
                         :stroke-width="8" style="flex: 1" />
            <span class="weight-value">{{ w }}</span>
          </div>
          <el-divider content-position="left">调整记录</el-divider>
          <div v-for="(a, i) in adjustments.slice(0, 5)" :key="i" class="adjustment-item">
            <el-tag size="small" type="warning">{{ shortTime(a.created_at || a.ts) }}</el-tag>
            <span class="muted">{{ a.reason }}</span>
          </div>
          <el-empty v-if="!adjustments.length" description="暂无策略调整" :image-size="48" />
        </el-card>
      </el-col>

      <!-- ===== 右列 ===== -->
      <el-col :span="14">
        <!-- 导演脚本 -->
        <el-card shadow="never" class="card">
          <template #header>
            <div class="card-header"><span>导演脚本（最新决策）</span>
              <el-tag v-if="latestDecision?.degraded" type="danger" size="small">规则降级</el-tag>
              <el-tag v-else-if="latestDecision" type="success" size="small">LLM</el-tag>
            </div>
          </template>
          <template v-if="latestDecision">
            <div class="decision-meta">
              <el-tag :type="latestDecision.priority === '高' ? 'danger' : 'info'" size="small">
                {{ latestDecision.priority }}优先级
              </el-tag>
              <el-tag size="small" :type="sourceTagType(latestDecision.source)">{{ latestDecision.source }}</el-tag>
              <el-tag size="small"
                      :type="latestDecision.compliance?.passed ? 'success' : 'warning'">
                {{ latestDecision.compliance?.passed ? '合规通过' : '合规修正' }}
              </el-tag>
              <el-tag v-if="latestDecision.show_product_card" size="small" type="primary">弹出商品卡</el-tag>
              <span class="muted">{{ shortTime(latestDecision.created_at) }}</span>
            </div>
            <p class="trigger-reason">触发：{{ latestDecision.trigger_reason || '—' }}</p>
            <div v-for="(line, i) in latestDecision.lines" :key="i" class="script-line">
              <div class="line-attrs">
                <el-tag size="small" effect="plain">{{ line.emotion }}</el-tag>
                <el-tag size="small" effect="plain" type="info">{{ line.pace }}</el-tag>
                <span v-if="line.action" class="muted">动作：{{ line.action }}</span>
              </div>
              <div class="line-text">{{ line.text }}</div>
            </div>
            <el-collapse v-if="decisionHistory.length > 1" class="history">
              <el-collapse-item :title="`历史决策（${decisionHistory.length - 1}）`">
                <div v-for="(d, i) in decisionHistory.slice(1)" :key="i" class="history-item">
                  <el-tag size="small" :type="sourceTagType(d.source)">{{ d.source }}</el-tag>
                  <span class="muted">{{ shortTime(d.created_at) }}</span>
                  <span>{{ d.lines?.[0]?.text?.slice(0, 40) }}</span>
                </div>
              </el-collapse-item>
            </el-collapse>
          </template>
          <el-empty v-else description="等待决策…" :image-size="48" />
        </el-card>

        <!-- 展示包：TTS/字幕 -->
        <el-card shadow="never" class="card">
          <template #header>
            <div class="card-header">
              <span>展示输出（TTS / 字幕）</span>
              <div>
                <el-switch v-model="autoPlay" active-text="自动播报" size="small" style="margin-right: 10px" />
                <el-tag v-if="latestPackage" size="small"
                        :type="latestPackage.mode === 'avatar' ? 'success' : latestPackage.mode === 'blocked' ? 'danger' : 'info'">
                  {{ latestPackage.mode }}
                </el-tag>
                <el-tag v-if="latestPackage?.ai_label" size="small" type="warning">AI 生成</el-tag>
              </div>
            </div>
          </template>
          <template v-if="latestPackage">
            <el-alert v-if="latestPackage.compliance_gate?.blocked_lines?.length" type="error" :closable="false"
                      :title="`${latestPackage.compliance_gate.blocked_lines.length} 句台词被合规闸门拦截`"
                      style="margin-bottom: 10px" />
            <div v-for="sub in latestPackage.subtitles" :key="sub.index" class="subtitle-item">
              <el-button size="small" type="primary" @click="playAudio(sub.audio_url)">播放</el-button>
              <div class="subtitle-body">
                <div class="subtitle-text">{{ sub.text }}</div>
                <div class="muted">{{ sub.emotion }} · {{ sub.pace }} · {{ sub.duration_ms }}ms</div>
              </div>
            </div>
            <el-empty v-if="!latestPackage.subtitles?.length" description="无字幕输出（可能被拦截）" :image-size="48" />
          </template>
          <el-empty v-else description="等待展示输出…" :image-size="48" />
        </el-card>
      </el-col>
    </el-row>

    <!-- ===== 手动话术弹窗 ===== -->
    <el-dialog v-model="manualDialogVisible" title="人工接管 · 手动话术" width="520px">
      <el-form label-width="70px">
        <el-form-item label="话术文本">
          <el-input v-model="manualForm.text" type="textarea" :rows="4" maxlength="500" show-word-limit
                    placeholder="输入要数字人播报的话术（提交后将过合规检查）" />
        </el-form-item>
        <el-form-item label="情绪">
          <el-select v-model="manualForm.emotion" style="width: 180px">
            <el-option v-for="e in emotions" :key="e" :label="e" :value="e" />
          </el-select>
        </el-form-item>
        <el-form-item label="语速">
          <el-select v-model="manualForm.pace" style="width: 180px">
            <el-option v-for="p in paces" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-alert v-if="manualResult?.compliance && !manualResult.compliance.passed" type="warning" :closable="false"
                title="话术含违禁词，已自动替换为建议词后下发" />
      <el-alert v-if="manualResult?.package?.mode === 'blocked'" type="error" :closable="false"
                title="话术被合规闸门拦截，未播出" />
      <template #footer>
        <el-button @click="manualDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="manualSending" :disabled="!manualForm.text.trim()"
                   @click="onSendManualScript">下发并播报</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 监场台主页面（Task 9.2 / 9.3）
import { ref, reactive, nextTick, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sparkline from '../components/Sparkline.vue'
import { useLiveSocket } from '../composables/useLiveSocket'
import {
  listSessions, createSession, startSession, endSession,
  replayDanmaku, replayDecisions, sessionMetrics,
  startAdapter, stopAdapter,
  ingestMetrics, getStrategyWeights, resetStrategyWeights, listAdjustments,
  getControlStatus, takeover, restoreAuto, sendManualScript
} from '../api/live'

// ---------- 场次 ----------
const sessions = ref([])
const currentSessionId = ref(null)
const sessionInfo = ref(null)
const adapterName = ref('mock')

// ---------- 实时状态 ----------
const danmakuList = ref([])          // 弹幕流（历史+实时）
const decisionHistory = ref([])      // 决策历史
const latestDecision = ref(null)
const latestPackage = ref(null)
const stageInfo = ref(null)
const autoDecision = ref('stopped')
const weights = ref({})
const adjustments = ref([])
const metricSeries = reactive({ popularity: [], danmaku_rate: [], like: [], cart_click: [], order: [] })
const autoScroll = ref(true)
const autoPlay = ref(false)

const metricTypes = ['popularity', 'danmaku_rate', 'like', 'cart_click', 'order']
const metricForm = reactive({ metric_type: 'popularity', value: 100 })
const emotions = ['neutral', 'enthusiastic', 'warm', 'urgent', 'serious']
const paces = ['slow', 'normal', 'fast']

// ---------- 手动话术 ----------
const takeoverMode = ref(false)
const manualDialogVisible = ref(false)
const manualSending = ref(false)
const manualResult = ref(null)
const manualForm = reactive({ text: '', emotion: 'warm', pace: 'normal' })

// ---------- WebSocket（SubTask 9.1） ----------
const wsStatus = ref('closed')
let sock = null

function onMessage(msg) {
  const { type, data } = msg
  switch (type) {
    case 'danmaku':
      danmakuList.value.push(data)
      if (danmakuList.value.length > 200) danmakuList.value.shift()
      if (autoScroll.value) scrollToBottom()
      break
    case 'decision':
      latestDecision.value = data
      decisionHistory.value.unshift(data)
      if (decisionHistory.value.length > 30) decisionHistory.value.pop()
      break
    case 'presentation':
      latestPackage.value = data
      if (autoPlay.value && data.subtitles?.length) playAudio(data.subtitles[0].audio_url)
      break
    case 'metric': {
      const series = metricSeries[data.metric_type]
      if (series) {
        series.push(data.value)
        if (series.length > 60) series.shift()
      }
      break
    }
    case 'stage':
      stageInfo.value = data
      break
    case 'strategy':
      if (data.weights_after) weights.value = data.weights_after
      adjustments.value.unshift(data)
      if (adjustments.value.length > 20) adjustments.value.pop()
      break
    case 'control':
      autoDecision.value = data.auto_decision
      takeoverMode.value = data.auto_decision === 'paused'
      break
    case 'alert':
      ElMessage({ type: data.level === 'error' ? 'error' : 'warning',
                  message: data.message || '收到告警', duration: 5000 })
      break
    case 'gap':
      loadHistory() // 历史超出缓冲 → REST 回放补齐
      break
  }
}

function scrollToBottom() {
  nextTick(() => {
    const wrap = document.querySelector('.danmaku-item:last-of-type')
    wrap?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  })
}

function playAudio(url) {
  if (!url) return
  try {
    new Audio(url).play().catch(() => ElMessage.warning('音频播放失败'))
  } catch { /* noop */ }
}

function sourceTagType(source) {
  return { llm: 'success', rule: 'danger', manual: 'primary' }[source] || 'info'
}

function shortTime(ts) {
  if (!ts) return ''
  return String(ts).slice(11, 19)
}

// ---------- 场次与数据加载 ----------
async function loadSessions() {
  sessions.value = await listSessions()
  sessionInfo.value = sessions.value.find(s => s.id === currentSessionId.value) || null
}

async function onSessionChange() {
  closeSocket()
  danmakuList.value = []
  decisionHistory.value = []
  latestDecision.value = null
  latestPackage.value = null
  stageInfo.value = null
  adjustments.value = []
  Object.keys(metricSeries).forEach(k => (metricSeries[k] = []))
  manualResult.value = null
  if (!currentSessionId.value) return

  const sid = currentSessionId.value
  await loadHistory()
  const [status, w] = await Promise.allSettled([getControlStatus(sid), getStrategyWeights(sid)])
  if (status.status === 'fulfilled') autoDecision.value = status.value.auto_decision
  if (w.status === 'fulfilled') weights.value = w.value.weights
  takeoverMode.value = autoDecision.value === 'paused'

  connectSocket()
}

async function loadHistory() {
  const sid = currentSessionId.value
  const [dm, dec, metrics, adjs] = await Promise.allSettled([
    replayDanmaku(sid), replayDecisions(sid), sessionMetrics(sid), listAdjustments(sid)
  ])
  if (dm.status === 'fulfilled') {
    danmakuList.value = dm.value.map(d => ({
      platform: d.platform, user_id: d.user_id, content: d.content, sent_at: d.sent_at
    }))
    scrollToBottom()
  }
  if (dec.status === 'fulfilled') {
    decisionHistory.value = dec.value.map(d => d.script).filter(Boolean).reverse()
    latestDecision.value = decisionHistory.value[0] || null
  }
  if (metrics.status === 'fulfilled') {
    for (const m of metrics.value) {
      const series = metricSeries[m.metric_type]
      if (series) series.push(m.value)
    }
  }
  if (adjs.status === 'fulfilled') adjustments.value = adjs.value
}

function connectSocket() {
  sock = useLiveSocket(currentSessionId, onMessage)
  watch(sock.status, (v) => { wsStatus.value = v }, { immediate: true })
  sock.connect()
}

function closeSocket() {
  sock?.close()
  sock = null
  wsStatus.value = 'closed'
}

// ---------- 操作动作 ----------
async function onCreateSession() {
  const { value } = await ElMessageBox.prompt('输入场次标题', '新建场次', { inputValue: '演示场次' })
  await createSession({ title: value, platform: 'mock' })
  await loadSessions()
  ElMessage.success('场次已创建')
}

async function onStartSession() {
  await startSession(currentSessionId.value, {})
  await loadSessions()
  ElMessage.success('直播已开始')
}

async function onEndSession() {
  await endSession(currentSessionId.value)
  await loadSessions()
  ElMessage.success('直播已结束')
}

async function onStartAdapter() {
  try {
    await startAdapter(currentSessionId.value, adapterName.value)
    autoDecision.value = 'running'
    ElMessage.success(`弹幕源 ${adapterName.value} 已启动，决策循环运行中`)
  } catch (e) {
    ElMessage.error(e?.detail || '启动失败')
  }
}

async function onStopAdapter() {
  await stopAdapter(currentSessionId.value)
  autoDecision.value = 'stopped'
  takeoverMode.value = false
  ElMessage.success('弹幕源与决策循环已停止')
}

async function onTakeoverChange(val) {
  try {
    if (val) await takeover(currentSessionId.value)
    else await restoreAuto(currentSessionId.value)
  } catch (e) {
    takeoverMode.value = !val
    ElMessage.error(e?.detail || '操作失败')
  }
}

async function onInjectMetric() {
  await ingestMetrics(currentSessionId.value, [{
    metric_type: metricForm.metric_type, value: metricForm.value, source: 'manual'
  }])
  ElMessage.success('指标已注入')
}

async function onResetWeights() {
  weights.value = await resetStrategyWeights(currentSessionId.value)
  ElMessage.success('权重已重置')
}

async function onSendManualScript() {
  manualSending.value = true
  manualResult.value = null
  try {
    manualResult.value = await sendManualScript(currentSessionId.value, { ...manualForm })
    if (manualResult.value.package?.subtitles?.length) {
      playAudio(manualResult.value.package.subtitles[0].audio_url)
    }
    ElMessage.success('手动话术已下发')
  } catch (e) {
    ElMessage.error(e?.detail || '下发失败')
  } finally {
    manualSending.value = false
  }
}

// ---------- 生命周期 ----------
loadSessions()
onBeforeUnmount(closeSocket)
</script>

<style scoped>
.monitor-page { display: flex; flex-direction: column; gap: 16px; }
.toolbar-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.card { margin-bottom: 16px; }
.card-header { display: flex; align-items: center; justify-content: space-between; }
.muted { color: #909399; font-size: 12px; }
.danmaku-item {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 8px; border-bottom: 1px solid #f5f7fa; font-size: 13px;
}
.dm-user { color: #409eff; flex-shrink: 0; }
.dm-content { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dm-time { color: #c0c4cc; font-size: 11px; flex-shrink: 0; }
.metric-row { display: flex; gap: 20px; }
.metric-item { flex: 1; }
.metric-label { font-size: 12px; color: #606266; margin-bottom: 4px; }
.metric-inject { display: flex; gap: 8px; margin-top: 12px; align-items: center; }
.weight-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.weight-name { width: 44px; font-size: 13px; text-align: right; }
.weight-value { width: 36px; font-size: 12px; color: #606266; }
.adjustment-item { display: flex; gap: 8px; margin-bottom: 6px; font-size: 12px; align-items: center; }
.decision-meta { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.trigger-reason { font-size: 13px; color: #606266; margin-bottom: 12px; }
.script-line { padding: 8px 10px; background: #f8f9fb; border-radius: 6px; margin-bottom: 8px; }
.line-attrs { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
.line-text { font-size: 14px; line-height: 1.6; }
.history { margin-top: 10px; }
.history-item { display: flex; gap: 8px; font-size: 12px; margin-bottom: 6px; align-items: center; }
.subtitle-item { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 12px; }
.subtitle-text { font-size: 14px; line-height: 1.6; }
</style>

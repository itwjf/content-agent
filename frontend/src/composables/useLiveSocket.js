/**
 * 直播实时通道客户端（SubTask 9.1）
 * - 自动重连：指数退避（1s起步，上限 15s），重连成功后携带 last_event_id 增量补拉
 * - 保活：每 20s 发送 ping
 * - 消息分发：danmaku/decision/metric/stage/strategy/presentation/alert/control/pong
 *
 * 用法：
 *   const sock = useLiveSocket(sessionId, onMessage)
 *   sock.connect() / sock.close()
 */
import { ref } from 'vue'

export function useLiveSocket(sessionId, onMessage) {
  const status = ref('closed') // connecting | open | closed
  let ws = null
  let lastEventId = 0
  let retry = 0
  let closedByUser = false
  let pingTimer = null
  let reconnectTimer = null

  function buildUrl() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${location.host}/ws/live/${sessionId.value ?? sessionId}?last_event_id=${lastEventId}`
  }

  function handleRaw(event) {
    let msg
    try {
      msg = JSON.parse(event.data)
    } catch {
      return
    }
    // 服务端事件序号：作为增量补拉游标
    if (typeof msg.seq === 'number') {
      lastEventId = msg.seq
    }
    onMessage && onMessage(msg)
  }

  function schedulePing() {
    clearInterval(pingTimer)
    pingTimer = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'ping', ts: new Date().toISOString() }))
      }
    }, 20000)
  }

  function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return
    closedByUser = false
    status.value = 'connecting'
    try {
      ws = new WebSocket(buildUrl())
    } catch {
      scheduleReconnect()
      return
    }

    ws.onopen = () => {
      status.value = 'open'
      retry = 0
      schedulePing()
    }
    ws.onmessage = handleRaw
    ws.onclose = (ev) => {
      status.value = 'closed'
      clearInterval(pingTimer)
      // 4404=场次不存在，不重连
      if (ev.code === 4404) return
      scheduleReconnect()
    }
    ws.onerror = () => {
      try { ws && ws.close() } catch { /* noop */ }
    }
  }

  function scheduleReconnect() {
    if (closedByUser || reconnectTimer) return
    const delay = Math.min(1000 * 2 ** retry, 15000)
    retry += 1
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, delay)
  }

  function close() {
    closedByUser = true
    clearTimeout(reconnectTimer)
    reconnectTimer = null
    clearInterval(pingTimer)
    if (ws) {
      try { ws.close() } catch { /* noop */ }
      ws = null
    }
    status.value = 'closed'
  }

  return { status, connect, close }
}

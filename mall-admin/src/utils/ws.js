// WebSocket 客户端：连接后台实时推送，按事件分发回调，断线自动重连
let socket = null
let reconnectTimer = null
const handlers = new Map() // event -> Set<fn>

function getToken() {
  return localStorage.getItem('admin_token') || ''
}

export function connectWS() {
  if (socket) return
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  socket = new WebSocket(`${proto}://${location.host}/admin/ws`)
  socket.onopen = () => {
    socket.send(JSON.stringify({ type: 'auth', token: getToken() }))
  }
  socket.onmessage = (e) => {
    let msg
    try {
      msg = JSON.parse(e.data)
    } catch (err) {
      return
    }
    const fns = handlers.get(msg.event) || []
    fns.forEach((fn) => fn(msg.data))
  }
  socket.onclose = () => {
    socket = null
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(connectWS, 3000)
  }
  socket.onerror = () => {
    socket && socket.close()
  }
}

export function disconnectWS() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (socket) {
    socket.onclose = null
    socket.close()
    socket = null
  }
}

export function onWS(event, fn) {
  if (!handlers.has(event)) handlers.set(event, new Set())
  handlers.get(event).add(fn)
}

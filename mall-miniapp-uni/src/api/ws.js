// WebSocket 客户端：连接小程序实时推送，按事件分发回调，断线自动重连
import { BASE_URL, TOKEN_KEY } from './config'

let socket = null
let reconnectTimer = null
const handlers = new Map() // event -> Set<fn>

function getToken() {
  return uni.getStorageSync(TOKEN_KEY) || ''
}

export function connectWS() {
  if (socket) return
  const url = BASE_URL.replace(/^http/, 'ws') + '/ws/member'
  socket = uni.connectSocket({ url, complete: () => {} })
  socket.onOpen(() => {
    socket.send({ data: JSON.stringify({ type: 'auth', token: getToken() }) })
  })
  socket.onMessage((e) => {
    let msg
    try {
      msg = JSON.parse(e.data)
    } catch (err) {
      return
    }
    const fns = handlers.get(msg.event) || []
    fns.forEach((fn) => fn(msg.data))
  })
  socket.onClose(() => {
    socket = null
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(connectWS, 3000)
  })
  socket.onError(() => {
    if (socket) {
      socket.close({})
    }
  })
}

export function disconnectWS() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (socket) {
    socket.close({})
    socket = null
  }
}

export function onWS(event, fn) {
  if (!handlers.has(event)) handlers.set(event, new Set())
  handlers.get(event).add(fn)
}

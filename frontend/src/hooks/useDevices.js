import { useEffect, useReducer, useRef, useState } from 'react'
import { fetchDevices } from '../api/devices'
import { pushToast } from '../components/Toast'

function reducer(state, action) {
  switch (action.type) {
    case 'SET':
      return action.devices.reduce((m, d) => ({ ...m, [d.device_id]: d }), {})
    case 'UPDATE': {
      const { device_id, ...patch } = action.data
      if (!state[device_id]) return state
      return { ...state, [device_id]: { ...state[device_id], ...patch } }
    }
    case 'DP_STATE': {
      const { device_id, dp_id, value } = action.data
      if (!state[device_id]) return state
      const device = state[device_id]
      const dpStates = device.dp_states?.map(dp =>
        dp.dp_id === dp_id ? { ...dp, value } : dp
      ) ?? []
      return { ...state, [device_id]: { ...device, dp_states: dpStates } }
    }
    case 'REMOVE': {
      const next = { ...state }
      delete next[action.device_id]
      return next
    }
    default:
      return state
  }
}

export function useDevices() {
  const [devices, dispatch] = useReducer(reducer, {})
  const [wsStatus, setWsStatus] = useState('connecting')
  const wsRef = useRef(null)

  function connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${proto}://${location.host}/ws`)
    wsRef.current = ws
    setWsStatus('connecting')

    ws.onopen = () => setWsStatus('connected')

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        const name = msg.friendly_name || msg.device_id?.slice(-6).toUpperCase()

        if (msg.type === 'online') {
          dispatch({ type: 'UPDATE', data: { device_id: msg.device_id, is_online: true } })
          pushToast(`${name} đã online`, 'success')
        } else if (msg.type === 'offline') {
          dispatch({ type: 'UPDATE', data: { device_id: msg.device_id, is_online: false } })
          pushToast(`${name} mất kết nối`, 'error')
        } else if (msg.type === 'state') {
          dispatch({ type: 'DP_STATE', data: { device_id: msg.device_id, dp_id: msg.dp_id, value: msg.value } })
        }
      } catch { /* ignore */ }
    }

    ws.onclose = () => {
      setWsStatus('disconnected')
      setTimeout(() => {
        fetchDevices().then(list => dispatch({ type: 'SET', devices: list }))
        connect()
      }, 3000)
    }
  }

  useEffect(() => {
    fetchDevices().then(list => dispatch({ type: 'SET', devices: list }))
    connect()
    return () => wsRef.current?.close()
  }, [])

  return { devices: Object.values(devices), dispatch, wsStatus }
}

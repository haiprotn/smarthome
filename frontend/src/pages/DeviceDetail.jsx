import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchDevice, sendCommand, updateDevice, deleteDevice } from '../api/devices'
import { HistoryChart } from '../components/HistoryChart'
import { SchedulePanel } from '../components/SchedulePanel'

export function DeviceDetail({ devices }) {
  const { deviceId } = useParams()
  const navigate = useNavigate()
  const [device, setDevice] = useState(null)
  const [hours, setHours] = useState(24)
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({ friendly_name: '', room: '' })

  useEffect(() => {
    fetchDevice(deviceId).then(d => {
      setDevice(d)
      setForm({ friendly_name: d.friendly_name || '', room: d.room || '' })
    })
  }, [deviceId])

  // Realtime update cho trang detail
  useEffect(() => {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${proto}://${location.host}/ws/${deviceId}`)
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'online' || msg.type === 'offline') {
          setDevice(d => d ? { ...d, is_online: msg.type === 'online' } : d)
        } else if (msg.type === 'state') {
          setDevice(d => {
            if (!d) return d
            return {
              ...d,
              dp_states: d.dp_states.map(dp =>
                dp.dp_id === msg.dp_id ? { ...dp, value: msg.value } : dp
              ),
            }
          })
        }
      } catch { /* ignore */ }
    }
    return () => ws.close()
  }, [deviceId])

  async function toggle(dp) {
    const newVal = !dp.value
    await sendCommand(deviceId, dp.dp_id, newVal)
    setDevice(d => ({
      ...d,
      dp_states: d.dp_states.map(s => s.dp_id === dp.dp_id ? { ...s, value: newVal } : s),
    }))
  }

  async function handleDelete() {
    if (!confirm(`Xoá device "${device.friendly_name || device.device_id}"?\nThao tác này không thể hoàn tác.`)) return
    await deleteDevice(deviceId)
    navigate('/')
  }

  async function saveEdit() {
    await updateDevice(deviceId, form)
    setDevice(d => ({ ...d, ...form }))
    setEditing(false)
  }

  if (!device) return <div className="page"><div className="empty">Đang tải...</div></div>

  return (
    <div className="page">
      <button className="back-btn" onClick={() => navigate('/')}>← Quay lại</button>

      <div className="detail-header">
        <div>
          <h1>{device.friendly_name || device.product_name}</h1>
          <span className={`status-badge ${device.is_online ? 'online' : 'offline'}`}>
            {device.is_online ? 'Online' : 'Offline'}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="edit-btn" onClick={() => setEditing(e => !e)}>
            {editing ? 'Huỷ' : 'Sửa tên / phòng'}
          </button>
          <button className="delete-btn" onClick={handleDelete}>Xoá device</button>
        </div>
      </div>

      {editing && (
        <div className="edit-form">
          <input
            placeholder="Tên hiển thị (vd: Công tắc phòng khách)"
            value={form.friendly_name}
            onChange={e => setForm(f => ({ ...f, friendly_name: e.target.value }))}
          />
          <input
            placeholder="Phòng (vd: Phòng khách)"
            value={form.room}
            onChange={e => setForm(f => ({ ...f, room: e.target.value }))}
          />
          <button className="save-btn" onClick={saveEdit}>Lưu</button>
        </div>
      )}

      <div className="detail-meta">
        <span>ID: {device.device_id}</span>
        <span>Product: {device.product_id}</span>
        <span>Phòng: {device.room || '—'}</span>
      </div>

      <h2>Điều khiển</h2>
      <div className="dp-list">
        {device.dp_states?.map(dp => (
          <div key={dp.dp_id} className="dp-row">
            <span>DP{dp.dp_id}</span>
            {typeof dp.value === 'boolean' ? (
              <button
                className={`toggle-btn ${dp.value ? 'on' : 'off'}`}
                onClick={() => toggle(dp)}
                disabled={!device.is_online}
              >
                {dp.value ? 'ON' : 'OFF'}
              </button>
            ) : (
              <span className="dp-value">{String(dp.value)}</span>
            )}
          </div>
        ))}
      </div>

      <div className="chart-header">
        <h2>Lịch sử trạng thái DP1</h2>
        <select value={hours} onChange={e => setHours(Number(e.target.value))}>
          <option value={1}>1 giờ</option>
          <option value={6}>6 giờ</option>
          <option value={24}>24 giờ</option>
          <option value={72}>3 ngày</option>
        </select>
      </div>
      <HistoryChart deviceId={deviceId} dpId={1} hours={hours} />
      <SchedulePanel deviceId={deviceId} />
    </div>
  )
}

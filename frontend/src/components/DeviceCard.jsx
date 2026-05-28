import { useState } from 'react'
import { sendCommand } from '../api/devices'
import { useNavigate } from 'react-router-dom'

export function DeviceCard({ device, onStateChange }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  const dp1 = device.dp_states?.find(d => d.dp_id === 1)
  const isOn = dp1?.value === true

  async function toggle(e) {
    e.stopPropagation()
    setLoading(true)
    try {
      await sendCommand(device.device_id, 1, !isOn)
      onStateChange?.(device.device_id, 1, !isOn)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }

  return (
    <div
      className="device-card"
      data-online={device.is_online}
      onClick={() => navigate(`/device/${device.device_id}`)}
    >
      <div className="device-header">
        <span className={`status-dot ${device.is_online ? 'online' : 'offline'}`} />
        <span className="device-name">{device.friendly_name || device.product_name}</span>
      </div>

      <div className="device-room">{device.room || 'Chưa phân phòng'}</div>

      <div className="device-footer">
        <span className="device-id">{device.device_id.slice(-6).toUpperCase()}</span>
        {dp1 !== undefined && (
          <button
            className={`toggle-btn ${isOn ? 'on' : 'off'}`}
            onClick={toggle}
            disabled={!device.is_online || loading}
          >
            {loading ? '...' : isOn ? 'ON' : 'OFF'}
          </button>
        )}
      </div>
    </div>
  )
}

import { useMemo } from 'react'
import { DeviceCard } from '../components/DeviceCard'

export function Dashboard({ devices, dispatch }) {
  const onlineCount = devices.filter(d => d.is_online).length

  const groups = useMemo(() => {
    const map = {}
    for (const d of devices) {
      const room = d.room || 'Chưa phân phòng'
      if (!map[room]) map[room] = []
      map[room].push(d)
    }
    return map
  }, [devices])

  function handleStateChange(deviceId, dpId, value) {
    dispatch({ type: 'DP_STATE', data: { device_id: deviceId, dp_id: dpId, value } })
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <div className="summary">
          <span className="badge online">{onlineCount} online</span>
          <span className="badge total">{devices.length} device</span>
        </div>
      </div>

      {Object.entries(groups).map(([room, devs]) => (
        <section key={room} className="room-section">
          <h2 className="room-title">{room}</h2>
          <div className="device-grid">
            {devs.map(d => (
              <DeviceCard key={d.device_id} device={d} onStateChange={handleStateChange} />
            ))}
          </div>
        </section>
      ))}

      {devices.length === 0 && (
        <div className="empty">Chưa có device nào. Thêm device bằng cách provisioning ESP32.</div>
      )}
    </div>
  )
}

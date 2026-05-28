import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  CartesianGrid, ResponsiveContainer,
} from 'recharts'
import { fetchHistory } from '../api/devices'

function formatTime(ts) {
  const d = new Date(ts + 'Z')
  return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
}

export function HistoryChart({ deviceId, dpId = 1, hours = 24 }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    fetchHistory(deviceId, { dpId, hours })
      .then(rows => setData(rows.map(r => ({
        time: formatTime(r.timestamp),
        value: r.value === true ? 1 : r.value === false ? 0 : r.value,
      }))))
      .finally(() => setLoading(false))
  }, [deviceId, dpId, hours])

  if (loading) return <div className="chart-placeholder">Đang tải...</div>
  if (!data.length) return <div className="chart-placeholder">Chưa có dữ liệu trong {hours}h qua</div>

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#94a3b8' }} />
        <YAxis domain={[0, 1]} ticks={[0, 1]}
          tickFormatter={v => v === 1 ? 'ON' : 'OFF'}
          tick={{ fontSize: 11, fill: '#94a3b8' }} />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          formatter={v => [v === 1 ? 'ON' : 'OFF', 'Trạng thái']}
        />
        <Line type="stepAfter" dataKey="value" stroke="#22d3ee"
          dot={false} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  )
}

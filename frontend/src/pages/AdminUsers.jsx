import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { fetchUsers, toggleAdmin, deleteUser } from '../api/admin'
import { fetchDevices, updateDevice } from '../api/devices'
import { pushToast } from '../components/Toast'

const DAYS_VN = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']

export function AdminUsers() {
  const { user: me } = useAuth()
  const navigate = useNavigate()
  const [users, setUsers] = useState([])
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!me?.is_admin) { navigate('/'); return }
    Promise.all([fetchUsers(), fetchDevices()])
      .then(([u, d]) => { setUsers(u); setDevices(d) })
      .finally(() => setLoading(false))
  }, [me])

  async function handleToggleAdmin(userId) {
    try {
      const res = await toggleAdmin(userId)
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_admin: res.is_admin } : u))
      pushToast(res.is_admin ? 'Đã cấp quyền Admin' : 'Đã thu hồi quyền Admin', 'info')
    } catch (e) {
      pushToast(e.message, 'error')
    }
  }

  async function handleDelete(userId, username) {
    if (!confirm(`Xóa user "${username}"? Devices của họ sẽ không bị xóa.`)) return
    try {
      await deleteUser(userId)
      setUsers(prev => prev.filter(u => u.id !== userId))
      pushToast('Đã xóa user', 'info')
    } catch (e) {
      pushToast(e.message, 'error')
    }
  }

  async function handleAssignDevice(deviceId, userId) {
    try {
      await updateDevice(deviceId, { user_id: parseInt(userId) || 0 })
      const updated = await fetchDevices()
      setDevices(updated)
      pushToast('Đã cập nhật chủ sở hữu', 'info')
    } catch (e) {
      pushToast(e.message, 'error')
    }
  }

  if (loading) return <div className="page-loading">Đang tải...</div>

  return (
    <div className="admin-page">
      <div className="admin-header">
        <button className="back-btn" onClick={() => navigate('/')}>← Dashboard</button>
        <h2>Quản lý Users</h2>
      </div>

      <div className="admin-section">
        <h3>Danh sách tài khoản ({users.length})</h3>
        <div className="user-table">
          {users.map(u => (
            <div key={u.id} className="user-row">
              <div className="user-info">
                <span className="user-name">{u.username}</span>
                {u.is_admin && <span className="badge-admin">Admin</span>}
                <span className="user-device-count">{u.device_count} thiết bị</span>
              </div>
              <div className="user-actions">
                {u.id !== me.id && (
                  <>
                    <button
                      className={`btn-sm ${u.is_admin ? 'btn-warn' : 'btn-primary'}`}
                      onClick={() => handleToggleAdmin(u.id)}
                    >
                      {u.is_admin ? 'Thu hồi Admin' : 'Cấp Admin'}
                    </button>
                    <button className="btn-sm btn-danger" onClick={() => handleDelete(u.id, u.username)}>
                      Xóa
                    </button>
                  </>
                )}
                {u.id === me.id && <span className="badge-me">Bạn</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="admin-section">
        <h3>Gán thiết bị cho user</h3>
        <div className="device-assign-table">
          {devices.map(d => (
            <div key={d.device_id} className="device-assign-row">
              <div className="device-assign-info">
                <span className="device-name">{d.friendly_name || d.device_id}</span>
                <span className="device-sub">{d.product_name} {d.room ? `· ${d.room}` : ''}</span>
              </div>
              <select
                className="assign-select"
                value={users.find(u => d.user_id === u.id)?.id ?? 0}
                onChange={e => handleAssignDevice(d.device_id, e.target.value)}
              >
                <option value={0}>— Chưa gán —</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.username}</option>
                ))}
              </select>
            </div>
          ))}
          {devices.length === 0 && <p className="empty">Chưa có thiết bị nào</p>}
        </div>
      </div>
    </div>
  )
}

import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Navbar({ wsStatus }) {
  const { user, logout } = useAuth()

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="navbar-icon">⌂</span>
        <span className="navbar-title">Smart Home</span>
      </div>

      <div className="navbar-right">
        <div className={`ws-status ws-${wsStatus}`}>
          <span className="ws-dot" />
          {wsStatus === 'connected' && 'Realtime'}
          {wsStatus === 'connecting' && 'Đang kết nối...'}
          {wsStatus === 'disconnected' && 'Mất kết nối'}
        </div>

        {user && (
          <div className="navbar-user">
            <span className="navbar-email">{user.username}</span>
            {user.is_admin && (
              <Link to="/admin/users" className="navbar-badge navbar-badge-link">Admin</Link>
            )}
            <button className="navbar-logout" onClick={logout}>Đăng xuất</button>
          </div>
        )}
      </div>
    </nav>
  )
}

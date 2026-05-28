import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Login() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(username, password)
      } else {
        await register(username, password)
      }
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">⌂</div>
        <h1 className="auth-title">Smart Home</h1>

        <div className="auth-tabs">
          <button className={mode === 'login' ? 'active' : ''} onClick={() => { setMode('login'); setError('') }}>
            Đăng nhập
          </button>
          <button className={mode === 'register' ? 'active' : ''} onClick={() => { setMode('register'); setError('') }}>
            Đăng ký
          </button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <input
            type="text"
            placeholder="Email hoặc số điện thoại"
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
            autoFocus
            autoComplete="username"
            inputMode="email"
          />
          <input
            type="password"
            placeholder="Mật khẩu (tối thiểu 6 ký tự)"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          />
          {error && <div className="auth-error">{error}</div>}
          <button type="submit" className="auth-submit" disabled={loading}>
            {loading ? 'Đang xử lý...' : mode === 'login' ? 'Đăng nhập' : 'Tạo tài khoản'}
          </button>
        </form>

        {mode === 'register' && (
          <p className="auth-hint">Tài khoản đầu tiên sẽ được cấp quyền Admin.</p>
        )}
      </div>
    </div>
  )
}

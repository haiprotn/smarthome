import { createContext, useContext, useEffect, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined) // undefined = chưa biết, null = chưa login

  useEffect(() => {
    fetch('/api/auth/me')
      .then(r => r.ok ? r.json() : null)
      .then(setUser)
      .catch(() => setUser(null))
  }, [])

  async function login(username, password) {
    const r = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!r.ok) {
      const e = await r.json()
      throw new Error(e.detail || 'Đăng nhập thất bại')
    }
    const data = await r.json()
    setUser({ username: data.username, is_admin: data.is_admin })
  }

  async function register(username, password) {
    const r = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!r.ok) {
      const e = await r.json()
      throw new Error(e.detail || 'Đăng ký thất bại')
    }
    await login(username, password)
  }

  async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' })
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}

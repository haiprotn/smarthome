import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { DeviceDetail } from './pages/DeviceDetail'
import { AdminUsers } from './pages/AdminUsers'
import { Login } from './pages/Login'
import { Navbar } from './components/Navbar'
import { ToastContainer } from './components/Toast'
import { useDevices } from './hooks/useDevices'
import { AuthProvider, useAuth } from './context/AuthContext'
import './index.css'

function ProtectedRoute({ children }) {
  const { user } = useAuth()
  if (user === undefined) return null // loading
  if (!user) return <Navigate to="/login" replace />
  return children
}

function AppShell() {
  const { devices, dispatch, wsStatus } = useDevices()

  return (
    <>
      <Navbar wsStatus={wsStatus} />
      <Routes>
        <Route path="/" element={<Dashboard devices={devices} dispatch={dispatch} />} />
        <Route path="/device/:deviceId" element={<DeviceDetail devices={devices} dispatch={dispatch} />} />
        <Route path="/admin/users" element={<AdminUsers />} />
      </Routes>
      <ToastContainer />
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AuthRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}

function AuthRoutes() {
  const { user } = useAuth()

  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <Login />}
      />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

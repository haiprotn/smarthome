import { useEffect, useState } from 'react'

let _push = null
export function pushToast(msg, type = 'info') {
  _push?.({ id: Date.now(), msg, type })
}

export function ToastContainer() {
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    _push = (t) => {
      setToasts(prev => [...prev.slice(-4), t])
      setTimeout(() => setToasts(prev => prev.filter(x => x.id !== t.id)), 3500)
    }
    return () => { _push = null }
  }, [])

  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast toast-${t.type}`}>{t.msg}</div>
      ))}
    </div>
  )
}

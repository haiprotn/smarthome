import { useEffect, useState } from 'react'
import { fetchSchedules, createSchedule, patchSchedule, deleteSchedule } from '../api/schedules'
import { pushToast } from './Toast'

const DAY_LABELS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']

function emptyForm() {
  return { dp_id: 1, value: true, days: [0, 1, 2, 3, 4], time_hhmm: '07:00', label: '' }
}

export function SchedulePanel({ deviceId }) {
  const [schedules, setSchedules] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(emptyForm())
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchSchedules(deviceId).then(setSchedules).catch(() => {})
  }, [deviceId])

  function toggleDay(d) {
    setForm(f => ({
      ...f,
      days: f.days.includes(d) ? f.days.filter(x => x !== d) : [...f.days, d],
    }))
  }

  async function handleSave() {
    if (!form.days.length) { pushToast('Chọn ít nhất 1 ngày', 'error'); return }
    setSaving(true)
    try {
      const payload = { ...form, value: form.value === 'true' || form.value === true }
      const s = await createSchedule(deviceId, payload)
      setSchedules(prev => [...prev, s])
      setShowForm(false)
      setForm(emptyForm())
      pushToast('Đã tạo lịch', 'success')
    } catch (e) {
      pushToast(e.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  async function handleToggle(s) {
    try {
      const updated = await patchSchedule(deviceId, s.id, { enabled: !s.enabled })
      setSchedules(prev => prev.map(x => x.id === s.id ? updated : x))
    } catch (e) {
      pushToast(e.message, 'error')
    }
  }

  async function handleDelete(id) {
    try {
      await deleteSchedule(deviceId, id)
      setSchedules(prev => prev.filter(x => x.id !== id))
      pushToast('Đã xóa lịch', 'info')
    } catch (e) {
      pushToast(e.message, 'error')
    }
  }

  return (
    <div className="schedule-panel">
      <div className="schedule-header">
        <h3>Lịch tự động</h3>
        <button className="btn-sm btn-primary" onClick={() => setShowForm(v => !v)}>
          {showForm ? 'Hủy' : '+ Thêm lịch'}
        </button>
      </div>

      {showForm && (
        <div className="schedule-form">
          <div className="form-row">
            <label>DP ID</label>
            <input type="number" min={1} max={255} value={form.dp_id}
              onChange={e => setForm(f => ({ ...f, dp_id: parseInt(e.target.value) || 1 }))} />
          </div>
          <div className="form-row">
            <label>Giá trị</label>
            <select value={String(form.value)}
              onChange={e => setForm(f => ({ ...f, value: e.target.value === 'true' }))}>
              <option value="true">Bật (ON)</option>
              <option value="false">Tắt (OFF)</option>
            </select>
          </div>
          <div className="form-row">
            <label>Giờ</label>
            <input type="time" value={form.time_hhmm}
              onChange={e => setForm(f => ({ ...f, time_hhmm: e.target.value }))} />
          </div>
          <div className="form-row">
            <label>Ngày</label>
            <div className="day-picker">
              {DAY_LABELS.map((d, i) => (
                <button key={i}
                  className={`day-btn${form.days.includes(i) ? ' active' : ''}`}
                  onClick={() => toggleDay(i)} type="button">
                  {d}
                </button>
              ))}
            </div>
          </div>
          <div className="form-row">
            <label>Tên (tuỳ chọn)</label>
            <input type="text" placeholder="VD: Bật đèn buổi sáng" value={form.label}
              onChange={e => setForm(f => ({ ...f, label: e.target.value }))} />
          </div>
          <button className="btn-save" onClick={handleSave} disabled={saving}>
            {saving ? 'Đang lưu...' : 'Lưu lịch'}
          </button>
        </div>
      )}

      <div className="schedule-list">
        {schedules.length === 0 && !showForm && (
          <p className="empty-small">Chưa có lịch nào. Nhấn "+ Thêm lịch" để tạo.</p>
        )}
        {schedules.map(s => (
          <div key={s.id} className={`schedule-item${s.enabled ? '' : ' disabled'}`}>
            <div className="schedule-main">
              <span className="schedule-time">{s.time_hhmm}</span>
              <span className={`schedule-value ${s.value ? 'on' : 'off'}`}>
                {s.value ? 'BẬT' : 'TẮT'} DP{s.dp_id}
              </span>
              <div className="schedule-days">
                {DAY_LABELS.map((d, i) => (
                  <span key={i} className={`day-chip${s.days.includes(i) ? ' active' : ''}`}>{d}</span>
                ))}
              </div>
              {s.label && <span className="schedule-label">{s.label}</span>}
            </div>
            <div className="schedule-actions">
              <button className={`toggle-btn ${s.enabled ? 'on' : 'off'}`} onClick={() => handleToggle(s)}>
                {s.enabled ? 'Bật' : 'Tắt'}
              </button>
              <button className="btn-sm btn-danger" onClick={() => handleDelete(s.id)}>Xóa</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export async function fetchSchedules(deviceId) {
  const r = await fetch(`/api/devices/${deviceId}/schedules`)
  if (!r.ok) throw new Error('Không thể tải lịch')
  return r.json()
}

export async function createSchedule(deviceId, body) {
  const r = await fetch(`/api/devices/${deviceId}/schedules`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) {
    const e = await r.json()
    throw new Error(e.detail || 'Tạo lịch thất bại')
  }
  return r.json()
}

export async function patchSchedule(deviceId, scheduleId, body) {
  const r = await fetch(`/api/devices/${deviceId}/schedules/${scheduleId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error('Cập nhật lịch thất bại')
  return r.json()
}

export async function deleteSchedule(deviceId, scheduleId) {
  const r = await fetch(`/api/devices/${deviceId}/schedules/${scheduleId}`, { method: 'DELETE' })
  if (!r.ok) throw new Error('Xóa lịch thất bại')
  return r.json()
}

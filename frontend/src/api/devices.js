const BASE = '/api/devices'

export async function fetchDevices() {
  const r = await fetch(BASE + '/')
  if (!r.ok) throw new Error('Failed to fetch devices')
  return r.json()
}

export async function fetchDevice(deviceId) {
  const r = await fetch(`${BASE}/${deviceId}`)
  if (!r.ok) throw new Error('Device not found')
  return r.json()
}

export async function fetchHistory(deviceId, { dpId, hours = 24 } = {}) {
  const params = new URLSearchParams({ hours })
  if (dpId != null) params.set('dp_id', dpId)
  const r = await fetch(`${BASE}/${deviceId}/history?${params}`)
  if (!r.ok) throw new Error('Failed to fetch history')
  return r.json()
}

export async function sendCommand(deviceId, dpId, value) {
  const r = await fetch(`${BASE}/${deviceId}/cmd`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dp_id: dpId, value }),
  })
  if (!r.ok) throw new Error('Command failed')
  return r.json()
}

export async function deleteDevice(deviceId) {
  const r = await fetch(`${BASE}/${deviceId}`, { method: 'DELETE' })
  if (!r.ok) throw new Error('Delete failed')
  return r.json()
}

export async function updateDevice(deviceId, patch) {
  const r = await fetch(`${BASE}/${deviceId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
  if (!r.ok) throw new Error('Update failed')
  return r.json()
}

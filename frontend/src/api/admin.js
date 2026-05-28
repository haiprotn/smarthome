export async function fetchUsers() {
  const r = await fetch('/api/admin/users')
  if (!r.ok) throw new Error('Không thể tải danh sách user')
  return r.json()
}

export async function toggleAdmin(userId) {
  const r = await fetch(`/api/admin/users/${userId}`, { method: 'PATCH' })
  if (!r.ok) throw new Error('Thao tác thất bại')
  return r.json()
}

export async function deleteUser(userId) {
  const r = await fetch(`/api/admin/users/${userId}`, { method: 'DELETE' })
  if (!r.ok) throw new Error('Xóa user thất bại')
  return r.json()
}

import 'package:flutter/material.dart';
import '../services/admin_service.dart';

class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key});

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> {
  List<AdminUser> _users = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final users = await AdminService.listUsers();
      if (mounted) setState(() { _users = users; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  Future<void> _toggleAdmin(AdminUser user) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('Xác nhận', style: TextStyle(color: Colors.white)),
        content: Text(
          user.isAdmin
              ? 'Bỏ quyền admin của "${user.username}"?'
              : 'Cấp quyền admin cho "${user.username}"?',
          style: const TextStyle(color: Color(0xFF94A3B8)),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Hủy')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(user.isAdmin ? 'Bỏ admin' : 'Cấp admin',
                style: const TextStyle(color: Color(0xFF3B82F6))),
          ),
        ],
      ),
    );
    if (confirm != true) return;

    try {
      final newIsAdmin = await AdminService.toggleAdmin(user.id);
      if (mounted) {
        setState(() {
          final idx = _users.indexWhere((u) => u.id == user.id);
          if (idx >= 0) {
            _users[idx] = AdminUser(
              id: user.id,
              username: user.username,
              isAdmin: newIsAdmin,
              deviceCount: user.deviceCount,
            );
          }
        });
      }
    } catch (e) {
      if (mounted) _showError(e.toString());
    }
  }

  Future<void> _deleteUser(AdminUser user) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('Xóa người dùng', style: TextStyle(color: Colors.white)),
        content: Text(
          'Xóa tài khoản "${user.username}"?\nThao tác này không thể hoàn tác.',
          style: const TextStyle(color: Color(0xFF94A3B8)),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Hủy')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Xóa', style: TextStyle(color: Color(0xFFEF4444))),
          ),
        ],
      ),
    );
    if (confirm != true) return;

    try {
      await AdminService.deleteUser(user.id);
      if (mounted) setState(() => _users.removeWhere((u) => u.id == user.id));
    } catch (e) {
      if (mounted) _showError(e.toString());
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: const Color(0xFFEF4444)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('Quản lý người dùng', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF3B82F6)))
          : _error != null
              ? Center(
                  child: Column(mainAxisSize: MainAxisSize.min, children: [
                    const Icon(Icons.lock_outline, size: 48, color: Color(0xFF475569)),
                    const SizedBox(height: 12),
                    Text(_error!, style: const TextStyle(color: Color(0xFF94A3B8))),
                    const SizedBox(height: 12),
                    TextButton(onPressed: _load, child: const Text('Thử lại')),
                  ]),
                )
              : RefreshIndicator(
                  onRefresh: _load,
                  color: const Color(0xFF3B82F6),
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: _users.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (_, i) => _UserCard(
                      user: _users[i],
                      onToggleAdmin: () => _toggleAdmin(_users[i]),
                      onDelete: () => _deleteUser(_users[i]),
                    ),
                  ),
                ),
    );
  }
}

class _UserCard extends StatelessWidget {
  final AdminUser user;
  final VoidCallback onToggleAdmin;
  final VoidCallback onDelete;

  const _UserCard({
    required this.user,
    required this.onToggleAdmin,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF334155)),
      ),
      child: Row(
        children: [
          // Avatar
          Container(
            width: 40, height: 40,
            decoration: BoxDecoration(
              color: const Color(0xFF0F172A),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Center(
              child: Text(
                user.username.substring(0, 1).toUpperCase(),
                style: const TextStyle(
                    color: Color(0xFF3B82F6), fontWeight: FontWeight.bold, fontSize: 16),
              ),
            ),
          ),
          const SizedBox(width: 12),
          // Info
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Flexible(
                  child: Text(user.username,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                ),
                if (user.isAdmin) ...[
                  const SizedBox(width: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1D4ED8).withAlpha(60),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text('ADMIN',
                        style: TextStyle(
                            color: Color(0xFF60A5FA), fontSize: 10, fontWeight: FontWeight.bold)),
                  ),
                ],
              ]),
              const SizedBox(height: 2),
              Text(
                '${user.deviceCount} thiết bị',
                style: const TextStyle(color: Color(0xFF64748B), fontSize: 12),
              ),
            ]),
          ),
          // Actions
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert, color: Color(0xFF64748B)),
            color: const Color(0xFF1E293B),
            onSelected: (v) {
              if (v == 'toggle') onToggleAdmin();
              if (v == 'delete') onDelete();
            },
            itemBuilder: (_) => [
              PopupMenuItem(
                value: 'toggle',
                child: Row(children: [
                  Icon(
                    user.isAdmin ? Icons.remove_moderator_outlined : Icons.admin_panel_settings_outlined,
                    size: 18,
                    color: const Color(0xFF94A3B8),
                  ),
                  const SizedBox(width: 8),
                  Text(user.isAdmin ? 'Bỏ quyền admin' : 'Cấp quyền admin'),
                ]),
              ),
              const PopupMenuDivider(),
              const PopupMenuItem(
                value: 'delete',
                child: Row(children: [
                  Icon(Icons.delete_outline, size: 18, color: Color(0xFFEF4444)),
                  SizedBox(width: 8),
                  Text('Xóa tài khoản', style: TextStyle(color: Color(0xFFEF4444))),
                ]),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

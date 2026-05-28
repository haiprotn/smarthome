import 'dart:convert';
import 'api_service.dart';

class AdminUser {
  final int id;
  final String username;
  final bool isAdmin;
  final int deviceCount;

  AdminUser({
    required this.id,
    required this.username,
    required this.isAdmin,
    required this.deviceCount,
  });

  factory AdminUser.fromJson(Map<String, dynamic> j) => AdminUser(
        id: j['id'],
        username: j['username'],
        isAdmin: j['is_admin'],
        deviceCount: j['device_count'] ?? 0,
      );
}

class AdminService {
  static Future<List<AdminUser>> listUsers() async {
    final r = await ApiService.get('/api/admin/users');
    if (r.statusCode != 200) throw Exception('Không có quyền truy cập');
    final list = jsonDecode(r.body) as List;
    return list.map((j) => AdminUser.fromJson(j)).toList();
  }

  static Future<bool> toggleAdmin(int userId) async {
    final r = await ApiService.patch('/api/admin/users/$userId', {});
    if (r.statusCode != 200) throw Exception('Thao tác thất bại');
    return jsonDecode(r.body)['is_admin'] as bool;
  }

  static Future<void> deleteUser(int userId) async {
    final r = await ApiService.delete('/api/admin/users/$userId');
    if (r.statusCode != 200) throw Exception('Xóa thất bại');
  }
}

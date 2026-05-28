import 'dart:convert';
import 'api_service.dart';

class AuthUser {
  final int id;
  final String username;
  final bool isAdmin;

  AuthUser({required this.id, required this.username, required this.isAdmin});

  factory AuthUser.fromJson(Map<String, dynamic> j) => AuthUser(
        id: j['id'],
        username: j['username'],
        isAdmin: j['is_admin'] ?? false,
      );
}

class AuthService {
  static Future<AuthUser> login(String username, String password) async {
    final r = await ApiService.post('/api/auth/login', {
      'username': username,
      'password': password,
    });
    if (r.statusCode != 200) {
      final e = jsonDecode(r.body);
      throw Exception(e['detail'] ?? 'Đăng nhập thất bại');
    }
    await ApiService.saveCookie(r);
    final data = jsonDecode(r.body);
    return AuthUser(
      id: 0,
      username: data['username'],
      isAdmin: data['is_admin'] ?? false,
    );
  }

  static Future<AuthUser> me() async {
    final r = await ApiService.get('/api/auth/me');
    if (r.statusCode != 200) throw Exception('Chưa đăng nhập');
    return AuthUser.fromJson(jsonDecode(r.body));
  }

  static Future<void> logout() async {
    await ApiService.post('/api/auth/logout', {});
    await ApiService.clearCookie();
  }
}

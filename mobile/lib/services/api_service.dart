import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

// Production
const String kBaseUrl = 'https://tncsmarthome.com';

// Dev (bỏ comment khi dev local):
// const String kBaseUrl = 'http://localhost:8000';     // Windows desktop
// const String kBaseUrl = 'http://10.0.2.2:8000';     // Android emulator
// const String kBaseUrl = 'http://10.0.3.2:8000';     // Genymotion
// const String kBaseUrl = 'http://192.168.1.x:8000';  // Điện thoại thật LAN

class ApiService {
  static Future<Map<String, String>> _headers() async {
    final prefs = await SharedPreferences.getInstance();
    final cookie = prefs.getString('cookie') ?? '';
    return {
      'Content-Type': 'application/json',
      if (cookie.isNotEmpty) 'Cookie': cookie,
    };
  }

  static Future<http.Response> get(String path) async {
    return http.get(Uri.parse('$kBaseUrl$path'), headers: await _headers());
  }

  static Future<http.Response> post(String path, Map<String, dynamic> body) async {
    return http.post(
      Uri.parse('$kBaseUrl$path'),
      headers: await _headers(),
      body: jsonEncode(body),
    );
  }

  static Future<http.Response> patch(String path, Map<String, dynamic> body) async {
    return http.patch(
      Uri.parse('$kBaseUrl$path'),
      headers: await _headers(),
      body: jsonEncode(body),
    );
  }

  static Future<http.Response> delete(String path) async {
    return http.delete(Uri.parse('$kBaseUrl$path'), headers: await _headers());
  }

  // Lưu cookie từ Set-Cookie header
  static Future<void> saveCookie(http.Response response) async {
    final raw = response.headers['set-cookie'];
    if (raw == null) return;
    final prefs = await SharedPreferences.getInstance();
    // Lấy phần tên=giá trị trước dấu ;
    final cookie = raw.split(';').first.trim();
    await prefs.setString('cookie', cookie);
  }

  static Future<void> clearCookie() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('cookie');
  }
}

import 'dart:convert';
import '../models/device.dart';
import 'api_service.dart';

class DeviceService {
  static Future<List<Device>> listDevices() async {
    final r = await ApiService.get('/api/devices/');
    if (r.statusCode != 200) throw Exception('Không thể tải thiết bị');
    final list = jsonDecode(r.body) as List;
    return list.map((j) => Device.fromJson(j)).toList();
  }

  static Future<Device> getDevice(String deviceId) async {
    final r = await ApiService.get('/api/devices/$deviceId');
    if (r.statusCode != 200) throw Exception('Không tìm thấy thiết bị');
    return Device.fromJson(jsonDecode(r.body));
  }

  static Future<void> sendCommand(String deviceId, int dpId, dynamic value) async {
    final r = await ApiService.post('/api/devices/$deviceId/cmd', {
      'dp_id': dpId,
      'value': value,
    });
    if (r.statusCode != 200) throw Exception('Gửi lệnh thất bại');
  }

  static Future<List<HistoryPoint>> getHistory(String deviceId, {int hours = 24, int? dpId}) async {
    var path = '/api/devices/$deviceId/history?hours=$hours&limit=300';
    if (dpId != null) path += '&dp_id=$dpId';
    final r = await ApiService.get(path);
    if (r.statusCode != 200) return [];
    final list = jsonDecode(r.body) as List;
    return list.map((j) => HistoryPoint.fromJson(j)).toList();
  }
}

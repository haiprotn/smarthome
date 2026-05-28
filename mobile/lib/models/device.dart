class DpState {
  final int dpId;
  final dynamic value;
  final DateTime updatedAt;

  DpState({required this.dpId, required this.value, required this.updatedAt});

  factory DpState.fromJson(Map<String, dynamic> j) => DpState(
        dpId: j['dp_id'],
        value: j['value'],
        updatedAt: DateTime.parse(j['updated_at']),
      );
}

class Device {
  final String deviceId;
  final String productId;
  final String productName;
  final String? friendlyName;
  final String? room;
  bool isOnline;
  final DateTime? lastSeen;
  final DateTime createdAt;
  List<DpState> dpStates;

  Device({
    required this.deviceId,
    required this.productId,
    required this.productName,
    this.friendlyName,
    this.room,
    required this.isOnline,
    this.lastSeen,
    required this.createdAt,
    this.dpStates = const [],
  });

  String get displayName => friendlyName?.isNotEmpty == true ? friendlyName! : deviceId;

  factory Device.fromJson(Map<String, dynamic> j) => Device(
        deviceId: j['device_id'],
        productId: j['product_id'],
        productName: j['product_name'],
        friendlyName: j['friendly_name'],
        room: j['room'],
        isOnline: j['is_online'] ?? false,
        lastSeen: j['last_seen'] != null ? DateTime.parse(j['last_seen']) : null,
        createdAt: DateTime.parse(j['created_at']),
        dpStates: (j['dp_states'] as List<dynamic>? ?? [])
            .map((s) => DpState.fromJson(s))
            .toList(),
      );
}

class HistoryPoint {
  final int dpId;
  final dynamic value;
  final DateTime timestamp;

  HistoryPoint({required this.dpId, required this.value, required this.timestamp});

  factory HistoryPoint.fromJson(Map<String, dynamic> j) => HistoryPoint(
        dpId: j['dp_id'],
        value: j['value'],
        timestamp: DateTime.parse(j['timestamp']),
      );
}

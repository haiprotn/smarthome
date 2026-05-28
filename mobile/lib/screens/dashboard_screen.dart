import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/device.dart';
import '../services/device_service.dart';
import '../main.dart';
import '../services/api_service.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  List<Device> _devices = [];
  bool _loading = true;
  WebSocketChannel? _ws;
  String _wsStatus = 'connecting'; // connecting | connected | disconnected

  @override
  void initState() {
    super.initState();
    _loadDevices();
    _connectWs();
  }

  @override
  void dispose() {
    _ws?.sink.close();
    super.dispose();
  }

  Future<void> _loadDevices() async {
    try {
      final devices = await DeviceService.listDevices();
      if (mounted) setState(() { _devices = devices; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _connectWs() async {
    final prefs = await SharedPreferences.getInstance();
    final cookie = prefs.getString('cookie') ?? '';
    final wsUrl = kBaseUrl.replaceFirst('http', 'ws') + '/ws';

    try {
      _ws = WebSocketChannel.connect(
        Uri.parse(wsUrl),
        protocols: cookie.isNotEmpty ? [] : null,
      );
      if (mounted) setState(() => _wsStatus = 'connected');

      _ws!.stream.listen(
        (data) {
          if (!mounted) return;
          try {
            final msg = jsonDecode(data as String);
            _handleWsMessage(msg);
          } catch (_) {}
        },
        onDone: () {
          if (mounted) {
            setState(() => _wsStatus = 'disconnected');
            Future.delayed(const Duration(seconds: 3), _connectWs);
          }
        },
        onError: (_) {
          if (mounted) {
            setState(() => _wsStatus = 'disconnected');
            Future.delayed(const Duration(seconds: 3), _connectWs);
          }
        },
      );
    } catch (_) {
      if (mounted) {
        setState(() => _wsStatus = 'disconnected');
        Future.delayed(const Duration(seconds: 3), _connectWs);
      }
    }
  }

  void _handleWsMessage(Map<String, dynamic> msg) {
    final deviceId = msg['device_id'] as String?;
    if (deviceId == null) return;

    setState(() {
      final idx = _devices.indexWhere((d) => d.deviceId == deviceId);
      if (idx < 0) return;

      if (msg['type'] == 'online') {
        _devices[idx].isOnline = true;
      } else if (msg['type'] == 'offline') {
        _devices[idx].isOnline = false;
      } else if (msg['type'] == 'dp_state') {
        final dpId = msg['dp_id'] as int;
        final value = msg['value'];
        final dpIdx = _devices[idx].dpStates.indexWhere((s) => s.dpId == dpId);
        if (dpIdx >= 0) {
          _devices[idx].dpStates[dpIdx] = DpState(
            dpId: dpId, value: value, updatedAt: DateTime.now());
        }
      }
    });
  }

  Future<void> _toggle(Device device, int dpId, bool current) async {
    try {
      await DeviceService.sendCommand(device.deviceId, dpId, !current);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: Colors.red));
      }
    }
  }

  // Group devices by room
  Map<String, List<Device>> get _grouped {
    final map = <String, List<Device>>{};
    for (final d in _devices) {
      final key = d.room?.isNotEmpty == true ? d.room! : 'Chưa phân phòng';
      map.putIfAbsent(key, () => []).add(d);
    }
    return map;
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E293B),
        title: const Row(children: [
          Text('⌂ ', style: TextStyle(fontSize: 20)),
          Text('Smart Home', style: TextStyle(fontWeight: FontWeight.bold)),
        ]),
        actions: [
          // WS status indicator
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: _WsDot(status: _wsStatus),
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.person_outline),
            color: const Color(0xFF1E293B),
            onSelected: (v) async {
              if (v == 'admin') {
                Navigator.pushNamed(context, '/admin');
              } else if (v == 'logout') {
                final auth = context.read<AuthProvider>();
                await auth.logout();
                if (mounted) Navigator.pushReplacementNamed(context, '/login');
              }
            },
            itemBuilder: (_) => [
              PopupMenuItem(
                enabled: false,
                child: Text(auth.user?.username ?? '',
                    style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13)),
              ),
              if (auth.user?.isAdmin == true)
                const PopupMenuItem(
                  value: 'admin',
                  child: Row(children: [
                    Icon(Icons.admin_panel_settings_outlined, size: 18, color: Color(0xFF60A5FA)),
                    SizedBox(width: 8),
                    Text('Quản lý người dùng'),
                  ]),
                ),
              const PopupMenuItem(value: 'logout', child: Text('Đăng xuất')),
            ],
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF3B82F6)))
          : _devices.isEmpty
              ? _buildEmpty()
              : RefreshIndicator(
                  onRefresh: _loadDevices,
                  color: const Color(0xFF3B82F6),
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: _grouped.entries.map((entry) => _buildRoom(entry.key, entry.value)).toList(),
                  ),
                ),
    );
  }

  Widget _buildEmpty() => Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.devices_other, size: 64, color: Color(0xFF334155)),
          const SizedBox(height: 16),
          const Text('Chưa có thiết bị nào', style: TextStyle(color: Color(0xFF64748B))),
          const SizedBox(height: 8),
          TextButton(onPressed: _loadDevices, child: const Text('Thử lại')),
        ]),
      );

  Widget _buildRoom(String room, List<Device> devices) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Text(room.toUpperCase(),
                style: const TextStyle(
                    fontSize: 11, fontWeight: FontWeight.w700,
                    letterSpacing: 1.2, color: Color(0xFF64748B))),
          ),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
              maxCrossAxisExtent: 200, mainAxisExtent: 120, crossAxisSpacing: 10, mainAxisSpacing: 10),
            itemCount: devices.length,
            itemBuilder: (_, i) => _DeviceCard(
              device: devices[i],
              onTap: () => Navigator.pushNamed(context, '/device', arguments: devices[i].deviceId)
                  .then((_) => _loadDevices()),
              onToggle: _toggle,
            ),
          ),
          const SizedBox(height: 8),
        ],
      );
}

class _WsDot extends StatelessWidget {
  final String status;
  const _WsDot({required this.status});

  @override
  Widget build(BuildContext context) {
    final color = status == 'connected'
        ? const Color(0xFF22C55E)
        : status == 'connecting'
            ? const Color(0xFF60A5FA)
            : const Color(0xFFEF4444);
    final label = status == 'connected' ? 'Realtime' : status == 'connecting' ? '...' : 'Mất KN';
    return Row(children: [
      Container(width: 8, height: 8, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
      const SizedBox(width: 4),
      Text(label, style: TextStyle(fontSize: 11, color: color)),
    ]);
  }
}

class _DeviceCard extends StatelessWidget {
  final Device device;
  final VoidCallback onTap;
  final Future<void> Function(Device, int, bool) onToggle;

  const _DeviceCard({required this.device, required this.onTap, required this.onToggle});

  bool get _relay => device.dpStates.any((s) => s.dpId == 1 && s.value == true);

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF334155)),
        ),
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Container(
                width: 8, height: 8,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: device.isOnline ? const Color(0xFF22C55E) : const Color(0xFF475569),
                ),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(device.displayName,
                    maxLines: 1, overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
              ),
            ]),
            const Spacer(),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(device.productName,
                    style: const TextStyle(color: Color(0xFF64748B), fontSize: 11),
                    maxLines: 1, overflow: TextOverflow.ellipsis),
                if (device.dpStates.isNotEmpty)
                  GestureDetector(
                    onTap: () => onToggle(device, 1, _relay),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: _relay ? const Color(0xFF22C55E) : const Color(0xFF334155),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(_relay ? 'BẬT' : 'TẮT',
                          style: TextStyle(
                              fontSize: 11, fontWeight: FontWeight.bold,
                              color: _relay ? const Color(0xFF052E16) : const Color(0xFF94A3B8))),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

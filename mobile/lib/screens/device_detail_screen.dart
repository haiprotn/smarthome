import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/device.dart';
import '../services/device_service.dart';
import '../services/api_service.dart';

class DeviceDetailScreen extends StatefulWidget {
  final String deviceId;
  const DeviceDetailScreen({super.key, required this.deviceId});

  @override
  State<DeviceDetailScreen> createState() => _DeviceDetailScreenState();
}

class _DeviceDetailScreenState extends State<DeviceDetailScreen> {
  Device? _device;
  List<HistoryPoint> _history = [];
  int _hours = 24;
  bool _loading = true;
  bool _toggling = false;
  WebSocketChannel? _ws;

  @override
  void initState() {
    super.initState();
    _load();
    _connectWs();
  }

  @override
  void dispose() {
    _ws?.sink.close();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final device = await DeviceService.getDevice(widget.deviceId);
      final history = await DeviceService.getHistory(widget.deviceId, hours: _hours, dpId: 1);
      if (mounted) setState(() { _device = device; _history = history; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _connectWs() async {
    final prefs = await SharedPreferences.getInstance();
    final wsUrl = kBaseUrl.replaceFirst('http', 'ws') + '/ws';
    try {
      _ws = WebSocketChannel.connect(Uri.parse(wsUrl));
      _ws!.stream.listen((data) {
        if (!mounted) return;
        try {
          final msg = jsonDecode(data as String);
          if (msg['device_id'] != widget.deviceId) return;
          setState(() {
            if (msg['type'] == 'online') _device?.isOnline = true;
            if (msg['type'] == 'offline') _device?.isOnline = false;
            if (msg['type'] == 'dp_state' && _device != null) {
              final dpId = msg['dp_id'] as int;
              final value = msg['value'];
              final idx = _device!.dpStates.indexWhere((s) => s.dpId == dpId);
              final newState = DpState(dpId: dpId, value: value, updatedAt: DateTime.now());
              if (idx >= 0) _device!.dpStates[idx] = newState;
              else _device!.dpStates.add(newState);
            }
          });
        } catch (_) {}
      }, onDone: () => Future.delayed(const Duration(seconds: 3), _connectWs));
    } catch (_) {
      Future.delayed(const Duration(seconds: 3), _connectWs);
    }
  }

  Future<void> _toggle(int dpId, bool current) async {
    setState(() => _toggling = true);
    try {
      await DeviceService.sendCommand(widget.deviceId, dpId, !current);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: Colors.red));
    } finally {
      if (mounted) setState(() => _toggling = false);
    }
  }

  Future<void> _loadHistory() async {
    final h = await DeviceService.getHistory(widget.deviceId, hours: _hours, dpId: 1);
    if (mounted) setState(() => _history = h);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E293B),
        title: Text(_device?.displayName ?? widget.deviceId,
            style: const TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          if (_device != null)
            Container(
              margin: const EdgeInsets.only(right: 12),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: _device!.isOnline ? const Color(0xFF064E3B) : const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(_device!.isOnline ? 'Online' : 'Offline',
                  style: TextStyle(
                      fontSize: 12, fontWeight: FontWeight.w600,
                      color: _device!.isOnline ? const Color(0xFF34D399) : const Color(0xFF64748B))),
            ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF3B82F6)))
          : _device == null
              ? const Center(child: Text('Không tìm thấy thiết bị'))
              : RefreshIndicator(
                  onRefresh: _load,
                  color: const Color(0xFF3B82F6),
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      _buildInfo(),
                      const SizedBox(height: 16),
                      _buildDpList(),
                      const SizedBox(height: 24),
                      _buildHistoryChart(),
                    ],
                  ),
                ),
    );
  }

  Widget _buildInfo() => Container(
        padding: const EdgeInsets.all(16),
        decoration: _cardDeco(),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(_device!.productName, style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13)),
          const SizedBox(height: 4),
          Text(_device!.deviceId,
              style: const TextStyle(fontFamily: 'monospace', color: Color(0xFF64748B), fontSize: 12)),
          if (_device!.room?.isNotEmpty == true) ...[
            const SizedBox(height: 4),
            Row(children: [
              const Icon(Icons.room_outlined, size: 14, color: Color(0xFF64748B)),
              const SizedBox(width: 4),
              Text(_device!.room!, style: const TextStyle(color: Color(0xFF64748B), fontSize: 12)),
            ]),
          ],
        ]),
      );

  Widget _buildDpList() => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Điểm dữ liệu',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFF94A3B8))),
          const SizedBox(height: 10),
          if (_device!.dpStates.isEmpty)
            const Text('Chưa có dữ liệu', style: TextStyle(color: Color(0xFF64748B)))
          else
            ..._device!.dpStates.map((s) => _DpRow(
                  dpState: s,
                  online: _device!.isOnline,
                  toggling: _toggling,
                  onToggle: () => _toggle(s.dpId, s.value == true),
                )),
        ],
      );

  Widget _buildHistoryChart() => Container(
        padding: const EdgeInsets.all(16),
        decoration: _cardDeco(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Lịch sử DP1',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                DropdownButton<int>(
                  value: _hours,
                  dropdownColor: const Color(0xFF1E293B),
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                  underline: const SizedBox(),
                  items: const [
                    DropdownMenuItem(value: 6, child: Text('6h')),
                    DropdownMenuItem(value: 24, child: Text('24h')),
                    DropdownMenuItem(value: 72, child: Text('3 ngày')),
                  ],
                  onChanged: (v) {
                    if (v == null) return;
                    setState(() => _hours = v);
                    _loadHistory();
                  },
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (_history.isEmpty)
              const SizedBox(
                height: 120,
                child: Center(child: Text('Không có dữ liệu', style: TextStyle(color: Color(0xFF64748B)))),
              )
            else
              SizedBox(height: 160, child: _buildChart()),
          ],
        ),
      );

  Widget _buildChart() {
    final spots = _history.asMap().entries.map((e) {
      final t = e.value.timestamp.millisecondsSinceEpoch.toDouble();
      final v = e.value.value == true ? 1.0 : 0.0;
      return FlSpot(t, v);
    }).toList();

    final minX = spots.first.x;
    final maxX = spots.last.x;
    final fmt = DateFormat('HH:mm');

    return LineChart(LineChartData(
      minY: -0.1, maxY: 1.1,
      minX: minX, maxX: maxX,
      lineBarsData: [
        LineChartBarData(
          spots: spots,
          isCurved: false,
          isStepLineChart: true,
          color: const Color(0xFF3B82F6),
          dotData: const FlDotData(show: false),
          belowBarData: BarAreaData(
            show: true,
            color: const Color(0xFF3B82F6).withAlpha(40),
          ),
        ),
      ],
      titlesData: FlTitlesData(
        leftTitles: AxisTitles(sideTitles: SideTitles(
          showTitles: true, reservedSize: 36,
          getTitlesWidget: (v, _) => Text(
            v == 1 ? 'ON' : v == 0 ? 'OFF' : '',
            style: const TextStyle(color: Color(0xFF64748B), fontSize: 11)),
        )),
        bottomTitles: AxisTitles(sideTitles: SideTitles(
          showTitles: true, reservedSize: 24,
          interval: (maxX - minX) / 4,
          getTitlesWidget: (v, _) => Text(
            fmt.format(DateTime.fromMillisecondsSinceEpoch(v.toInt())),
            style: const TextStyle(color: Color(0xFF64748B), fontSize: 10)),
        )),
        rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      ),
      gridData: FlGridData(
        show: true,
        getDrawingHorizontalLine: (_) => const FlLine(color: Color(0xFF1E293B), strokeWidth: 1),
        getDrawingVerticalLine: (_) => const FlLine(color: Color(0xFF1E293B), strokeWidth: 1),
      ),
      borderData: FlBorderData(show: false),
    ));
  }

  BoxDecoration _cardDeco() => BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF334155)),
      );
}

class _DpRow extends StatelessWidget {
  final DpState dpState;
  final bool online;
  final bool toggling;
  final VoidCallback onToggle;

  const _DpRow({required this.dpState, required this.online, required this.toggling, required this.onToggle});

  @override
  Widget build(BuildContext context) {
    final isBool = dpState.value is bool;
    final isOn = dpState.value == true;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Text('DP${dpState.dpId}',
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          const Spacer(),
          if (!isBool)
            Text('${dpState.value}', style: const TextStyle(color: Color(0xFF94A3B8))),
          if (isBool) ...[
            if (toggling)
              const SizedBox(width: 16, height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF3B82F6)))
            else
              GestureDetector(
                onTap: online ? onToggle : null,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                  decoration: BoxDecoration(
                    color: isOn ? const Color(0xFF22C55E) : const Color(0xFF334155),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(isOn ? 'BẬT' : 'TẮT',
                      style: TextStyle(
                          fontWeight: FontWeight.bold, fontSize: 13,
                          color: isOn ? const Color(0xFF052E16) : const Color(0xFF94A3B8))),
                ),
              ),
          ],
        ],
      ),
    );
  }
}

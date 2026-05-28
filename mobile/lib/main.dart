import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/auth_service.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/device_detail_screen.dart';
import 'screens/admin_screen.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      create: (_) => AuthProvider(),
      child: const SmartHomeApp(),
    ),
  );
}

class AuthProvider extends ChangeNotifier {
  AuthUser? _user;
  AuthUser? get user => _user;

  void setUser(AuthUser? user) {
    _user = user;
    notifyListeners();
  }

  Future<void> logout() async {
    await AuthService.logout();
    _user = null;
    notifyListeners();
  }
}

class SmartHomeApp extends StatelessWidget {
  const SmartHomeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Home',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF3B82F6),
          surface: Color(0xFF1E293B),
        ),
        scaffoldBackgroundColor: const Color(0xFF0F172A),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1E293B),
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        textTheme: const TextTheme(
          bodyMedium: TextStyle(color: Colors.white),
        ),
      ),
      initialRoute: '/splash',
      routes: {
        '/splash': (_) => const _SplashScreen(),
        '/login': (_) => const LoginScreen(),
        '/dashboard': (_) => const DashboardScreen(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/device') {
          final deviceId = settings.arguments as String;
          return MaterialPageRoute(
              builder: (_) => DeviceDetailScreen(deviceId: deviceId));
        }
        if (settings.name == '/admin') {
          return MaterialPageRoute(builder: (_) => const AdminScreen());
        }
        return null;
      },
    );
  }
}

class _SplashScreen extends StatefulWidget {
  const _SplashScreen();

  @override
  State<_SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<_SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    try {
      final user = await AuthService.me();
      if (!mounted) return;
      context.read<AuthProvider>().setUser(user);
      Navigator.pushReplacementNamed(context, '/dashboard');
    } catch (_) {
      if (mounted) Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Color(0xFF0F172A),
      body: Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text('⌂', style: TextStyle(fontSize: 64)),
          SizedBox(height: 16),
          CircularProgressIndicator(color: Color(0xFF3B82F6)),
        ]),
      ),
    );
  }
}

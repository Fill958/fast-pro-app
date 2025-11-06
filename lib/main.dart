import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FastPro',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: Colors.blue,
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => const Screen1(),
      },
    );
  }
}

/// Первый экран — форма по центру со стеклянным эффектом
class Screen1 extends StatefulWidget {
  const Screen1({super.key});

  @override
  State<Screen1> createState() => _Screen1State();
}

class _Screen1State extends State<Screen1> {
  final TextEditingController _idController = TextEditingController();

  void _navigateToSecondScreen() {
    final id = _idController.text.trim();
    if (id.isNotEmpty && id == 'd263a900') {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => HealthStatsScreen(userId: id),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Введите корректный ID'),
        ),
      );
    }
  }

    


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF3A0CA3), Color(0xFF4361EE), Color(0xFF4CC9F0)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Column(
                children: const [
                  CircleAvatar(
                    radius: 36,
                    backgroundColor: Colors.white24,
                    child: Icon(Icons.monitor_heart, color: Colors.white, size: 40),
                  ),
                  SizedBox(height: 16),
                  Text(
                    'Приложение FastPro',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 22,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  SizedBox(height: 6),
                  Text(
                    'Введите ID вашего трекера',
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 40),

              // Эффект стекла вокруг формы
              ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: BackdropFilter(
                  filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
                  child: Container(
                    width: double.infinity,
                    margin: const EdgeInsets.symmetric(horizontal: 24),
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: Colors.white.withOpacity(0.3),
                        width: 1.2,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.1),
                          blurRadius: 12,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Align(
                          alignment: Alignment.centerLeft,
                          child: Text(
                            'ID Трекера',
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.9),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        TextField(
                          controller: _idController,
                          style: const TextStyle(color: Colors.white),
                          decoration: const InputDecoration(
                            labelText: 'Введите ID трекера',
                            labelStyle: TextStyle(color: Colors.white),
                            border: OutlineInputBorder(),
                            enabledBorder: OutlineInputBorder(
                              borderSide: BorderSide(color: Colors.white, width: 1.2), // бордер неактивный
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderSide: BorderSide(color: Colors.white, width: 1.5), // бордер при фокусе
                            ),
                          ),
                          keyboardType: TextInputType.text,
                          inputFormatters: [
                            FilteringTextInputFormatter.allow(RegExp(r'[a-zA-Z0-9\-]')),
                          ],
                        ),
                        const SizedBox(height: 20),
                        SizedBox(
                          width: double.infinity,
                          height: 48,
                          child: ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.white.withOpacity(0.3),
                              foregroundColor: Colors.white,
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(8),
                              ),
                            ),
                            onPressed: _navigateToSecondScreen,
                            child: const Text(
                              'Показать данные',
                              style: TextStyle(
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 50),

              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 24),
                child: Text(
                  'ID трекера можно найти на обратной стороне устройства.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class HealthStatsScreen extends StatefulWidget {
  final String userId;

  const HealthStatsScreen({super.key, required this.userId});

  @override
  State<HealthStatsScreen> createState() => _HealthStatsScreenState();
}

class _HealthStatsScreenState extends State<HealthStatsScreen> {
  Map<String, dynamic>? baseData;
  Map<String, dynamic>? currentData;
  Map<String, dynamic>? statuses;
  bool isLoading = true;
  Timer? _updateTimer;

  @override
  void initState() {
    super.initState();
    _loadBaseData();
  }

  @override
  void dispose() {
    _updateTimer?.cancel();
    super.dispose();
  }

  /// Первый запрос при загрузке экрана
  Future<void> _loadBaseData() async {
    final data = await getBaseData();
    if (mounted) {
      setState(() {
        baseData = data;
        isLoading = false;
      });
    }

    // как только получили первые данные — запускаем автообновление
    if (baseData != null) {
      _startAutoUpdate();
    }
  }

  /// 🔁 Автоматический POST-запрос каждую секунду
  void _startAutoUpdate() {
    _updateTimer = Timer.periodic(const Duration(seconds: 1), (timer) async {
      if (baseData == null) return;

      try {
        final updatedData = await sendBaseData(baseData!);
        if (updatedData != null && mounted) {
          setState(() {
            currentData = updatedData;
          });
        }
      } catch (e) {
        print('Ошибка при автообновлении: $e');
      }
    });
  }

  /// ⬇️ Получение базовых данных (первый запрос)
  Future<Map<String, dynamic>?> getBaseData() async {
    final url = Uri.parse('https://fast-pro-server.onrender.com/health-data');
    try {
      final response = await http.post(url);
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      print('Ошибка запроса: $e');
    }
    return null;
  }

  /// ⬆️ Отправка baseData на сервер и получение обновлённых данных
  Future<Map<String, dynamic>?> sendBaseData(Map<String, dynamic> currentData) async {
    final url = Uri.parse('https://fast-pro-server.onrender.com/health-data');
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode(currentData),
      );

      if (response.statusCode == 200) {
        final decoded = json.decode(response.body);
        if (decoded is Map<String, dynamic>) {
          return decoded;
        }
      }
    } catch (e) {
      print('Ошибка при отправке baseData: $e');
    }

    return null;
  }

  Map<String, String> getDescription(parameter, value) {
    String result = '';
    String status = '';
    String textStatus = '';

    switch (parameter) {
      case 'temperature':
        final double numValue = value is double
          ? value
          : (value is String ? double.tryParse(value) ?? 0 : 0);
        if (numValue < 36.0) {
          result = 'Температура ниже нормы';
          status = 'alert';
          textStatus = 'Опасно';
        } else if (numValue <= 37.5) {
          result = 'Температура в норме';
          status = 'normal';
          textStatus = 'Норма';
        } else {
          result = 'Температура выше нормы';
          status = 'alert';
          textStatus = 'Опасно';
        }
        break;

      case 'spo2':
        final int numValue = value is int
          ? value
          : (value is String ? int.tryParse(value) ?? 0 : 0);
        if (numValue < 93) {
          result = 'Низкий уровень кислорода';
          status = 'alert';
          textStatus = 'Опасно';
        } else {
          result = 'Уровень кислорода в норме';
          status = 'normal';
          textStatus = 'Норма';
        }
        break;

      case 'pulse':
        final int numValue = value is int
          ? value
          : (value is String ? int.tryParse(value) ?? 0 : 0);
        if (numValue < 60) {
          result = 'Пульс ниже нормы';
          status = 'warning';
          textStatus = 'Внимание';
        } else if (numValue <= 100) {
          result = 'Пульс в норме';
          status = 'normal';
          textStatus = 'Норма';
        } else {
          result = 'Пульс выше нормы';
          status = 'warning';
          textStatus = 'Внимание';
        }
        break;

      case 'stress':
      final int numValue = value is int
          ? value
          : (value is String ? int.tryParse(value) ?? 0 : 0);

      if (numValue < 30) {
        result = 'Похоже, Вы не стрессуете';
        status = 'normal';
        textStatus = 'Норма';
      } else if (numValue <= 70) {
        result = 'Стресс выше нормы';
        status = 'warning';
        textStatus = 'Внимание';
      } else {
        result = 'Стресс сильно выше нормы';
        status = 'alert';
        textStatus = 'Опасно';
      }
      break;
    }

    return {
      'result': result,
      'status': status,
      'textStatus': textStatus
    };
  }

  Color getColor(status) {
    dynamic color;
    switch(status) {
      case 'normal':
        color = Colors.green;
        break;
      case 'warning':
        color = Colors.amber;
        break;
      case 'alert':
        color = Colors.red;
        break;
    }

    return color;
  }
 
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF3A0CA3), Color(0xFF4361EE), Color(0xFF4CC9F0)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: isLoading
              ? const Center(
                  child: CircularProgressIndicator(color: Colors.white),
                )
              : Column(
                  children: [
                    // Верхняя панель
                    Padding(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 8),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          InkWell(
                            onTap: () => Navigator.pop(context),
                            child: const Row(
                              children: [
                                Icon(Icons.arrow_back, color: Colors.white),
                                SizedBox(width: 6),
                                Text("Назад",
                                    style: TextStyle(
                                        color: Colors.white, fontSize: 16)),
                              ],
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Row(
                              children: [
                                const Icon(Icons.monitor_heart,
                                    color: Colors.white, size: 18),
                                const SizedBox(width: 4),
                                Text("ID: ${widget.userId}",
                                    style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.w600)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                    const Padding(
                      padding:
                          EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      child: Align(
                        alignment: Alignment.centerLeft,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "Показатели спортсмена",
                              style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 22),
                            ),
                            SizedBox(height: 4),
                          ],
                        ),
                      ),
                    ),

                    Expanded(
                      child: Container(
                        decoration:
                            const BoxDecoration(color: Colors.white10),
                        child: ListView(
                          padding: const EdgeInsets.all(16),
                          children: currentData != null ? [
                            GlassHealthCard(
                              icon: Icons.thermostat_sharp,
                              title: "Температура",
                              value: '${currentData?['temperature']?.toString()}°C',
                              status: '${getDescription('temperature', currentData?['temperature'])['textStatus']}',
                              description: '${getDescription('temperature', currentData?['temperature'])['result']}',
                              statusColor: getColor(getDescription('temperature', currentData?['temperature'])['status']),
                            ),
                           GlassHealthCard(
                              icon: Icons.eco_sharp,
                              title: "Кислород",
                              value: '${currentData?['spo2']?.toString()}%',
                              status: '${getDescription('spo2', currentData?['spo2'])['textStatus']}',
                              description: '${getDescription('spo2', currentData?['spo2'])['result']}',
                              statusColor: getColor(getDescription('spo2', currentData?['spo2'])['status']),
                            ),
                            GlassHealthCard(
                              icon: Icons.monitor_heart,
                              title: "Пульс",
                              value: '${currentData?['pulse']?.toString()} уд/м',
                              status: '${getDescription('pulse', currentData?['pulse'])['textStatus']}',
                              description: '${getDescription('pulse', currentData?['pulse'])['result']}',
                              statusColor: getColor(getDescription('pulse', currentData?['pulse'])['status']),
                            ),
                            GlassHealthCard(
                              icon: Icons.electric_bolt_sharp,
                              title: "Стресс",
                              value: 'BCP: ${currentData?['stress']?.toString()}',
                              status: '${getDescription('stress', currentData?['stress'])['textStatus']}',
                              description: '${getDescription('stress', currentData?['stress'])['result']}',
                              statusColor: getColor(getDescription('stress', currentData?['stress'])['status']),
                            ),
                          ] : [
                            const Center(
                              child: CircularProgressIndicator(), // пока нет данных
                            )
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
        ),
      ),
    );
  }
}



class GlassHealthCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;
  final String status;
  final String description;
  final Color statusColor;

  const GlassHealthCard({
    super.key,
    required this.icon,
    required this.title,
    required this.value,
    required this.status,
    required this.description,
    required this.statusColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(18),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: Colors.white.withOpacity(0.3)),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, 3),
                ),
              ],
            ),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.3),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(icon, color: Colors.white),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        title,
                        style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 16),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: statusColor.withOpacity(0.5),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        status,
                        style: TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  value,
                  style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                      fontSize: 18),
                ),
                const SizedBox(height: 4),
                Text(
                  description,
                  style: const TextStyle(color: Colors.white70, fontSize: 13),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

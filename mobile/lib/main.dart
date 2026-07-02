import 'package:flutter/widgets.dart';  // importing flutter widgets package
import 'app/app.dart';
import 'core/di/service_locator.dart'; // service locator

Future<void> main() async{ // void to future void cause we are awaiting setupDependencies()
  WidgetsFlutterBinding.ensureInitialized(); //ensuring flutter initialized before running app.
  await setupDependencies(); // setting up dependencies for service locator
  runApp(const App()); // starting app
}
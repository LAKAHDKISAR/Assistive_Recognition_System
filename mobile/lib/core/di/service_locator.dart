import 'package:get_it/get_it.dart'; // GetIt package

final GetIt getIt = GetIt.instance; // instance of getit. final to make it initialized only once and no reassigned. getIt global variable name to access rather than GetIt.instance every time.

Future<void> setupDependencies() async {  // future so it can await for any asynconous operation. ie void can wait.
    // services 
}
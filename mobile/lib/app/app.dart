import 'package:flutter/material.dart'; // widgets packages
import 'package:mobile/app/router/app_router.dart'; //app router
import 'package:mobile/app/theme/app_theme.dart'; // theme
import 'package:mobile/core/config/app_config.dart'; // app configuration



class App extends StatelessWidget {  // app class that extends stateless widget (ie widget that doesnt change or store any data and only displays UI)
  const App({super.key});  // constructor 

  @override
  Widget build(BuildContext context) { //build method that called when need to display anything on screen.
    return MaterialApp.router(
      title: AppConfig.appName, // app name by using directly thats defined in app_config.dart file rather than hardcoding.
      debugShowCheckedModeBanner: false,  // the default debug banner on top right removed
      theme: AppTheme.light, // theme
      routerConfig: appRouter, // router to app router which will handle showing different pages of app,
    );
  }
}
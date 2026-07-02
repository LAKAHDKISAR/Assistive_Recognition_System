import 'package:flutter/material.dart'; // widgets packages
import 'package:mobile/features/home/presentation/home_page.dart'; //home page 



class App extends StatelessWidget {  // app class that extends stateless widget (ie widget that doesnt change or store any data and only displays UI)
  const App({super.key});  // constructor 

  @override
  Widget build(BuildContext context) { //build method that called when need to display anything on screen.
    return MaterialApp(
      title: 'Assistive Recognition System',
      debugShowCheckedModeBanner: false,  // the default debug banner on top right removed
      home: const HomePage(), // first screen to show when app start,
    );
  }
}
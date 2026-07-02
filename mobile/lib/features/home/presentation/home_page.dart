import 'package:flutter/material.dart'; // widgets packages

class HomePage extends StatelessWidget { //homepage extended to stateless widget
  const HomePage({super.key}); //constructor

  @override
  Widget build(BuildContext context) { // build method to display anything on screen
    return const Scaffold(
      body: Center(
        child: Text('Home'),
      ),
    );
  }
}
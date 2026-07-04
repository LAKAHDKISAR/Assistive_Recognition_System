import 'package:flutter/material.dart'; // widgets packages
import 'package:go_router/go_router.dart';

class HomePage extends StatelessWidget { //homepage extended to stateless widget
  const HomePage({super.key}); //constructor

  @override
  Widget build(BuildContext context) { // build method to display anything on screen
    return Scaffold(
      body: Center(
        child: ElevatedButton(
          onPressed: () {context.push('/camera');},
          child: const Text('Open Camera'),
        ),
      ),
    );
  }
}
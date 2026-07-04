abstract interface class CameraService { // abstract interface class that defines contracts for the camera operations (similar to abstract class but since Dart 3, we can use interface class)
    Future<void> initialize();
    Future<void> startPreview(); 
    Future<void> stopPreview();
    Future<void> dispose();
}
import "package:go_router/go_router.dart";
import "package:mobile/features/home/presentation/home_page.dart";
import "package:mobile/features/camera/presentation/pages/camera_page.dart";

final GoRouter appRouter = GoRouter(
    routes: [
      GoRoute(
        path: "/",
        builder: (context, state) => const HomePage(), // route to home page when app start
      ),
      GoRoute(
        path: "/camera",
        builder: (context, state) => const CameraPage(),
      )]
);
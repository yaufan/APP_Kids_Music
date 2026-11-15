import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/content.dart';
import '../core/providers.dart';
import '../features/band/band_screen.dart';
import '../features/freeze/freeze_screen.dart';
import '../features/highlow/highlow_screen.dart';
import '../features/listen/listen_screen.dart';
import '../features/parent/parent_gate.dart';
import '../features/parent/parent_screen.dart';
import '../features/record/record_screen.dart';
import '../features/rest/rest_screen.dart';
import '../features/stage/stage_screen.dart';
import '../features/tap/tap_screen.dart';
import 'strings.dart';
import 'theme.dart';

Widget toyScreen(Toy t) => switch (t) {
      Toy.tap => const TapScreen(),
      Toy.band => const BandScreen(),
      Toy.freeze => const FreezeScreen(),
      Toy.highlow => const HighLowScreen(),
      Toy.record => const RecordScreen(),
      Toy.listen => const ListenScreen(),
    };

final routerProvider = Provider<GoRouter>((ref) {
  final resting = ref.read(gameProvider).resting(ref.read(clockProvider)());
  final router = GoRouter(
    initialLocation: resting ? '/rest' : '/',
    // Always start here, whatever page another app asks the phone to open.
    overridePlatformDefaultLocation: true,
    // A page that does not exist: the stage.
    onException: (_, _, router) => router.go('/'),
    redirect: (_, state) {
      final at = state.matchedLocation;
      if (at == '/parent' && !ParentPass.take()) return '/';
      final name = state.pathParameters['toy'];
      if (name != null) {
        final toy = Toy.values.asNameMap()[name];
        // Unknown, turned off, or not in the free version: back to the stage.
        if (toy == null || !ref.read(gameProvider).settings.opens(toy)) return '/';
      }
      return null;
    },
    routes: [
      GoRoute(path: '/', builder: (_, _) => const StageScreen()),
      GoRoute(path: '/toy/:toy', builder: (_, s) => toyScreen(Toy.values.byName(s.pathParameters['toy']!))),
      GoRoute(path: '/rest', builder: (_, _) => const RestScreen()),
      GoRoute(path: '/parent', builder: (_, _) => const ParentScreen()),
    ],
  );
  ref.onDispose(router.dispose);
  return router;
});

class LittleWaveApp extends ConsumerWidget {
  const LittleWaveApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(gameProvider.select((g) => g.settings));
    ref.read(soundsProvider)
      ..music = settings.music
      ..effects = settings.sounds
      ..volume = settings.volume;
    return MaterialApp.router(
      title: Strings.appName,
      debugShowCheckedModeBanner: false,
      theme: NeonTheme.dark(),
      locale: const Locale('zh', 'TW'),
      supportedLocales: const [Locale('zh', 'TW')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      routerConfig: ref.watch(routerProvider),
      builder: (_, child) => RestGuard(child: child ?? const SizedBox()),
    );
  }
}

/// Keeps the parent's play time: when the sitting has gone on for the
/// minutes they set, the lights go out one by one; an hour later (or when a
/// parent says so) play can go on. Away from the app for ten minutes counts
/// as a rest. It also counts today's minutes for the parent page.
class RestGuard extends ConsumerStatefulWidget {
  const RestGuard({super.key, required this.child});

  final Widget child;

  static const check = Duration(seconds: 2);
  static const awayIsRest = Duration(minutes: 10);

  @override
  ConsumerState<RestGuard> createState() => _RestGuardState();
}

class _RestGuardState extends ConsumerState<RestGuard> {
  Timer? _timer;
  AppLifecycleListener? _life;
  DateTime? _away;
  DateTime? _counted;

  @override
  void initState() {
    super.initState();
    ref.read(sessionStartProvider);
    _counted = ref.read(clockProvider)();
    _timer = Timer.periodic(RestGuard.check, (_) => _check());
    _life = AppLifecycleListener(
      onHide: () {
        _count();
        _away = ref.read(clockProvider)();
      },
      onShow: () {
        final away = _away;
        _away = null;
        _counted = ref.read(clockProvider)();
        if (away != null && ref.read(clockProvider)().difference(away) >= RestGuard.awayIsRest) ref.read(sessionStartProvider.notifier).restart();
        _check();
      },
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    _life?.dispose();
    super.dispose();
  }

  /// Adds the minutes played since the last count (every half minute or so).
  void _count({bool force = true}) {
    final now = ref.read(clockProvider)();
    final from = _counted;
    if (from == null) return;
    final d = now.difference(from);
    if (!force && d < const Duration(seconds: 30)) return;
    _counted = now;
    if (d > Duration.zero && d < const Duration(hours: 2)) ref.read(gameProvider.notifier).change((g) => g.played(d, now));
  }

  void _check() {
    if (!mounted) return;
    final now = ref.read(clockProvider)();
    final g = ref.read(gameProvider);
    final router = ref.read(routerProvider);
    final path = router.state.matchedLocation;
    if (path.startsWith('/parent')) return;
    if (g.restSince != null) {
      _counted = now;
      if (g.resting(now)) {
        if (path != '/rest') router.go('/rest');
        return;
      }
      ref.read(gameProvider.notifier).change((g) => g.playOn());
      ref.read(sessionStartProvider.notifier).restart();
      if (path == '/rest') router.go('/');
      return;
    }
    if (path == '/rest') return;
    _count(force: false);
    if (now.difference(ref.read(sessionStartProvider)) >= Duration(minutes: g.settings.minutes)) {
      _count();
      ref.read(gameProvider.notifier).change((g) => g.rest(now));
      router.go('/rest');
    }
  }

  @override
  Widget build(BuildContext context) => widget.child;
}

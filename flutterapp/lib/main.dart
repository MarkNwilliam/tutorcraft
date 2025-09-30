import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:google_fonts/google_fonts.dart';
import 'firebase_options.dart';
import 'screens/home_screen.dart';
import 'screens/auth_screen.dart';
import 'screens/email_sign_in_screen.dart';
import 'screens/video_generation_screen.dart';
import 'screens/video_player_screen.dart';
import 'screens/paywall_screen.dart';
import 'providers/auth_provider.dart';
import 'providers/revenuecat_provider.dart';
import 'theme/app_theme.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'package:onesignal_flutter/onesignal_flutter.dart';

void main() async {
  // Ensure that widget binding is initialized
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  // Initialize RevenueCat - moved to provider for better state management
  await Purchases.configure(
    PurchasesConfiguration(
     
    )
  );

  // Initialize OneSignal for push notifications
  await _initializeOneSignal();
  
  runApp(
    const ProviderScope(
      child: TutorCraftApp(),
    ),
  );
}

// Initialize OneSignal with your App ID
Future<void> _initializeOneSignal() async {
  // Enable verbose logging for debugging (remove in production)
  OneSignal.Debug.setLogLevel(OSLogLevel.verbose);
  
  // Initialize with your OneSignal App ID
  OneSignal.initialize("");
  
  // Request notification permission (true = shows native permission dialog)
  OneSignal.Notifications.requestPermission(true);
  
    // Enable IN-APP MESSAGES (add this)
  OneSignal.InAppMessages.paused(false);

  // Set up notification click handler
  OneSignal.Notifications.addClickListener((event) {
    _handleNotificationClick(event);
  });

  // Set up foreground notification handler
  OneSignal.Notifications.addForegroundWillDisplayListener((event) {
    // You can modify the notification before it displays
    print("Notification received in foreground: ${event.notification}");
  });

    // Add in-app message click handler (optional)
  OneSignal.InAppMessages.addClickListener((event) {
    print("In-app message clicked: ${event.result}");
  });
}

// Handle notification clicks for deep linking
void _handleNotificationClick(OSNotificationClickEvent event) {
  print("Notification clicked: ${event.notification}");
  
  // Handle deep linking based on notification data
  if (event.notification.additionalData != null) {
    final data = event.notification.additionalData!;
    
    // Example: Navigate to specific tutorial
    if (data['tutorial_id'] != null) {
      print("Navigate to tutorial: ${data['tutorial_id']}");
      // You can use a navigation service or provider to handle this
    }
    
    // Example: Navigate to specific screen
    if (data['screen'] != null) {
      print("Navigate to screen: ${data['screen']}");
    }
  }
}

class TutorCraftApp extends StatelessWidget {
  const TutorCraftApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TutorCraft - AI Learning Videos',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      
      // Define named routes
      routes: {
        '/': (context) => const ConnectivityWrapper(),
        '/auth': (context) => const AuthScreen(),
        '/email-signin': (context) => const EmailSignInScreen(),
        '/home': (context) => const HomeScreen(),
        '/paywall': (context) => const PaywallScreen(),
      },
      
      // Handle unknown routes
      onUnknownRoute: (settings) {
        return MaterialPageRoute(
          builder: (context) => const ConnectivityWrapper(),
        );
      },
    );
  }
}

// Main wrapper that handles connectivity and authentication
class ConnectivityWrapper extends ConsumerWidget {
  const ConnectivityWrapper({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final revenueCatState = ref.watch(revenueCatProvider);
    
    // Show authentication loading screen
    if (authState.isLoading || revenueCatState.isLoading) {
      return const AuthLoadingScreen();
    }
    
    // Always show HomeScreen - let it handle auth internally
    return const HomeScreen();
  }
}

// Loading screen shown during initial connectivity check
class ConnectivityLoadingScreen extends StatelessWidget {
  const ConnectivityLoadingScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              theme.colorScheme.primary.withOpacity(0.1),
              theme.colorScheme.surface,
              theme.colorScheme.secondary.withOpacity(0.1),
            ],
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // App Logo/Icon
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      theme.colorScheme.primary,
                      theme.colorScheme.secondary,
                    ],
                  ),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: theme.colorScheme.primary.withOpacity(0.3),
                      blurRadius: 20,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: Icon(
                  Icons.play_circle_filled,
                  size: 40,
                  color: Colors.white,
                ),
              ),
              
              const SizedBox(height: 32),
              
              // App Name
              Text(
                'TutorCraft',
                style: theme.textTheme.headlineLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: theme.colorScheme.onSurface,
                ),
              ),
              
              const SizedBox(height: 8),
              
              Text(
                'AI-Powered Learning Videos',
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
              
              const SizedBox(height: 48),
              
              // Loading Indicator
              CircularProgressIndicator(
                strokeWidth: 3,
                color: theme.colorScheme.primary,
              ),
              
              const SizedBox(height: 24),
              
              Text(
                'Checking connection...',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.6),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// Loading screen shown during authentication and RevenueCat setup
class AuthLoadingScreen extends StatelessWidget {
  const AuthLoadingScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              theme.colorScheme.primary.withOpacity(0.1),
              theme.colorScheme.surface,
              theme.colorScheme.secondary.withOpacity(0.1),
            ],
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // App Logo/Icon
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      theme.colorScheme.primary,
                      theme.colorScheme.secondary,
                    ],
                  ),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: theme.colorScheme.primary.withOpacity(0.3),
                      blurRadius: 20,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: Icon(
                  Icons.person,
                  size: 40,
                  color: Colors.white,
                ),
              ),
              
              const SizedBox(height: 32),
              
              // App Name
              Text(
                'TutorCraft',
                style: theme.textTheme.headlineLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: theme.colorScheme.onSurface,
                ),
              ),
              
              const SizedBox(height: 48),
              
              // Loading Indicator
              CircularProgressIndicator(
                strokeWidth: 3,
                color: theme.colorScheme.primary,
              ),
              
              const SizedBox(height: 24),
              
              Text(
                'Initializing app...',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.6),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// Utility class for sending notifications from anywhere in your app
class NotificationService {
  // Send tag-based notifications (user preferences, learning level, etc.)
  static Future<void> setUserTags(Map<String, dynamic> tags) async {
    try {
      await OneSignal.User.addTags(tags);
      print("User tags set: $tags");
    } catch (e) {
      print("Error setting user tags: $e");
    }
  }

  // Example: Set user learning level
  static Future<void> setLearningLevel(String level) async {
    await setUserTags({'learning_level': level});
  }

  // Example: Set user subscription status
  static Future<void> setSubscriptionStatus(String status) async {
    await setUserTags({'subscription_status': status});
  }

  // Example: Track tutorial completion
  static Future<void> trackTutorialCompletion(String tutorialId) async {
    await setUserTags({'completed_$tutorialId': 'true'});
  }
}

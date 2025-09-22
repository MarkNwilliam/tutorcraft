import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/auth_provider.dart';
import 'home_screen.dart';
import 'email_sign_in_screen.dart';

class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends ConsumerState<AuthScreen> {
@override
void initState() {
  super.initState();
  
  // Listen to auth state changes ONLY for errors, not navigation
  WidgetsBinding.instance.addPostFrameCallback((_) {
    ref.listen<AuthState>(authProvider, (previous, next) {
      // Handle errors only - navigation is handled in EmailSignInScreen
      if (next.error != null) {
        print("❌ Auth error: ${next.error}");
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.error!),
            backgroundColor: Colors.red,
          ),
        );
        // Clear error after showing
        ref.read(authProvider.notifier).clearError();
      }
    });
  });
}

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sign In'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Logo or App Name
            Icon(
              Icons.school,
              size: 64,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 16),
            Text(
              'Welcome to TutorCraft',
              style: theme.textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Sign in to generate unlimited educational videos',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.7),
              ),
              textAlign: TextAlign.center,
            ),
            
            const SizedBox(height: 48),
            
            // Google Sign In Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: authState.isLoading 
                  ? null 
                  : () async {
                      print("🐛 Google Sign-In button pressed");
                      try {
                        // Add a small delay to ensure the loading state is visible
                        await Future.delayed(Duration(milliseconds: 100));
                        
                        final result = await ref.read(authProvider.notifier).signInWithGoogle(context);
                        print("✅ Google Sign-In completed successfully");
                        
                        // Check if we're still mounted before showing success message
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('Signed in successfully!'),
                              backgroundColor: Colors.green,
                            ),
                          );
                        }
                      } catch (e, stackTrace) {
                        print("❌ Google Sign-In error: $e");
                        print("📋 Stack trace: $stackTrace");
                        
                        // Check if we're still mounted before showing error
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('Sign-in failed: $e'),
                              backgroundColor: Colors.red,
                            ),
                          );
                        }
                      } finally {
                        print("🔚 Google Sign-In process completed");
                      }
                    },
                icon: authState.isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Image.asset(
                      'assets/images/google_logo.png',
                      width: 20,
                      height: 20,
                      errorBuilder: (context, error, stackTrace) {
                        print("⚠️ Google logo asset not found");
                        return const Icon(Icons.login, size: 20);
                      },
                    ),
                label: Text(
                  authState.isLoading 
                    ? 'Signing in...' 
                    : 'Continue with Google',
                ),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 16,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),      
            const SizedBox(height: 16),
            
            // Email Sign In Button
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
// In the AuthScreen, update the email button onPressed:
onPressed: authState.isLoading 
  ? null 
  : () async {
      print("📧 Navigating to email sign-in screen");
      // Navigate to email sign in form and wait for result
      final result = await Navigator.push<bool>(
        context,
        MaterialPageRoute(
          builder: (context) => const EmailSignInScreen(),
        ),
      );
      
      // If email sign-in was successful, close this auth screen too
      if (result == true && mounted) {
        print("✅ Email sign-in successful, closing auth screen");
        Navigator.pop(context, true); // Return to HomeScreen
      }
    },
                icon: const Icon(Icons.email_outlined, size: 20),
                label: const Text('Sign in with Email'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 16,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
            
            const SizedBox(height: 32),
            
            // Terms and Privacy
            Text(
              'By signing in, you agree to our Terms of Service and Privacy Policy',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
              textAlign: TextAlign.center,
            ),
            
            const SizedBox(height: 24),
            
            // Continue as Guest option
            TextButton(
              onPressed: () {
                Navigator.pop(context, false); // Return false for guest mode
              },
              child: Text(
                'Continue as Guest (Limited features)',
                style: TextStyle(
                  color: theme.colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}


// lib/screens/email_sign_in_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import '../providers/auth_provider.dart';
import 'package:fluttertoast/fluttertoast.dart';

class EmailSignInScreen extends ConsumerStatefulWidget {
  const EmailSignInScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<EmailSignInScreen> createState() => _EmailSignInScreenState();
}

class _EmailSignInScreenState extends ConsumerState<EmailSignInScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _nameController = TextEditingController();
  bool _isSignUp = false;
  bool _hasNavigated = false;
  bool _isPasswordVisible = false; // Added for password visibility toggle

  @override
  void initState() {
    super.initState();
    
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.listen<AuthState>(authProvider, (previous, next) {
        if (_hasNavigated) return;
        
        if (next.isAuthenticated && !_hasNavigated) {
          print("✅ Email auth successful, going back");
          _hasNavigated = true;
          
          // Show success toast
          //_showSuccessToast('Welcome! Sign in successful');
          
          // Navigate to home
          //Navigator.pushReplacementNamed(context, '/home');
        }
        
        if (next.error != null && !next.isLoading) {
          print("❌ Email auth error: ${next.error}");
          
          // Show error toast instead of snackbar
          _showErrorToast(next.error!);
          
          ref.read(authProvider.notifier).clearError();
        }
      });
    });
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  void _submitForm() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text.trim();
    
    if (email.isEmpty || password.isEmpty) {
      _showWarningToast('Please fill in all fields');
      return;
    }

    // Basic email validation
    if (!_isValidEmail(email)) {
      _showWarningToast('Please enter a valid email address');
      return;
    }

    // Password length check
    if (password.length < 6) {
      _showWarningToast('Password must be at least 6 characters');
      return;
    }

    try {
      if (_isSignUp) {
        final name = _nameController.text.trim();
        if (name.isEmpty) {
          _showWarningToast('Please enter your name');
          return;
        }
        if (name.length < 2) {
          _showWarningToast('Name must be at least 2 characters');
          return;
        }
        
        _showInfoToast('Creating your account...');
        await ref.read(authProvider.notifier).signUp(email, password, name, context );
      } else {
        _showInfoToast('Signing you in...');
        await ref.read(authProvider.notifier).signIn(email, password, context);
      }
    } catch (e) {
      print("❌ Form submission error: $e");
      _showErrorToast('Something went wrong. Please try again.');
    }
  }

  bool _isValidEmail(String email) {
    return RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(email);
  }

  // Toast helper methods
  void _showSuccessToast(String message) {
    Fluttertoast.showToast(
      msg: message,
      toastLength: Toast.LENGTH_LONG,
      gravity: ToastGravity.BOTTOM,
      timeInSecForIosWeb: 3,
      backgroundColor: Colors.green.shade700,
      textColor: Colors.white,
      fontSize: 16.0,
    );
  }

  void _showErrorToast(String message) {
    Fluttertoast.showToast(
      msg: message,
      toastLength: Toast.LENGTH_LONG,
      gravity: ToastGravity.BOTTOM,
      timeInSecForIosWeb: 4,
      backgroundColor: Colors.red.shade700,
      textColor: Colors.white,
      fontSize: 16.0,
    );
  }

  void _showWarningToast(String message) {
    Fluttertoast.showToast(
      msg: message,
      toastLength: Toast.LENGTH_SHORT,
      gravity: ToastGravity.BOTTOM,
      timeInSecForIosWeb: 2,
      backgroundColor: Colors.orange.shade700,
      textColor: Colors.white,
      fontSize: 16.0,
    );
  }

  void _showInfoToast(String message) {
    Fluttertoast.showToast(
      msg: message,
      toastLength: Toast.LENGTH_SHORT,
      gravity: ToastGravity.BOTTOM,
      timeInSecForIosWeb: 2,
      backgroundColor: Colors.blue.shade700,
      textColor: Colors.white,
      fontSize: 16.0,
    );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(_isSignUp ? 'Sign Up' : 'Sign In'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            onPressed: () {
              Navigator.pushReplacementNamed(context, '/home');
            },
            icon: const Icon(Icons.home),
            tooltip: 'Go to Home',
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: ConstrainedBox(
            constraints: BoxConstraints(
              minHeight: MediaQuery.of(context).size.height - 
                         MediaQuery.of(context).padding.top - 
                         kToolbarHeight - 48, // Account for SafeArea and padding
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // App logo or title
                Icon(
                  _isSignUp ? Icons.people : Icons.people_outline,
                  size: 64
                ),
                const SizedBox(height: 32),
                
                if (_isSignUp) ...[
                  TextField(
                    controller: _nameController,
                    decoration: const InputDecoration(
                      labelText: 'Full Name',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.person),
                    ),
                    textInputAction: TextInputAction.next,
                    enabled: !authState.isLoading,
                  ),
                  const SizedBox(height: 16),
                ],
                
                TextField(
                  controller: _emailController,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.email),
                  ),
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.next,
                  enabled: !authState.isLoading,
                ),
                
                const SizedBox(height: 16),
                
                TextField(
                  controller: _passwordController,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    border: const OutlineInputBorder(),
                    prefixIcon: const Icon(Icons.lock),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _isPasswordVisible 
                          ? Icons.visibility 
                          : Icons.visibility_off,
                      ),
                      onPressed: () {
                        setState(() {
                          _isPasswordVisible = !_isPasswordVisible;
                        });
                      },
                      tooltip: _isPasswordVisible ? 'Hide password' : 'Show password',
                    ),
                  ),
                  obscureText: !_isPasswordVisible,
                  textInputAction: TextInputAction.done,
                  enabled: !authState.isLoading,
                  onSubmitted: (_) => _submitForm(),
                ),
                
                const SizedBox(height: 24),
                
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: authState.isLoading ? null : _submitForm,
                    child: authState.isLoading
                      ? Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Text(_isSignUp ? 'Creating Account...' : 'Signing In...'),
                          ],
                        )
                      : Text(
                          _isSignUp ? 'Create Account' : 'Sign In',
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                        ),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
                
                const SizedBox(height: 16),
                
                TextButton(
                  onPressed: authState.isLoading ? null : () {
                    setState(() {
                      _isSignUp = !_isSignUp;
                      // Clear controllers when switching
                      _nameController.clear();
                      _emailController.clear();
                      _passwordController.clear();
                      // Reset password visibility when switching modes
                      _isPasswordVisible = false;
                    });
                    
                    // Show info toast about switching modes
                    _showInfoToast(_isSignUp 
                      ? 'Switched to sign up mode'
                      : 'Switched to sign in mode'
                    );
                  },
                  child: Text(
                    _isSignUp 
                      ? 'Already have an account? Sign In'
                      : 'Don\'t have an account? Sign Up',
                    style: TextStyle(
                      fontSize: 14,
          
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                
                // Optional: Add forgot password for sign in mode
                if (!_isSignUp && !authState.isLoading) ...[
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: () {
                      // Handle forgot password
                      _showInfoToast('Forgot password feature coming soon');
                    },
                    child: Text(
                      'Forgot Password?',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
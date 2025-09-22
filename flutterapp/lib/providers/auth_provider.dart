import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import 'dart:async';

// User model
class AppUser {
  final String uid;
  final String email;
  final String? displayName;
  final String? photoURL;
  final String subscription; // 'free', 'premium', 'pro'
  final DateTime createdAt;
  final DateTime? subscriptionExpiry;

  AppUser({
    required this.uid,
    required this.email,
    this.displayName,
    this.photoURL,
    this.subscription = 'free',
    required this.createdAt,
    this.subscriptionExpiry,
  });

  factory AppUser.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return AppUser(
      uid: doc.id,
      email: data['email'] ?? '',
      displayName: data['displayName'],
      photoURL: data['photoURL'],
      subscription: data['subscription'] ?? 'free',
      createdAt: (data['createdAt'] as Timestamp?)?.toDate() ?? DateTime.now(),
      subscriptionExpiry: (data['subscriptionExpiry'] as Timestamp?)?.toDate(),
    );
  }

  Map<String, dynamic> toFirestore() {
    return {
      'email': email,
      'displayName': displayName,
      'photoURL': photoURL,
      'subscription': subscription,
      'createdAt': Timestamp.fromDate(createdAt),
      'subscriptionExpiry': subscriptionExpiry != null 
        ? Timestamp.fromDate(subscriptionExpiry!)
        : null,
      'updatedAt': Timestamp.fromDate(DateTime.now()),
    };
  }

  AppUser copyWith({
    String? uid,
    String? email,
    String? displayName,
    String? photoURL,
    String? subscription,
    DateTime? createdAt,
    DateTime? subscriptionExpiry,
  }) {
    return AppUser(
      uid: uid ?? this.uid,
      email: email ?? this.email,
      displayName: displayName ?? this.displayName,
      photoURL: photoURL ?? this.photoURL,
      subscription: subscription ?? this.subscription,
      createdAt: createdAt ?? this.createdAt,
      subscriptionExpiry: subscriptionExpiry ?? this.subscriptionExpiry,
    );
  }
}

// Auth state
class AuthState {
  final AppUser? user;
  final bool isLoading;
  final String? error;

  AuthState({
    this.user,
    this.isLoading = false,
    this.error,
  });

  bool get isAuthenticated => user != null;

  AuthState copyWith({
    AppUser? user,
    bool? isLoading,
    String? error,
  }) {
    return AuthState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }
}

// Auth provider
class AuthNotifier extends StateNotifier<AuthState> {
  final FirebaseAuth _firebaseAuth;
  final FirebaseFirestore _firestore;
  bool _isGoogleSignInInitialized = false;
  Timer? _errorClearTimer; // Added for auto-clearing errors

  AuthNotifier({
    FirebaseAuth? firebaseAuth,
    FirebaseFirestore? firestore,
  })  : _firebaseAuth = firebaseAuth ?? FirebaseAuth.instance,
        _firestore = firestore ?? FirebaseFirestore.instance,
        super(AuthState()) {
    // Initialize Google Sign-In and listen to auth state changes
    _initializeGoogleSignIn();
    _firebaseAuth.authStateChanges().listen((User? user) {
      print("🔄 Auth state changed: ${user?.uid ?? 'null'}"); // Added debug print
      if (user != null) {
        print("👤 Loading user data for: ${user.email}"); // Added debug print
        _loadUserData(user.uid);
      } else {
        print("👋 User signed out, clearing state"); // Added debug print
        state = AuthState();
      }
    });
  }

  @override
  void dispose() {
    _errorClearTimer?.cancel(); // Clean up timer
    super.dispose();
  }

  // Added method to auto-clear errors
  void _setErrorWithAutoClear(String error) {
    print("❌ Setting error: $error");
    state = state.copyWith(error: error, isLoading: false);
    
    _errorClearTimer?.cancel();
    _errorClearTimer = Timer(const Duration(seconds: 3), () {
      if (mounted && state.error == error) {
        print("🧹 Auto-clearing error: $error");
        state = state.copyWith(error: null);
      }
    });
  }

  Future<void> _initializeGoogleSignIn() async {
    try {
      print("🔧 Initializing Google Sign-In..."); // Added debug print
      await GoogleSignIn.instance.initialize();
      _isGoogleSignInInitialized = true;
      print("✅ Google Sign-In initialized successfully"); // Added debug print
    } catch (e) {
      print('❌ Failed to initialize Google Sign-In: $e');
    }
  }

  Future<void> _ensureGoogleSignInInitialized() async {
    if (!_isGoogleSignInInitialized) {
      print("🔄 Google Sign-In not initialized, initializing now..."); // Added debug print
      await _initializeGoogleSignIn();
    }
  }

  Future<void> _loadUserData(String uid) async {
    try {
      print("📊 Loading user data for UID: $uid"); // Added debug print
      final doc = await _firestore.collection('users').doc(uid).get();
      if (doc.exists) {
        print("✅ User document found in Firestore"); // Added debug print
        final appUser = AppUser.fromFirestore(doc);
        state = state.copyWith(user: appUser, isLoading: false);
        print("👤 User loaded: ${appUser.email} (${appUser.subscription})"); // Added debug print
      } else {
        print("📝 User document not found, creating new one..."); // Added debug print
        // User document doesn't exist, create it
        final firebaseUser = _firebaseAuth.currentUser;
        if (firebaseUser != null) {
          final newAppUser = AppUser(
            uid: firebaseUser.uid,
            email: firebaseUser.email ?? '',
            displayName: firebaseUser.displayName,
            photoURL: firebaseUser.photoURL,
            createdAt: DateTime.now(),
          );
          await _firestore.collection('users').doc(uid).set(newAppUser.toFirestore());
          state = state.copyWith(user: newAppUser, isLoading: false);
          print("✅ New user document created: ${newAppUser.email}"); // Added debug print
        }
      }
    } catch (e) {
      print("❌ Failed to load user data: $e"); // Added debug print
      _setErrorWithAutoClear('Failed to load user data: ${e.toString()}'); // Changed to auto-clear
    }
  }

  Future<void> signUp(String email, String password, String name, BuildContext context  ) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {

      print("🚀 Starting email/password sign-up for $email")  ;
      print("📧 Creating Firebase user account..."); // Added debug print
      final credential = await _firebaseAuth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );

      print("✅ Email/Password sign-up successful for $email")  ; 


      if (credential.user != null) {
        print("🏷️ Updating display name to: $name"); // Added debug print
        // Update display name
        await credential.user!.updateDisplayName(name);
        print("✅ Updated display name to $name") ;
        // Create user document in Firestore
        final appUser = AppUser(
          uid: credential.user!.uid,
          email: email,
          displayName: name,
          createdAt: DateTime.now(),
        );
        print("📝 Creating new user document in Firestore") ;
        print("💾 Saving user document to Firestore..."); // Added debug print
        await _firestore
            .collection('users')
            .doc(credential.user!.uid)
            .set(appUser.toFirestore());

        state = state.copyWith(user: appUser, isLoading: false);
        print("✅ User document created successfully") ;  
        print("🎉 Sign-up completed successfully for: $email"); // Added debug print
        print("🧭 Navigating to home screen..."); // Added debug print
        Navigator.of(context).pushReplacementNamed('/home');
      }

      print("✅ User document created successfully"); 

       Navigator.of(context).pushReplacementNamed('/home');

    } on FirebaseAuthException catch (e) {
      print("❌ FirebaseAuthException during sign-up: ${e.code} - ${e.message}"); // Added debug print
      String errorMessage;
      switch (e.code) {
        case 'weak-password':
          errorMessage = 'The password provided is too weak.';
          break;
        case 'email-already-in-use':
          errorMessage = 'An account already exists for that email.';
          break;
        case 'invalid-email':
          errorMessage = 'The email address is not valid.';
          break;
        default:
          errorMessage = e.message ?? 'An error occurred during sign up.';
      }
      _setErrorWithAutoClear(errorMessage); // Changed to auto-clear
    } catch (e) {
      print("❌ Unexpected error during sign-up: $e"); // Added debug print
      _setErrorWithAutoClear('Unexpected error during sign up: ${e.toString()}'); // Changed to auto-clear
    }
  }

  Future<void> signIn(String email, String password , BuildContext context) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      print("🚀 Starting email/password sign-in for $email");
      print("🔐 Authenticating with Firebase..."); // Added debug print
      await _firebaseAuth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );
      // User data will be loaded automatically by authStateChanges listener

      print("✅ Email/Password sign-in successful for $email");
      print("🧭 Navigating to home screen..."); // Added debug print

      Navigator.of(context).pushReplacementNamed('/home');

    } on FirebaseAuthException catch (e) {
      print("❌ FirebaseAuthException during sign-in: ${e.code} - ${e.message}"); // Added debug print
      String errorMessage;
      switch (e.code) {
        case 'user-not-found':
          errorMessage = 'No user found for that email.';
          break;
        case 'wrong-password':
          errorMessage = 'Wrong password provided.';
          break;
        case 'invalid-email':
          errorMessage = 'The email address is not valid.';
          break;
        case 'user-disabled':
          errorMessage = 'This user account has been disabled.';
          break;
        default:
          errorMessage = e.message ?? 'An error occurred during sign in.';
      }
      _setErrorWithAutoClear(errorMessage); // Changed to auto-clear
    } catch (e) {
      print("❌ Unexpected error during sign-in: $e"); // Added debug print
      _setErrorWithAutoClear('Unexpected error during sign in: ${e.toString()}'); // Changed to auto-clear
    }
  }

  Future<void> signInWithGoogle(BuildContext? context) async { // Added context parameter
  state = state.copyWith(isLoading: true, error: null);
  
  try {
    print("🚀 Starting Google Sign-In process");
    print("🔧 Ensuring Google Sign-In is initialized..."); // Added debug print
    
    // Ensure Google Sign-In is initialized
    await _ensureGoogleSignInInitialized();
    
    print("🔄 Signing out from previous Google sessions..."); // Added debug print
    // Sign out first to force account selection
    await GoogleSignIn.instance.signOut();
    
    print("🎯 Triggering Google account selection..."); // Added debug print
    // Trigger the authentication flow
    final GoogleSignInAccount? googleUser = await GoogleSignIn.instance.authenticate();
    
    if (googleUser == null) {
      // User cancelled the sign-in
      print("⚠️ User cancelled Google Sign-In - this is normal user behavior"); // Updated debug print
      state = state.copyWith(isLoading: false);
      return; // Don't show error for cancellation
    }
    
    print("✅ Google account selected: ${googleUser.email}");
    print("👤 Google user info: ${googleUser.displayName} (${googleUser.id})"); // Added debug print

    print("🔑 Getting Google authentication tokens..."); // Added debug print
    // Obtain the auth details from the request
    final GoogleSignInAuthentication googleAuth = await googleUser.authentication;
    
    if (googleAuth.idToken == null) {
      throw Exception('Failed to get ID token from Google');
    }
    
    print("✅ Got Google authentication tokens");
    print("🔐 ID Token length: ${googleAuth.idToken?.length ?? 0}"); // Added debug print

    print("🎫 Creating Firebase credential..."); // Added debug print
    // Create a new credential with idToken only (as per Firebase docs)
    final credential = GoogleAuthProvider.credential(
      idToken: googleAuth.idToken,
    );

    print("✅ Created Firebase credential");

    print("🔥 Signing in to Firebase with Google credential..."); // Added debug print
    // Sign in to Firebase with the Google credential
    final userCredential = await _firebaseAuth.signInWithCredential(credential);
    
    print("✅ Firebase sign-in successful for UID: ${userCredential.user?.uid}");
    print("🎉 Firebase sign-in successful!"); // Added debug print
    print("👤 Firebase UID: ${userCredential.user?.uid}"); // Added debug print
    print("📧 Firebase email: ${userCredential.user?.email}"); // Added debug print
    
    if (userCredential.user != null) {
      final user = userCredential.user!;
      
      print("📋 Checking if user document exists in Firestore..."); // Added debug print
      // Check if user document exists in Firestore
      final userDoc = await _firestore.collection('users').doc(user.uid).get();
      
      if (!userDoc.exists) {
        print("📝 Creating new user document in Firestore");
        
        // Create new user document
        final appUser = AppUser(
          uid: user.uid,
          email: user.email ?? '',
          displayName: user.displayName ?? googleUser.displayName,
          photoURL: user.photoURL ?? googleUser.photoUrl,
          createdAt: DateTime.now(),
        );

        await _firestore
            .collection('users')
            .doc(user.uid)
            .set(appUser.toFirestore());
        
        print("✅ User document created successfully");
      } else {
        print("✅ Existing user document found");
      }
      
      print("📊 Loading user data from Firestore..."); // Added debug print
      // Load user data (this will update the state)
      await _loadUserData(user.uid);
      
      print("✅ User data loaded successfully");
      print("🎊 Google Sign-In completed successfully!"); // Added debug print
      
      // Added navigation to home on successful Google sign-in
      if (context != null && context.mounted) {
        print("🧭 Navigating to home screen after Google sign-in..."); // Added debug print
        Navigator.of(context).pushReplacementNamed('/home');
      }
    }
    
  } on GoogleSignInException catch (e) {
    print("❌ GoogleSignInException: ${e.code} - ${e.description}");
    
    // Don't show error for user cancellation
    if (e.code.name == 'canceled' || e.code.name == 'cancelled') {
      print("ℹ️ User cancelled Google Sign-In - no error message needed"); // Added debug print
      state = state.copyWith(isLoading: false);
      return;
    }
    
    String errorMessage;
    switch (e.code.name) {
      case 'interrupted':
        errorMessage = 'Sign-in was interrupted. Please try again.';
        break;
      case 'clientConfigurationError':
        errorMessage = 'Google Sign-In configuration error. Please contact support.';
        break;
      case 'providerConfigurationError':
        errorMessage = 'Google Sign-In is currently unavailable. Please try again later.';
        break;
      default:
        errorMessage = 'Google Sign-In failed: ${e.description ?? 'Unknown error'}';
    }
    _setErrorWithAutoClear(errorMessage); // Changed to auto-clear
  } on FirebaseAuthException catch (e) {
    print("❌ FirebaseAuthException: ${e.code} - ${e.message}");
    String errorMessage;
    switch (e.code) {
      case 'account-exists-with-different-credential':
        errorMessage = 'An account already exists with a different sign-in method.';
        break;
      case 'invalid-credential':
        errorMessage = 'The credential is invalid or has expired.';
        break;
      case 'operation-not-allowed':
        errorMessage = 'Google Sign-In is not enabled for this project.';
        break;
      default:
        errorMessage = 'Firebase authentication failed: ${e.message}';
    }
    _setErrorWithAutoClear(errorMessage); // Changed to auto-clear
  } catch (e, stackTrace) {
    print("❌ Unexpected error: $e");
    print("📋 Stack trace: $stackTrace");
    _setErrorWithAutoClear('Unexpected error during Google sign-in: ${e.toString()}'); // Changed to auto-clear
  }
}

// Debug method to test Firebase connectivity
Future<void> testFirebaseConnection() async {
  try {
    print("🔍 Testing Firebase connection...");
    
    // Test Firestore connection
    await _firestore.collection('test').doc('connection').set({
      'timestamp': Timestamp.now(),
      'test': true,
    });
    
    print("✅ Firestore connection successful");
    
    // Test current user
    final currentUser = _firebaseAuth.currentUser;
    print("👤 Current Firebase user: ${currentUser?.uid ?? 'None'}");
    print("📧 Current user email: ${currentUser?.email ?? 'None'}");
    
  } catch (e) {
    print("❌ Firebase connection test failed: $e");
  }
}
  Future<void> signOut() async {
    try {
      print("🚪 Signing out user..."); // Added debug print
      await GoogleSignIn.instance.signOut();
      await _firebaseAuth.signOut();
      state = AuthState(); // Clear user state immediately
      print("✅ Sign out completed"); // Added debug print
    } catch (e) {
      print("❌ Sign out error: $e"); // Added debug print
      _setErrorWithAutoClear('Failed to sign out: ${e.toString()}'); // Changed to auto-clear
    }
  }

  Future<void> updateSubscription(String subscription, DateTime? expiry) async {
    if (state.user == null) return;

    try {
      print("💳 Updating subscription to: $subscription"); // Added debug print
      await _firestore.collection('users').doc(state.user!.uid).update({
        'subscription': subscription,
        'subscriptionExpiry': expiry != null ? Timestamp.fromDate(expiry) : null,
        'updatedAt': Timestamp.fromDate(DateTime.now()),
      });

      state = state.copyWith(
        user: state.user!.copyWith(
          subscription: subscription,
          subscriptionExpiry: expiry,
        ),
      );
      print("✅ Subscription updated successfully"); // Added debug print
    } catch (e) {
      print("❌ Failed to update subscription: $e"); // Added debug print
      _setErrorWithAutoClear('Failed to update subscription: ${e.toString()}'); // Changed to auto-clear
    }
  }

  void clearError() {
    print("🧹 Manually clearing error"); // Added debug print
    _errorClearTimer?.cancel();
    state = state.copyWith(error: null);
  }

  // Helper method to refresh user data
  Future<void> refreshUserData() async {
    if (state.user != null) {
      print("🔄 Refreshing user data..."); // Added debug print
      await _loadUserData(state.user!.uid);
    }
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier();
});

// Additional provider for current user stream
final authStateChangesProvider = StreamProvider<User?>((ref) {
  return FirebaseAuth.instance.authStateChanges();
});

// Provider for accessing the auth notifier
final authNotifierProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier();
});
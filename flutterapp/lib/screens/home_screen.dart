import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:glassmorphism/glassmorphism.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../widgets/topic_input_card.dart';
import '../widgets/topic_templates_grid.dart';
import '../widgets/recent_videos_list.dart';
import '../widgets/category_chips.dart';
import '../widgets/premium_gate.dart';
import '../providers/auth_provider.dart';
import '../providers/revenuecat_provider.dart';
import '../providers/usage_provider.dart';
import '../screens/auth_screen.dart';
import '../screens/paywall_screen.dart';

// Import the new Firebase provider (make sure this matches your file structure)
import '../providers/video_history_provider.dart'; // Or wherever you put firebaseVideosProvider

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final GlobalKey _topicInputKey = GlobalKey();
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    // Load usage stats when screen initializes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeUserData();
    });
    debugPrint('🏠 HomeScreen initialized');
  }

  Future<void> _initializeUserData() async {
    final authState = ref.read(authProvider);
    if (authState.isAuthenticated && authState.user != null) {
      // Load usage stats for authenticated users
      final usageNotifier = ref.read(usageProvider.notifier);
      await usageNotifier.loadUsageStats(authState.user!.uid);
      
      // Set RevenueCat user ID
      final revenueCatNotifier = ref.read(revenueCatProvider.notifier);
      await revenueCatNotifier.setUserId(authState.user!.uid);
    }
  }

  // Add logout confirmation dialog
  Future<void> _showLogoutConfirmation() async {
    final theme = Theme.of(context);
    
    return showDialog<void>(
      context: context,
      barrierDismissible: true,
      builder: (BuildContext context) {
        return AlertDialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          title: Row(
            children: [
              Icon(
                LucideIcons.logOut,
                color: theme.colorScheme.error,
                size: 24,
              ),
              const SizedBox(width: 12),
              const Text('Sign Out'),
            ],
          ),
          content: const Text(
            'Are you sure you want to sign out? You can always sign back in to access your videos.',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                debugPrint('🔐 Logout cancelled');
              },
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                Navigator.of(context).pop();
                debugPrint('🔐 Logout confirmed - signing out...');
                
                try {
                  // Logout from RevenueCat first
                  final revenueCatNotifier = ref.read(revenueCatProvider.notifier);
                  await revenueCatNotifier.logout();
                  
                  // Then logout from Firebase
                  await ref.read(authProvider.notifier).signOut();
                  
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: const Row(
                          children: [
                            Icon(LucideIcons.check, color: Colors.white, size: 20),
                            SizedBox(width: 8),
                            Text('Successfully signed out'),
                          ],
                        ),
                        backgroundColor: Colors.green,
                        behavior: SnackBarBehavior.floating,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    );
                  }
                  debugPrint('✅ Successfully signed out');
                } catch (error) {
                  debugPrint('❌ Error signing out: $error');
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Row(
                          children: [
                            const Icon(LucideIcons.alertCircle, color: Colors.white, size: 20),
                            const SizedBox(width: 8),
                            Expanded(child: Text('Failed to sign out: $error')),
                          ],
                        ),
                        backgroundColor: Colors.red,
                        behavior: SnackBarBehavior.floating,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    );
                  }
                }
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: theme.colorScheme.error,
                foregroundColor: theme.colorScheme.onError,
              ),
              child: const Text('Sign Out'),
            ),
          ],
        );
      },
    );
  }

  // Add user menu bottom sheet
  void _showUserMenu() {
    final authState = ref.read(authProvider);
    final user = authState.user;
    final isPremium = ref.read(isPremiumProvider);
    final usageState = ref.read(usageProvider);
    
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: BoxDecoration(
          color: Theme.of(context).scaffoldBackgroundColor,
          borderRadius: const BorderRadius.vertical(
            top: Radius.circular(20),
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Handle bar
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 24),
              
              // User info with premium status
              Row(
                children: [
                  Stack(
                    children: [
                      CircleAvatar(
                        radius: 30,
                        backgroundColor: Theme.of(context).colorScheme.primary,
                        backgroundImage: user?.photoURL != null 
                          ? NetworkImage(user!.photoURL!)
                          : null,
                        child: user?.photoURL == null 
                          ? Text(
                              (user?.displayName?.isNotEmpty == true
                                ? user!.displayName![0].toUpperCase()
                                : user?.email?.isNotEmpty == true
                                  ? user!.email![0].toUpperCase()
                                  : 'U'),
                              style: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                                color: Theme.of(context).colorScheme.onPrimary,
                              ),
                            )
                          : null,
                      ),
                      if (isPremium)
                        Positioned(
                          bottom: 0,
                          right: 0,
                          child: Container(
                            padding: const EdgeInsets.all(2),
                            decoration: BoxDecoration(
                              color: Colors.orange,
                              shape: BoxShape.circle,
                              border: Border.all(
                                color: Theme.of(context).scaffoldBackgroundColor,
                                width: 2,
                              ),
                            ),
                            child: const Icon(
                              LucideIcons.crown,
                              size: 14,
                              color: Colors.white,
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                user?.displayName ?? 'User',
                                style: Theme.of(context).textTheme.titleLarge,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            PremiumStatusIndicator(),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          user?.email ?? 'No email',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (!isPremium) ...[
                          const SizedBox(height: 8),
                          Text(
                            'Videos used: ${usageState.currentUsage}/5 this month',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: usageState.currentUsage >= 5 
                                  ? Colors.red 
                                  : Theme.of(context).colorScheme.primary,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
              
              const SizedBox(height: 24),

Expanded(
  child: SingleChildScrollView(
    child: Column(
      children: [
              // Premium upgrade section for free users
              if (!isPremium) ...[
                
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Theme.of(context).colorScheme.primary.withOpacity(0.1),
                        Theme.of(context).colorScheme.secondary.withOpacity(0.1),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
                    ),
                  ),
                 
        
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Icon(
                            LucideIcons.crown,
                            color: Theme.of(context).colorScheme.primary,
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'Upgrade to Premium',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Get unlimited videos, HD quality, and premium features',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
                        ),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: () {
                            Navigator.pop(context);
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const PaywallScreen(),
                              ),
                            );
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Theme.of(context).colorScheme.primary,
                            foregroundColor: Colors.white,
                          ),
                          child: const Text('Upgrade Now',
                           style: TextStyle(color: Colors.white)
                           ),
                        ),
                      ),
                    ],
                  ),
                   
                  
                ),

                const SizedBox(height: 16),
              ],
                    ],
    ),
  ),
),

              const Divider(),
              
              ListTile(
                leading: Icon(
                  LucideIcons.logOut,
                  color: Theme.of(context).colorScheme.error,
                ),
                title: Text(
                  'Sign Out',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.error,
                  ),
                ),
                subtitle: const Text('Sign out of your account'),
                onTap: () {
                  Navigator.pop(context);
                  _showLogoutConfirmation();
                },
              ),
              
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final authState = ref.watch(authProvider);
    final isPremium = ref.watch(isPremiumProvider);
    final usageState = ref.watch(usageProvider);
    
    // Watch the NEW Firebase videos provider instead of the old videoProvider
    final videosAsync = ref.watch(firebaseVideosProvider);
    
    // Get the actual list of videos from the async value
    final videos = videosAsync.valueOrNull ?? [];
    
    debugPrint('🏠 Building HomeScreen - Auth: ${authState.isAuthenticated}, Videos: ${videos.length}, Premium: $isPremium, Usage: ${usageState.currentUsage}/5');

    return Scaffold(
      body: CustomScrollView(
        controller: _scrollController,
        slivers: [
          // Beautiful App Bar with glassmorphism - FIXED OVERFLOW HERE
          SliverAppBar(
            expandedHeight: 200,
            floating: true,
            pinned: true,
            backgroundColor: Colors.transparent,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      theme.colorScheme.primary.withOpacity(0.8),
                      theme.colorScheme.secondary.withOpacity(0.6),
                    ],
                  ),
                ),
                child: SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // FIXED: Wrapped Row with proper constraints to prevent overflow
                        LayoutBuilder(
                          builder: (context, constraints) {
                            return Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                // FIXED: Use Expanded to prevent text overflow
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        'TutorCraft',
                                        style: theme.textTheme.displayLarge?.copyWith(
                                          color: Colors.white,
                                          fontWeight: FontWeight.bold,
                                        ),
                                        overflow: TextOverflow.ellipsis,
                                        maxLines: 1,
                                      ).animate().fadeIn().slideX(),
                                      const SizedBox(height: 4),
                                      // FIXED: Constrained subtitle text
                                      ConstrainedBox(
                                        constraints: BoxConstraints(
                                          maxWidth: constraints.maxWidth * 0.75, // 75% of available width
                                        ),
                                        child: Text(
                                          authState.isAuthenticated 
                                            ? 'Welcome back, ${authState.user?.displayName ?? 'User'}!'
                                            : 'AI-Powered Learning Videos',
                                          style: theme.textTheme.bodyLarge?.copyWith(
                                            color: Colors.white.withOpacity(0.9),
                                          ),
                                          overflow: TextOverflow.ellipsis,
                                          maxLines: 2,
                                        ).animate().fadeIn(delay: 200.ms).slideX(),
                                      ),
                                    ],
                                  ),
                                ),
                                // FIXED: Add spacing and constrain icon container
                                const SizedBox(width: 12),
                                SizedBox(
                                  width: 50,
                                  height: 50,
                                  child: GestureDetector(
                                    onTap: authState.isAuthenticated ? _showUserMenu : null,
                                    child: GlassmorphicContainer(
                                      width: 50,
                                      height: 50,
                                      borderRadius: 25,
                                      blur: 10,
                                      alignment: Alignment.center,
                                      border: 2,
                                      linearGradient: LinearGradient(
                                        colors: [
                                          Colors.white.withOpacity(0.2),
                                          Colors.white.withOpacity(0.1),
                                        ],
                                      ),
                                      borderGradient: LinearGradient(
                                        colors: [
                                          Colors.white.withOpacity(0.3),
                                          Colors.white.withOpacity(0.1),
                                        ],
                                      ),
                                      child: Stack(
                                        alignment: Alignment.center,
                                        children: [
                                          authState.isAuthenticated && authState.user?.photoURL != null
                                            ? ClipRRect(
                                                borderRadius: BorderRadius.circular(25),
                                                child: Image.network(
                                                  authState.user!.photoURL!,
                                                  width: 40,
                                                  height: 40,
                                                  fit: BoxFit.cover,
                                                  errorBuilder: (context, error, stackTrace) {
                                                    return Icon(
                                                      LucideIcons.user,
                                                      color: Colors.white,
                                                      size: 24,
                                                    );
                                                  },
                                                ),
                                              )
                                            : Icon(
                                                authState.isAuthenticated 
                                                  ? LucideIcons.user
                                                  : LucideIcons.sparkles,
                                                color: Colors.white,
                                                size: 24,
                                              ),
                                          // Premium crown indicator
                                          if (authState.isAuthenticated && isPremium)
                                            Positioned(
                                              top: 2,
                                              right: 2,
                                              child: Container(
                                                padding: const EdgeInsets.all(2),
                                                decoration: BoxDecoration(
                                                  color: Colors.orange,
                                                  shape: BoxShape.circle,
                                                  border: Border.all(
                                                    color: Colors.white,
                                                    width: 1,
                                                  ),
                                                ),
                                                child: const Icon(
                                                  LucideIcons.crown,
                                                  size: 8,
                                                  color: Colors.white,
                                                ),
                                              ),
                                            ),
                                        ],
                                      ),
                                    ),
                                  ).animate().scale(delay: 400.ms),
                                ),
                              ],
                            );
                          },
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
          
          // Main content
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Usage limit warning for free users
                  if (authState.isAuthenticated && !isPremium && usageState.currentUsage >= 4) ...[
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: usageState.currentUsage >= 5 ? Colors.red.withOpacity(0.1) : Colors.orange.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: usageState.currentUsage >= 5 ? Colors.red.withOpacity(0.3) : Colors.orange.withOpacity(0.3),
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            usageState.currentUsage >= 5 ? LucideIcons.alertTriangle : LucideIcons.clock,
                            color: usageState.currentUsage >= 5 ? Colors.red : Colors.orange,
                            size: 20,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  usageState.currentUsage >= 5 
                                      ? 'Monthly Limit Reached' 
                                      : 'Almost at Limit',
                                  style: theme.textTheme.titleSmall?.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: usageState.currentUsage >= 5 ? Colors.red : Colors.orange,
                                  ),
                                ),
                                Text(
                                  usageState.currentUsage >= 5 
                                      ? 'You\'ve used all 5 free videos this month'
                                      : 'You have ${5 - usageState.currentUsage} video${5 - usageState.currentUsage == 1 ? '' : 's'} left',
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    color: theme.colorScheme.onSurface.withOpacity(0.7),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          ElevatedButton(
                            onPressed: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => const PaywallScreen(),
                                ),
                              );
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: theme.colorScheme.primary,
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                            ),
                            child: Text(
                              'Upgrade',
                              style: theme.textTheme.labelMedium?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ).animate().fadeIn().slideY(begin: -0.2),
                    const SizedBox(height: 16),
                  ],

                  // Topic Input Card with key for scrolling
                  Container(
                    key: _topicInputKey,
                    child: authState.isAuthenticated && !isPremium && usageState.currentUsage >= 5
                        ? PremiumGate(
                            title: 'Generate More Videos',
                            description: 'You\'ve reached your monthly limit of 5 free videos. Upgrade to premium for unlimited video generation.',
                            icon: LucideIcons.video,
                            child: const TopicInputCard(),
                          )
                        : const TopicInputCard(),
                  ).animate().fadeIn(delay: 600.ms).slideY(begin: 0.2, end: 0),
                  
                  const SizedBox(height: 32),
                  
                  // Categories
                  Text(
                    'Explore Categories',
                    style: theme.textTheme.headlineMedium,
                  ).animate().fadeIn(delay: 800.ms),
                  
                  const SizedBox(height: 16),
                  const CategoryChips()
                      .animate()
                      .fadeIn(delay: 900.ms),
                  
                  const SizedBox(height: 32),
                  
                  // Topic Templates
                  Text(
                    'Quick Start Templates',
                    style: theme.textTheme.headlineMedium,
                  ).animate().fadeIn(delay: 1000.ms),
                  
                  const SizedBox(height: 16),
                  TopicTemplatesGrid(
                    onTemplateSelected: _handleTemplateSelection,
                  ),
                  
                  const SizedBox(height: 32),
                  
                  // Premium features showcase for free users
                  if (authState.isAuthenticated && !isPremium) ...[
                    Text(
                      'Premium Features',
                      style: theme.textTheme.headlineMedium,
                    ).animate().fadeIn(delay: 1100.ms),
                    
                    const SizedBox(height: 16),
                    
                    Column(
                      children: [
                        PremiumFeatureCard(
                          title: 'HD Video Generation',
                          description: 'Generate high-definition videos with advanced AI models',
                          icon: LucideIcons.video,
                        ),
                        const SizedBox(height: 8),
                        PremiumFeatureCard(
                          title: 'Unlimited Videos',
                          description: 'Generate as many videos as you want every month',
                          icon: LucideIcons.infinity,
                        ),
                        const SizedBox(height: 8),
                        PremiumFeatureCard(
                          title: 'Priority Support',
                          description: 'Get help when you need it with priority customer support',
                          icon: LucideIcons.headphones,
                        ),
                      ],
                    ).animate().fadeIn(delay: 1150.ms),
                    
                    const SizedBox(height: 32),
                  ],
                  
                  // Recent Videos Section - FIXED OVERFLOW HERE
                  LayoutBuilder(
                    builder: (context, constraints) {
                      return Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          // FIXED: Use Flexible to prevent text overflow
                          Flexible(
                            flex: 3,
                            child: Text(
                              'Recently Generated',
                              style: theme.textTheme.headlineMedium,
                              overflow: TextOverflow.ellipsis,
                              maxLines: 1,
                            ),
                          ),
                          // FIXED: Add spacing and constrain button
                          if (authState.isAuthenticated && videos.isNotEmpty) ...[
                            const SizedBox(width: 8),
                            Flexible(
                              flex: 1,
                              child: TextButton.icon(
                                onPressed: () {
                                  debugPrint('📋 View All videos pressed');
                                  // Navigate to full video history
                                  // TODO: Add navigation to video history screen
                                },
                                icon: const Icon(LucideIcons.history, size: 16),
                                label: const Text(
                                  'View All',
                                  overflow: TextOverflow.ellipsis,
                                ),
                                style: TextButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 8,
                                    vertical: 4,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ],
                      );
                    },
                  ).animate().fadeIn(delay: 1200.ms),
                  
                  const SizedBox(height: 16),
                  
                  // Recent Videos Content with Auth Checks
                  _buildRecentVideosSection(context, authState, videosAsync, videos)
                      .animate()
                      .fadeIn(delay: 1300.ms),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _handleTemplateSelection(String templateTitle) {
    print('📋 Template selected: $templateTitle');
    
    // Optional: If you want to set the text in the TopicInputCard
    // You'd need to create a way to access the TopicInputCard's setTopicText method
    // For now, the template grid handles its own navigation
  }

  Widget _buildRecentVideosSection(BuildContext context, AuthState authState, 
      AsyncValue<List<FirebaseVideo>> videosAsync, List<FirebaseVideo> videos) {
    final theme = Theme.of(context);
    
    debugPrint('📊 Building recent videos section - Auth: ${authState.isAuthenticated}, Videos count: ${videos.length}');

    // Case 1: User not authenticated
    if (!authState.isAuthenticated) {
      debugPrint('🔒 User not authenticated, showing sign-in prompt');
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: theme.colorScheme.outline.withOpacity(0.2),
          ),
          color: theme.colorScheme.surface.withOpacity(0.5),
        ),
        child: Column(
          children: [
            Icon(
              LucideIcons.lock,
              size: 48,
              color: theme.colorScheme.onSurface.withOpacity(0.6),
            ),
            const SizedBox(height: 16),
            Text(
              'Sign in to view your videos',
              style: theme.textTheme.titleMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.8),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Create an account or sign in to access your previously generated learning videos.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: () {
                _showAuthBottomSheet(context);
              },
              icon: const Icon(LucideIcons.logIn),
              label: const Text('Sign In'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 12,
                ),
              ),
            ),
          ],
        ),
      );
    }
    
    // Case 2: Loading state
    if (videosAsync.isLoading) {
      debugPrint('⏳ Videos are loading...');
      return Container(
        padding: const EdgeInsets.all(24),
        child: Center(
          child: Column(
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              Text(
                'Loading your videos...',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withOpacity(0.6),
                ),
              ),
            ],
          ),
        ),
      );
    }
    
    // Case 3: Error state
    if (videosAsync.hasError) {
      debugPrint('❌ Error loading videos: ${videosAsync.error}');
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: Colors.red.withOpacity(0.3),
          ),
          color: Colors.red.withOpacity(0.1),
        ),
        child: Column(
          children: [
            Icon(
              LucideIcons.alertCircle,
              size: 48,
              color: Colors.red,
            ),
            const SizedBox(height: 16),
            Text(
              'Failed to load videos',
              style: theme.textTheme.titleMedium?.copyWith(
                color: Colors.red,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'There was an error loading your videos. Please try again.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: () {
                debugPrint('🔄 Retrying video load...');
                ref.refresh(firebaseVideosProvider);
              },
              icon: const Icon(LucideIcons.refreshCw),
              label: const Text('Try Again'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
              ),
            ),
          ],
        ),
      );
    }
    
    // Case 4: User authenticated but no videos
    if (videos.isEmpty) {
      debugPrint('📭 User authenticated but no videos found');
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: theme.colorScheme.outline.withOpacity(0.2),
          ),
          color: theme.colorScheme.surface.withOpacity(0.5),
        ),
        child: Column(
          children: [
            Icon(
              LucideIcons.video,
              size: 48,
              color: theme.colorScheme.onSurface.withOpacity(0.6),
            ),
            const SizedBox(height: 16),
            Text(
              'No videos yet',
              style: theme.textTheme.titleMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.8),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Start by generating your first learning video using the topic input above or choose from our templates.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      );
    }
    
    // Case 5: User authenticated and has videos
    debugPrint('✅ Showing ${videos.length} videos in list');
    return const RecentVideosList();
  }

  void _showAuthBottomSheet(BuildContext context) {
    debugPrint('🔐 Showing auth bottom sheet');
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.7,
        decoration: BoxDecoration(
          color: Theme.of(context).scaffoldBackgroundColor,
          borderRadius: const BorderRadius.vertical(
            top: Radius.circular(20),
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              // Handle bar
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 24),
              
              Text(
                'Welcome to TutorCraft',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 16),
              
              Text(
                'Sign in to save and access your generated learning videos across all your devices.',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
              
              const SizedBox(height: 32),
              
              // Google Sign In Button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton.icon(
                  onPressed: () async {
                    debugPrint('🔐 Google sign-in initiated');
                    Navigator.pop(context);
                    try {
                      await ref.read(authProvider.notifier).signInWithGoogle(context);
                      // Initialize user data after successful sign in
                      await _initializeUserData();
                    } catch (e) {
                      debugPrint('Google sign-in error: $e');
                    }
                  },
                  icon: const Icon(LucideIcons.mail),
                  label: const Text('Continue with Google'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.primary,
                    foregroundColor: Theme.of(context).colorScheme.onPrimary,
                  ),
                ),
              ),
              
              const SizedBox(height: 16),
              
              // Email Sign In Button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: OutlinedButton.icon(
                  onPressed: () {
                    debugPrint('🔐 Email sign-in initiated');
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const AuthScreen(),
                      ),
                    );
                  },
                  icon: const Icon(LucideIcons.user),
                  label: const Text('Sign in with Email'),
                ),
              ),
              
              const SizedBox(height: 24),
              
              Text(
                'By signing in, you agree to our Terms of Service and Privacy Policy.',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
                ),
              ),
              
              const Spacer(),
              
              TextButton(
                onPressed: () {
                  debugPrint('🔐 Auth cancelled');
                  Navigator.pop(context);
                },
                child: const Text('Maybe Later'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    debugPrint('🏠 HomeScreen disposed');
    super.dispose();
  }
}
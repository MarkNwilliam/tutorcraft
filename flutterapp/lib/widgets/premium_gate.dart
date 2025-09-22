// lib/widgets/premium_gate.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/revenuecat_provider.dart';
import '../screens/paywall_screen.dart';

/// A widget that gates content behind a premium subscription
/// Displays premium content if user is subscribed, otherwise shows a fallback UI
class PremiumGate extends ConsumerWidget {
  final Widget child;
  final Widget? fallback;
  final String? title;
  final String? description;
  final IconData? icon;
  final bool showButton;

  const PremiumGate({
    Key? key,
    required this.child,
    this.fallback,
    this.title,
    this.description,
    this.icon,
    this.showButton = true,
  }) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isPremium = ref.watch(isPremiumProvider);

    // Return the premium content if user has active subscription
    if (isPremium) {
      return child;
    }

    // Return custom fallback or default premium gate UI
    return fallback ?? _buildDefaultFallback(context);
  }

  /// Builds the default premium gate UI when no custom fallback is provided
  Widget _buildDefaultFallback(BuildContext context) {
    final theme = Theme.of(context);
    
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            theme.colorScheme.primary.withOpacity(0.05),
            theme.colorScheme.secondary.withOpacity(0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: theme.colorScheme.outline.withOpacity(0.2),
        ),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Premium icon with gradient background
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  theme.colorScheme.primary,
                  theme.colorScheme.secondary,
                ],
              ),
              shape: BoxShape.circle,
            ),
            child: Icon(
              icon ?? Icons.workspace_premium,
              size: 32,
              color: Colors.white,
            ),
          ),
          
          const SizedBox(height: 16),
          
          // Title
          Text(
            title ?? 'Premium Feature',
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          
          const SizedBox(height: 8),
          
          // Description
          Text(
            description ?? 'This feature is available with premium subscription',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withOpacity(0.7),
            ),
            textAlign: TextAlign.center,
          ),
          
          // Upgrade button (optional)
          if (showButton) ...[
            const SizedBox(height: 20),
            
            ElevatedButton(
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (context) => const PaywallScreen(),
                  ),
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: theme.colorScheme.primary,
                padding: const EdgeInsets.symmetric(
                  horizontal: 32,
                  vertical: 12,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(25),
                ),
              ),
              child: Text(
                'Upgrade to Premium',
                style: theme.textTheme.titleMedium?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// A card widget for displaying premium features in lists
/// Automatically handles premium status and navigation to paywall
class PremiumFeatureCard extends ConsumerWidget {
  final String title;
  final String description;
  final IconData icon;
  final VoidCallback? onTap;

  const PremiumFeatureCard({
    Key? key,
    required this.title,
    required this.description,
    required this.icon,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isPremium = ref.watch(isPremiumProvider);

    return Card(
      elevation: 2,
      child: InkWell(
        onTap: isPremium ? onTap : () {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (context) => const PaywallScreen(),
            ),
          );
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Feature icon with conditional styling
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  gradient: isPremium 
                      ? LinearGradient(
                          colors: [
                            theme.colorScheme.primary,
                            theme.colorScheme.secondary,
                          ],
                        )
                      : LinearGradient(
                          colors: [
                            theme.colorScheme.outline.withOpacity(0.3),
                            theme.colorScheme.outline.withOpacity(0.1),
                          ],
                        ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  icon,
                  color: isPremium ? Colors.white : theme.colorScheme.outline,
                ),
              ),
              
              const SizedBox(width: 16),
              
              // Feature details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          title,
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                            color: isPremium 
                                ? theme.colorScheme.onSurface
                                : theme.colorScheme.onSurface.withOpacity(0.6),
                          ),
                        ),
                        // Premium badge for locked features
                        if (!isPremium) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 6,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: theme.colorScheme.primary.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              'PRO',
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: theme.colorScheme.primary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                    Text(
                      description,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: isPremium
                            ? theme.colorScheme.onSurface.withOpacity(0.7)
                            : theme.colorScheme.onSurface.withOpacity(0.5),
                      ),
                    ),
                  ],
                ),
              ),
              
              // Chevron indicator
              Icon(
                Icons.chevron_right,
                color: isPremium
                    ? theme.colorScheme.onSurface.withOpacity(0.5)
                    : theme.colorScheme.outline,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// A small badge indicator for premium features or status
class PremiumBadge extends StatelessWidget {
  final double size;
  final Color? color;

  const PremiumBadge({
    Key? key,
    this.size = 20,
    this.color,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            color ?? theme.colorScheme.primary,
            color?.withOpacity(0.7) ?? theme.colorScheme.secondary,
          ],
        ),
        shape: BoxShape.circle,
      ),
      child: Icon(
        Icons.star,
        size: size * 0.6,
        color: Colors.white,
      ),
    );
  }
}

/// Displays the current premium subscription status with visual indicators
class PremiumStatusIndicator extends ConsumerWidget {
  const PremiumStatusIndicator({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final isPremium = ref.watch(isPremiumProvider);
    final revenueCatState = ref.watch(revenueCatProvider);

    // Show loading indicator while checking subscription status
    if (revenueCatState.isLoading) {
      return const SizedBox(
        width: 16,
        height: 16,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isPremium 
            ? theme.colorScheme.primary.withOpacity(0.1)
            : theme.colorScheme.outline.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isPremium ? Icons.workspace_premium : Icons.lock,
            size: 14,
            color: isPremium 
                ? theme.colorScheme.primary
                : theme.colorScheme.outline,
          ),
          const SizedBox(width: 4),
          Text(
            isPremium ? 'Premium' : 'Free',
            style: theme.textTheme.labelSmall?.copyWith(
              color: isPremium 
                  ? theme.colorScheme.primary
                  : theme.colorScheme.outline,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
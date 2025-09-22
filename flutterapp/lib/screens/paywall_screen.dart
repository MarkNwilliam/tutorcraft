import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_ui_flutter/purchases_ui_flutter.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import '../constant.dart';
import '../providers/auth_provider.dart'; // Import your auth provider

class PaywallScreen extends ConsumerWidget {
  final bool showCloseButton;
  final VoidCallback? onPurchaseSuccess;

  const PaywallScreen({
    Key? key,
    this.showCloseButton = true,
    this.onPurchaseSuccess,
  }) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return PaywallView(
      displayCloseButton: showCloseButton,
      onPurchaseStarted: (Package package) {
        debugPrint('Purchase started for package: ${package.identifier}');
      },
      onPurchaseCompleted: (CustomerInfo customerInfo, StoreTransaction storeTransaction) async {
        debugPrint('Purchase completed: ${customerInfo.entitlements}');
        debugPrint('Store transaction: ${storeTransaction.transactionIdentifier}');
        
        // Check if user now has the entitlement
        final hasEntitlement = customerInfo.entitlements.all[entitlementID]?.isActive ?? false;
        
        if (hasEntitlement) {
          try {
            // Get the entitlement expiry date
            final entitlement = customerInfo.entitlements.all[entitlementID];
            
            // Update Firebase user subscription status
            final authNotifier = ref.read(authProvider.notifier);
            DateTime? expiryDate = entitlement?.expirationDate != null 
    ? DateTime.parse(entitlement!.expirationDate.toString()) 
    : null;
            await authNotifier.updateSubscription(
              'premium', 
              expiryDate, // Direct access to DateTime?
            );
            
           // debugPrint('Firebase subscription updated: premium, expires: ${expiryDate ?? "never"}');
            
            onPurchaseSuccess?.call();
            Navigator.of(context).pop();
            
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Welcome to Premium! You now have unlimited video generation!'),
                backgroundColor: Colors.green,
                duration: Duration(seconds: 4),
              ),
            );
          } catch (e) {
            debugPrint('Error updating subscription in Firebase: $e');
            // Still show success since RevenueCat purchase succeeded
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Purchase successful! Please restart the app if premium features don\'t appear immediately.'),
                backgroundColor: Colors.orange,
                duration: Duration(seconds: 5),
              ),
            );
          }
        }
      },
      onPurchaseError: (PurchasesError error) {
        debugPrint('Purchase error: ${error.message}');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Purchase failed: ${error.message}'),
            backgroundColor: Colors.red,
          ),
        );
      },
      onRestoreCompleted: (CustomerInfo customerInfo) async {
        debugPrint('Restore completed: ${customerInfo.entitlements}');
        // Check if restore was successful
        final hasEntitlement = customerInfo.entitlements.all[entitlementID]?.isActive ?? false;
        
        if (hasEntitlement) {
          try {
            // Get the entitlement expiry date
            final entitlement = customerInfo.entitlements.all[entitlementID];
            final expiryDate = entitlement?.expirationDate;
            
            // Update Firebase user subscription status
            final authNotifier = ref.read(authProvider.notifier);
            DateTime date = DateTime.parse(expiryDate.toString());
            await authNotifier.updateSubscription(
              'premium', 
              date,
            );
            
            debugPrint('Firebase subscription restored: premium, expires: ${expiryDate ?? "never"}');
            
            Navigator.of(context).pop();
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Premium subscription restored! You have unlimited video generation!'),
                backgroundColor: Colors.green,
                duration: Duration(seconds: 4),
              ),
            );
          } catch (e) {
            debugPrint('Error updating restored subscription in Firebase: $e');
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Subscription restored! Please restart the app if premium features don\'t appear immediately.'),
                backgroundColor: Colors.orange,
                duration: Duration(seconds: 5),
              ),
            );
          }
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('No premium purchases found to restore.'),
              backgroundColor: Colors.orange,
            ),
          );
        }
      },
      onRestoreError: (PurchasesError error) {
        debugPrint('Restore error: ${error.message}');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Restore failed: ${error.message}'),
            backgroundColor: Colors.red,
          ),
        );
      },
      onDismiss: () {
        debugPrint('Paywall dismissed');
        Navigator.of(context).pop();
      },
    );
  }
}

// Utility function to show paywall using RevenueCatUI.presentPaywall()
Future<void> presentPaywall(BuildContext context, {String? entitlementId}) async {
  final paywallResult = await RevenueCatUI.presentPaywall(
    displayCloseButton: true,
  );
  
  debugPrint('Paywall result: $paywallResult');
  
  _handlePaywallResult(context, paywallResult, entitlementId);
}

// Utility function to show paywall only if needed using RevenueCatUI.presentPaywallIfNeeded()
Future<void> presentPaywallIfNeeded(BuildContext context, {String? entitlementId}) async {
  final entitlementIdentifier = entitlementId ?? entitlementID;
  final paywallResult = await RevenueCatUI.presentPaywallIfNeeded(
    entitlementIdentifier,
    displayCloseButton: true,
  );
  
  debugPrint('Paywall result: $paywallResult');
  
  _handlePaywallResult(context, paywallResult, entitlementIdentifier);
}

// Helper function to handle paywall results
void _handlePaywallResult(BuildContext context, PaywallResult result, String? entitlementId) {
  switch (result) {
    case PaywallResult.notPresented:
      debugPrint('Paywall was not presented - user likely already has premium');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('You already have premium access!'),
          backgroundColor: Colors.green,
        ),
      );
      break;
    case PaywallResult.cancelled:
      debugPrint('User cancelled the paywall');
      break;
    case PaywallResult.error:
      debugPrint('Error presenting paywall');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Error loading paywall'),
          backgroundColor: Colors.red,
        ),
      );
      break;
    case PaywallResult.purchased:
      debugPrint('Purchase completed through presentPaywall');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Welcome to Premium! You now have unlimited video generation!'),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 4),
        ),
      );
      break;
    case PaywallResult.restored:
      debugPrint('Purchases restored through presentPaywall');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Premium subscription restored successfully!'),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 4),
        ),
      );
      break;
  }
}
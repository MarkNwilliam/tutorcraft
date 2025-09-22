// lib/providers/revenuecat_provider.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

// State class for RevenueCat
class RevenueCatState {
  final bool isLoading;
  final List<Package> availablePackages;
  final CustomerInfo? customerInfo;
  final String? error;
  final bool isPremium;

  const RevenueCatState({
    this.isLoading = false,
    this.availablePackages = const [],
    this.customerInfo,
    this.error,
    this.isPremium = false,
  });

  RevenueCatState copyWith({
    bool? isLoading,
    List<Package>? availablePackages,
    CustomerInfo? customerInfo,
    String? error,
    bool? isPremium,
  }) {
    return RevenueCatState(
      isLoading: isLoading ?? this.isLoading,
      availablePackages: availablePackages ?? this.availablePackages,
      customerInfo: customerInfo ?? this.customerInfo,
      error: error,
      isPremium: isPremium ?? this.isPremium,
    );
  }
}

// RevenueCat Provider
class RevenueCatNotifier extends StateNotifier<RevenueCatState> {
  RevenueCatNotifier() : super(const RevenueCatState()) {
    _initialize();
  }

  static const String _entitlementId = 'premium'; // Your entitlement ID
  static const String _offeringId = 'default'; // Your offering ID

  Future<void> _initialize() async {
    try {
      state = state.copyWith(isLoading: true, error: null);
      
      // Configure RevenueCat
      await Purchases.configure(
        PurchasesConfiguration('goog_FfaRxAOFqolncdeWgvmtLOGvFmR'),
      );

      // Set up listener for customer info updates
      Purchases.addCustomerInfoUpdateListener(_onCustomerInfoUpdate);

      // Get initial customer info
      await refreshCustomerInfo();
      
      // Get available packages
      await getOfferings();
      
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to initialize RevenueCat: ${e.toString()}',
      );
    }
  }

  void _onCustomerInfoUpdate(CustomerInfo customerInfo) {
    final isPremium = customerInfo.entitlements.all[_entitlementId]?.isActive == true;
    state = state.copyWith(
      customerInfo: customerInfo,
      isPremium: isPremium,
    );
  }

  Future<void> refreshCustomerInfo() async {
    try {
      final customerInfo = await Purchases.getCustomerInfo();
      final isPremium = customerInfo.entitlements.all[_entitlementId]?.isActive == true;
      
      state = state.copyWith(
        customerInfo: customerInfo,
        isPremium: isPremium,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to get customer info: ${e.toString()}',
      );
    }
  }

  Future<void> getOfferings() async {
    try {
      final offerings = await Purchases.getOfferings();
      final packages = offerings.getOffering(_offeringId)?.availablePackages ?? [];
      
      state = state.copyWith(
        availablePackages: packages,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to get offerings: ${e.toString()}',
      );
    }
  }

  Future<bool> purchasePackage(Package package) async {
    try {
      state = state.copyWith(isLoading: true, error: null);
      
      final purchaseResult = await Purchases.purchasePackage(package);
      final customerInfo = purchaseResult.customerInfo;
      final isPremium = customerInfo.entitlements.all[_entitlementId]?.isActive == true;
      
      state = state.copyWith(
        customerInfo: customerInfo,
        isPremium: isPremium,
        isLoading: false,
      );
      
      return isPremium;
    } catch (e) {
      String errorMessage;
      if (e is PurchasesErrorCode) {
        switch (e) {
          case PurchasesErrorCode.purchaseCancelledError:
            errorMessage = 'Purchase was cancelled';
            break;
          case PurchasesErrorCode.purchaseNotAllowedError:
            errorMessage = 'Purchase not allowed';
            break;
          case PurchasesErrorCode.paymentPendingError:
            errorMessage = 'Payment is pending';
            break;
          case PurchasesErrorCode.productNotAvailableForPurchaseError:
            errorMessage = 'Product not available for purchase';
            break;
          case PurchasesErrorCode.networkError:
            errorMessage = 'Network error occurred';
            break;
          default:
            errorMessage = 'Purchase failed: ${e.toString()}';
        }
      } else {
        errorMessage = 'Purchase failed: ${e.toString()}';
      }
      
      state = state.copyWith(
        isLoading: false,
        error: errorMessage,
      );
      return false;
    }
  }

  Future<bool> restorePurchases() async {
    try {
      state = state.copyWith(isLoading: true, error: null);
      
      final customerInfo = await Purchases.restorePurchases();
      final isPremium = customerInfo.entitlements.all[_entitlementId]?.isActive == true;
      
      state = state.copyWith(
        customerInfo: customerInfo,
        isPremium: isPremium,
        isLoading: false,
      );
      
      return isPremium;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to restore purchases: ${e.toString()}',
      );
      return false;
    }
  }

  Future<void> setUserId(String userId) async {
    try {
      await Purchases.logIn(userId);
      await refreshCustomerInfo();
    } catch (e) {
      state = state.copyWith(
        error: 'Failed to set user ID: ${e.toString()}',
      );
    }
  }

  Future<void> logout() async {
    try {
      await Purchases.logOut();
      await refreshCustomerInfo();
    } catch (e) {
      state = state.copyWith(
        error: 'Failed to logout: ${e.toString()}',
      );
    }
  }

  void clearError() {
    state = state.copyWith(error: null);
  }

  @override
  void dispose() {
    Purchases.removeCustomerInfoUpdateListener(_onCustomerInfoUpdate);
    super.dispose();
  }
}

// Provider instance
final revenueCatProvider = StateNotifierProvider<RevenueCatNotifier, RevenueCatState>(
  (ref) => RevenueCatNotifier(),
);

// Convenience providers
final isPremiumProvider = Provider<bool>((ref) {
  return ref.watch(revenueCatProvider).isPremium;
});

final availablePackagesProvider = Provider<List<Package>>((ref) {
  return ref.watch(revenueCatProvider).availablePackages;
});
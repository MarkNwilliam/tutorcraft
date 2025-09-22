import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

// Usage record model
class UsageRecord {
  final String id;
  final String userId;
  final String type; // 'video_generation', 'premium_feature', etc.
  final String topic;
  final DateTime createdAt;
  final Map<String, dynamic>? metadata;

  UsageRecord({
    required this.id,
    required this.userId,
    required this.type,
    required this.topic,
    required this.createdAt,
    this.metadata,
  });

  factory UsageRecord.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return UsageRecord(
      id: doc.id,
      userId: data['userId'] ?? '',
      type: data['type'] ?? '',
      topic: data['topic'] ?? '',
      createdAt: (data['createdAt'] as Timestamp?)?.toDate() ?? DateTime.now(),
      metadata: data['metadata'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toFirestore() {
    return {
      'userId': userId,
      'type': type,
      'topic': topic,
      'createdAt': Timestamp.fromDate(createdAt),
      'metadata': metadata,
    };
  }
}

// Usage statistics model
class UsageStats {
  final int totalVideos;
  final int monthlyVideos;
  final int dailyVideos;
  final List<String> popularTopics;
  final DateTime lastActivity;

  UsageStats({
    required this.totalVideos,
    required this.monthlyVideos,
    required this.dailyVideos,
    required this.popularTopics,
    required this.lastActivity,
  });

  factory UsageStats.empty() {
    return UsageStats(
      totalVideos: 0,
      monthlyVideos: 0,
      dailyVideos: 0,
      popularTopics: [],
      lastActivity: DateTime.now(),
    );
  }
}

// Usage state
class UsageState {
  final UsageStats stats;
  final int currentUsage;
  final bool isLoading;
  final String? error;

  UsageState({
    required this.stats,
    this.currentUsage = 0,
    this.isLoading = false,
    this.error,
  });

  UsageState copyWith({
    UsageStats? stats,
    int? currentUsage,
    bool? isLoading,
    String? error,
  }) {
    return UsageState(
      stats: stats ?? this.stats,
      currentUsage: currentUsage ?? this.currentUsage,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }
}

// Usage provider
class UsageNotifier extends StateNotifier<UsageState> {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  UsageNotifier() : super(UsageState(stats: UsageStats.empty()));

  // Record a video generation
  Future<void> recordVideoGeneration(String userId, String topic) async {
    try {
      final record = UsageRecord(
        id: '', // Firestore will generate
        userId: userId,
        type: 'video_generation',
        topic: topic,
        createdAt: DateTime.now(),
        metadata: {
          'platform': 'mobile',
          'version': '1.0.0',
        },
      );

      await _firestore
          .collection('usage_records')
          .add(record.toFirestore());

      // Update current usage
      final currentUsage = await getCurrentUsage(userId);
      state = state.copyWith(currentUsage: currentUsage);

      // Update user stats
      await _updateUserStats(userId);

    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  // Get current month usage for user
  Future<int> getCurrentUsage(String userId) async {
    try {
      final now = DateTime.now();
      final startOfMonth = DateTime(now.year, now.month, 1);
      
      final query = await _firestore
          .collection('usage_records')
          .where('userId', isEqualTo: userId)
          .where('type', isEqualTo: 'video_generation')
          .where('createdAt', isGreaterThanOrEqualTo: Timestamp.fromDate(startOfMonth))
          .get();

      return query.docs.length;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return 0;
    }
  }

  // Get usage statistics for user
  Future<void> loadUsageStats(String userId) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      final now = DateTime.now();
      final startOfMonth = DateTime(now.year, now.month, 1);
      final startOfDay = DateTime(now.year, now.month, now.day);

      // Get total videos
      final totalQuery = await _firestore
          .collection('usage_records')
          .where('userId', isEqualTo: userId)
          .where('type', isEqualTo: 'video_generation')
          .get();

      // Get monthly videos
      final monthlyQuery = await _firestore
          .collection('usage_records')
          .where('userId', isEqualTo: userId)
          .where('type', isEqualTo: 'video_generation')
          .where('createdAt', isGreaterThanOrEqualTo: Timestamp.fromDate(startOfMonth))
          .get();

      // Get daily videos
      final dailyQuery = await _firestore
          .collection('usage_records')
          .where('userId', isEqualTo: userId)
          .where('type', isEqualTo: 'video_generation')
          .where('createdAt', isGreaterThanOrEqualTo: Timestamp.fromDate(startOfDay))
          .get();

      // Get popular topics (last 30 days)
      final thirtyDaysAgo = now.subtract(const Duration(days: 30));
      final popularQuery = await _firestore
          .collection('usage_records')
          .where('userId', isEqualTo: userId)
          .where('type', isEqualTo: 'video_generation')
          .where('createdAt', isGreaterThanOrEqualTo: Timestamp.fromDate(thirtyDaysAgo))
          .orderBy('createdAt', descending: true)
          .limit(50)
          .get();

      // Process popular topics
      final topicCounts = <String, int>{};
      for (final doc in popularQuery.docs) {
        final record = UsageRecord.fromFirestore(doc);
        topicCounts[record.topic] = (topicCounts[record.topic] ?? 0) + 1;
      }
      
      final popularTopics = topicCounts.entries
          .toList()
          ..sort((a, b) => b.value.compareTo(a.value));

      final stats = UsageStats(
        totalVideos: totalQuery.docs.length,
        monthlyVideos: monthlyQuery.docs.length,
        dailyVideos: dailyQuery.docs.length,
        popularTopics: popularTopics.take(5).map((e) => e.key).toList(),
        lastActivity: totalQuery.docs.isNotEmpty 
          ? UsageRecord.fromFirestore(totalQuery.docs.first).createdAt
          : DateTime.now(),
      );

      state = state.copyWith(
        stats: stats,
        currentUsage: monthlyQuery.docs.length,
        isLoading: false,
      );

    } catch (e) {
      state = state.copyWith(error: e.toString(), isLoading: false);
    }
  }

  // Update user statistics document
  Future<void> _updateUserStats(String userId) async {
    try {
      final stats = await _calculateUserStats(userId);
      
      await _firestore
          .collection('user_stats')
          .doc(userId)
          .set({
        'totalVideos': stats.totalVideos,
        'monthlyVideos': stats.monthlyVideos,
        'dailyVideos': stats.dailyVideos,
        'popularTopics': stats.popularTopics,
        'lastActivity': Timestamp.fromDate(stats.lastActivity),
        'updatedAt': Timestamp.fromDate(DateTime.now()),
      }, SetOptions(merge: true));
      
      state = state.copyWith(stats: stats);
    } catch (e) {
      // Don't update state error for background updates
      print('Error updating user stats: $e');
    }
  }

  Future<UsageStats> _calculateUserStats(String userId) async {
    final now = DateTime.now();
    final startOfMonth = DateTime(now.year, now.month, 1);
    final startOfDay = DateTime(now.year, now.month, now.day);

    // Get all records for this user
    final query = await _firestore
        .collection('usage_records')
        .where('userId', isEqualTo: userId)
        .where('type', isEqualTo: 'video_generation')
        .orderBy('createdAt', descending: true)
        .get();

    final allRecords = query.docs.map((doc) => UsageRecord.fromFirestore(doc)).toList();

    // Calculate stats
    final totalVideos = allRecords.length;
    final monthlyVideos = allRecords.where((r) => r.createdAt.isAfter(startOfMonth)).length;
    final dailyVideos = allRecords.where((r) => r.createdAt.isAfter(startOfDay)).length;

    // Popular topics from last 30 days
    final thirtyDaysAgo = now.subtract(const Duration(days: 30));
    final recentRecords = allRecords.where((r) => r.createdAt.isAfter(thirtyDaysAgo));
    final topicCounts = <String, int>{};
    
    for (final record in recentRecords) {
      topicCounts[record.topic] = (topicCounts[record.topic] ?? 0) + 1;
    }
    
    final popularTopics = topicCounts.entries
        .toList()
        ..sort((a, b) => b.value.compareTo(a.value));

    return UsageStats(
      totalVideos: totalVideos,
      monthlyVideos: monthlyVideos,
      dailyVideos: dailyVideos,
      popularTopics: popularTopics.take(5).map((e) => e.key).toList(),
      lastActivity: allRecords.isNotEmpty ? allRecords.first.createdAt : DateTime.now(),
    );
  }

  // Check if user has reached limit
  Future<bool> canGenerateVideo(String userId, String subscription) async {
    try {
      final currentUsage = await getCurrentUsage(userId);
      final limit = _getLimit(subscription);
      
      return currentUsage < limit;
    } catch (e) {
      return false; // Conservative approach - deny on error
    }
  }

  int _getLimit(String subscription) {
    switch (subscription) {
      case 'premium':
        return 100;
      case 'pro':
        return 999999; // Effectively unlimited
      default:
        return 3; // Free tier
    }
  }

  // Get usage records for analytics
  Future<List<UsageRecord>> getUsageHistory(String userId, {int limit = 50}) async {
    try {
      final query = await _firestore
          .collection('usage_records')
          .where('userId', isEqualTo: userId)
          .orderBy('createdAt', descending: true)
          .limit(limit)
          .get();

      return query.docs.map((doc) => UsageRecord.fromFirestore(doc)).toList();
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return [];
    }
  }

  void clearError() {
    state = state.copyWith(error: null);
  }
}

final usageProvider = StateNotifierProvider<UsageNotifier, UsageState>((ref) {
  return UsageNotifier();
});
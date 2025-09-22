import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

// Enhanced video history model
class VideoHistory {
  final String id;
  final String userId;
  final String topic;
  final String status;
  final String? videoUrl;
  final String? localPath;
  final String? thumbnailUrl;
  final DateTime createdAt;
  final DateTime? completedAt;
  final int duration; // in seconds
  final Map<String, dynamic>? metadata;
  final List<String> tags;
  final bool isFavorite;
  final int viewCount;
  final DateTime? lastViewedAt;

  VideoHistory({
    required this.id,
    required this.userId,
    required this.topic,
    required this.status,
    this.videoUrl,
    this.localPath,
    this.thumbnailUrl,
    required this.createdAt,
    this.completedAt,
    this.duration = 0,
    this.metadata,
    this.tags = const [],
    this.isFavorite = false,
    this.viewCount = 0,
    this.lastViewedAt,
  });

  VideoHistory copyWith({
    String? id,
    String? userId,
    String? topic,
    String? status,
    String? videoUrl,
    String? localPath,
    String? thumbnailUrl,
    DateTime? createdAt,
    DateTime? completedAt,
    int? duration,
    Map<String, dynamic>? metadata,
    List<String>? tags,
    bool? isFavorite,
    int? viewCount,
    DateTime? lastViewedAt,
  }) {
    return VideoHistory(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      topic: topic ?? this.topic,
      status: status ?? this.status,
      videoUrl: videoUrl ?? this.videoUrl,
      localPath: localPath ?? this.localPath,
      thumbnailUrl: thumbnailUrl ?? this.thumbnailUrl,
      createdAt: createdAt ?? this.createdAt,
      completedAt: completedAt ?? this.completedAt,
      duration: duration ?? this.duration,
      metadata: metadata ?? this.metadata,
      tags: tags ?? this.tags,
      isFavorite: isFavorite ?? this.isFavorite,
      viewCount: viewCount ?? this.viewCount,
      lastViewedAt: lastViewedAt ?? this.lastViewedAt,
    );
  }

  factory VideoHistory.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return VideoHistory(
      id: doc.id,
      userId: data['userId'] ?? '',
      topic: data['topic'] ?? '',
      status: data['status'] ?? 'unknown',
      videoUrl: data['videoUrl'],
      localPath: data['localPath'],
      thumbnailUrl: data['thumbnailUrl'],
      createdAt: (data['createdAt'] as Timestamp?)?.toDate() ?? DateTime.now(),
      completedAt: (data['completedAt'] as Timestamp?)?.toDate(),
      duration: data['duration'] ?? 0,
      metadata: data['metadata'] as Map<String, dynamic>?,
      tags: List<String>.from(data['tags'] ?? []),
      isFavorite: data['isFavorite'] ?? false,
      viewCount: data['viewCount'] ?? 0,
      lastViewedAt: (data['lastViewedAt'] as Timestamp?)?.toDate(),
    );
  }

  Map<String, dynamic> toFirestore() {
    return {
      'userId': userId,
      'topic': topic,
      'status': status,
      'videoUrl': videoUrl,
      'localPath': localPath,
      'thumbnailUrl': thumbnailUrl,
      'createdAt': Timestamp.fromDate(createdAt),
      'completedAt': completedAt != null ? Timestamp.fromDate(completedAt!) : null,
      'duration': duration,
      'metadata': metadata,
      'tags': tags,
      'isFavorite': isFavorite,
      'viewCount': viewCount,
      'lastViewedAt': lastViewedAt != null ? Timestamp.fromDate(lastViewedAt!) : null,
      'updatedAt': Timestamp.fromDate(DateTime.now()),
    };
  }
}

// Video history statistics
class VideoHistoryStats {
  final int totalVideos;
  final int completedVideos;
  final int failedVideos;
  final int favoriteVideos;
  final int totalDuration; // in seconds
  final List<String> popularTopics;
  final DateTime? lastVideoDate;
  final Map<String, int> statusCount;

  VideoHistoryStats({
    required this.totalVideos,
    required this.completedVideos,
    required this.failedVideos,
    required this.favoriteVideos,
    required this.totalDuration,
    required this.popularTopics,
    this.lastVideoDate,
    required this.statusCount,
  });

  factory VideoHistoryStats.empty() {
    return VideoHistoryStats(
      totalVideos: 0,
      completedVideos: 0,
      failedVideos: 0,
      favoriteVideos: 0,
      totalDuration: 0,
      popularTopics: [],
      statusCount: {},
    );
  }
}

// Video history state
class VideoHistoryState {
  final List<VideoHistory> videos;
  final List<VideoHistory> favorites;
  final VideoHistoryStats stats;
  final bool isLoading;
  final bool hasMore;
  final String? error;
  final String searchQuery;
  final List<String> selectedTags;
  final String sortBy; // 'newest', 'oldest', 'topic', 'duration'

  VideoHistoryState({
    this.videos = const [],
    this.favorites = const [],
    required this.stats,
    this.isLoading = false,
    this.hasMore = true,
    this.error,
    this.searchQuery = '',
    this.selectedTags = const [],
    this.sortBy = 'newest',
  });

  VideoHistoryState copyWith({
    List<VideoHistory>? videos,
    List<VideoHistory>? favorites,
    VideoHistoryStats? stats,
    bool? isLoading,
    bool? hasMore,
    String? error,
    String? searchQuery,
    List<String>? selectedTags,
    String? sortBy,
  }) {
    return VideoHistoryState(
      videos: videos ?? this.videos,
      favorites: favorites ?? this.favorites,
      stats: stats ?? this.stats,
      isLoading: isLoading ?? this.isLoading,
      hasMore: hasMore ?? this.hasMore,
      error: error,
      searchQuery: searchQuery ?? this.searchQuery,
      selectedTags: selectedTags ?? this.selectedTags,
      sortBy: sortBy ?? this.sortBy,
    );
  }
}

// Video history provider
class VideoHistoryNotifier extends StateNotifier<VideoHistoryState> {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  DocumentSnapshot? _lastDocument;
  static const int _pageSize = 20;

  VideoHistoryNotifier() : super(VideoHistoryState(stats: VideoHistoryStats.empty()));

  // Save a video to history when it's created
  Future<String> saveVideoToHistory({
    required String userId,
    required String topic,
    String status = 'generating',
    String? videoUrl,
    String? localPath,
    String? thumbnailUrl,
    Map<String, dynamic>? metadata,
    List<String> tags = const [],
  }) async {
    try {
      final videoHistory = VideoHistory(
        id: '', // Firestore will generate
        userId: userId,
        topic: topic,
        status: status,
        videoUrl: videoUrl,
        localPath: localPath,
        thumbnailUrl: thumbnailUrl,
        createdAt: DateTime.now(),
        completedAt: status == 'completed' ? DateTime.now() : null,
        metadata: metadata,
        tags: tags,
      );

      final docRef = await _firestore
          .collection('video_history')
          .add(videoHistory.toFirestore());

      debugPrint('Video saved to history: ${docRef.id}');
      
      // Refresh the list if we're showing this user's videos
      final currentUser = FirebaseAuth.instance.currentUser;
      if (currentUser?.uid == userId) {
        await loadVideoHistory();
      }
      
      return docRef.id;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      throw Exception('Failed to save video to history: $e');
    }
  }

  // Update video status and details
  Future<void> updateVideoInHistory({
    required String videoId,
    String? status,
    String? videoUrl,
    String? localPath,
    String? thumbnailUrl,
    int? duration,
    Map<String, dynamic>? metadata,
  }) async {
    try {
      final updateData = <String, dynamic>{};
      
      if (status != null) {
        updateData['status'] = status;
        if (status == 'completed') {
          updateData['completedAt'] = Timestamp.fromDate(DateTime.now());
        }
      }
      if (videoUrl != null) updateData['videoUrl'] = videoUrl;
      if (localPath != null) updateData['localPath'] = localPath;
      if (thumbnailUrl != null) updateData['thumbnailUrl'] = thumbnailUrl;
      if (duration != null) updateData['duration'] = duration;
      if (metadata != null) updateData['metadata'] = metadata;
      
      updateData['updatedAt'] = Timestamp.fromDate(DateTime.now());

      await _firestore
          .collection('video_history')
          .doc(videoId)
          .update(updateData);

      debugPrint('Video updated in history: $videoId');

      // Update local state
      final updatedVideos = state.videos.map((video) {
        if (video.id == videoId) {
          return video.copyWith(
            status: status ?? video.status,
            videoUrl: videoUrl ?? video.videoUrl,
            localPath: localPath ?? video.localPath,
            thumbnailUrl: thumbnailUrl ?? video.thumbnailUrl,
            duration: duration ?? video.duration,
            metadata: metadata ?? video.metadata,
            completedAt: status == 'completed' ? DateTime.now() : video.completedAt,
          );
        }
        return video;
      }).toList();

      state = state.copyWith(videos: updatedVideos);

    } catch (e) {
      state = state.copyWith(error: e.toString());
      debugPrint('Error updating video in history: $e');
    }
  }

  // Load video history for current user
  Future<void> loadVideoHistory({bool refresh = false}) async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      state = state.copyWith(error: 'Please sign in to view video history');
      return;
    }

    if (refresh) {
      _lastDocument = null;
      state = state.copyWith(videos: [], hasMore: true);
    }

    if (state.isLoading || !state.hasMore) return;

    state = state.copyWith(isLoading: true, error: null);

    try {
      Query query = _firestore
          .collection('video_history')
          .where('userId', isEqualTo: user.uid)
          .orderBy(_getSortField(), descending: _isDescending());

      // Apply filters
      if (state.searchQuery.isNotEmpty) {
        query = query.where('topic', isGreaterThanOrEqualTo: state.searchQuery)
                    .where('topic', isLessThan: state.searchQuery + '\uf8ff');
      }

      if (state.selectedTags.isNotEmpty) {
        query = query.where('tags', arrayContainsAny: state.selectedTags);
      }

      query = query.limit(_pageSize);

      if (_lastDocument != null) {
        query = query.startAfterDocument(_lastDocument!);
      }

      final querySnapshot = await query.get();
      
      final newVideos = querySnapshot.docs
          .map((doc) => VideoHistory.fromFirestore(doc))
          .toList();

      if (querySnapshot.docs.isNotEmpty) {
        _lastDocument = querySnapshot.docs.last;
      }

      final allVideos = refresh ? newVideos : [...state.videos, ...newVideos];
      final hasMore = newVideos.length == _pageSize;

      state = state.copyWith(
        videos: allVideos,
        hasMore: hasMore,
        isLoading: false,
      );

      // Load stats
      await _loadStats(user.uid);

    } catch (e) {
      state = state.copyWith(error: e.toString(), isLoading: false);
      debugPrint('Error loading video history: $e');
    }
  }

  // Load favorites
  Future<void> loadFavorites() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return;

    try {
      final query = await _firestore
          .collection('video_history')
          .where('userId', isEqualTo: user.uid)
          .where('isFavorite', isEqualTo: true)
          .orderBy('createdAt', descending: true)
          .get();

      final favorites = query.docs
          .map((doc) => VideoHistory.fromFirestore(doc))
          .toList();

      state = state.copyWith(favorites: favorites);

    } catch (e) {
      debugPrint('Error loading favorites: $e');
    }
  }

  // Toggle favorite status
  Future<void> toggleFavorite(String videoId) async {
    try {
      final video = state.videos.firstWhere((v) => v.id == videoId);
      final newFavoriteStatus = !video.isFavorite;

      await _firestore
          .collection('video_history')
          .doc(videoId)
          .update({'isFavorite': newFavoriteStatus});

      // Update local state
      final updatedVideos = state.videos.map((v) {
        if (v.id == videoId) {
          return v.copyWith(isFavorite: newFavoriteStatus);
        }
        return v;
      }).toList();

      state = state.copyWith(videos: updatedVideos);

      // Reload favorites
      await loadFavorites();

    } catch (e) {
      state = state.copyWith(error: e.toString());
      debugPrint('Error toggling favorite: $e');
    }
  }

  // Record video view
  Future<void> recordVideoView(String videoId) async {
    try {
      await _firestore
          .collection('video_history')
          .doc(videoId)
          .update({
        'viewCount': FieldValue.increment(1),
        'lastViewedAt': Timestamp.fromDate(DateTime.now()),
      });

      // Update local state
      final updatedVideos = state.videos.map((v) {
        if (v.id == videoId) {
          return v.copyWith(
            viewCount: v.viewCount + 1,
            lastViewedAt: DateTime.now(),
          );
        }
        return v;
      }).toList();

      state = state.copyWith(videos: updatedVideos);

    } catch (e) {
      debugPrint('Error recording video view: $e');
    }
  }

  // Search videos
  Future<void> searchVideos(String query) async {
    state = state.copyWith(searchQuery: query);
    await loadVideoHistory(refresh: true);
  }

  // Filter by tags
  Future<void> filterByTags(List<String> tags) async {
    state = state.copyWith(selectedTags: tags);
    await loadVideoHistory(refresh: true);
  }

  // Sort videos
  Future<void> sortVideos(String sortBy) async {
    state = state.copyWith(sortBy: sortBy);
    await loadVideoHistory(refresh: true);
  }

  // Delete video
  Future<void> deleteVideo(String videoId) async {
    try {
      await _firestore
          .collection('video_history')
          .doc(videoId)
          .delete();

      // Remove from local state
      final updatedVideos = state.videos.where((v) => v.id != videoId).toList();
      state = state.copyWith(videos: updatedVideos);

      debugPrint('Video deleted from history: $videoId');

    } catch (e) {
      state = state.copyWith(error: e.toString());
      debugPrint('Error deleting video: $e');
    }
  }

  // Get all unique tags for filtering
  List<String> getAllTags() {
    final tags = <String>{};
    for (final video in state.videos) {
      tags.addAll(video.tags);
    }
    return tags.toList()..sort();
  }

  // Load statistics
  Future<void> _loadStats(String userId) async {
    try {
      final query = await _firestore
          .collection('video_history')
          .where('userId', isEqualTo: userId)
          .get();

      final videos = query.docs.map((doc) => VideoHistory.fromFirestore(doc)).toList();

      final totalVideos = videos.length;
      final completedVideos = videos.where((v) => v.status == 'completed').length;
      final failedVideos = videos.where((v) => v.status == 'failed').length;
      final favoriteVideos = videos.where((v) => v.isFavorite).length;
      final totalDuration = videos.fold<int>(0, (sum, v) => sum + v.duration);

      // Popular topics
      final topicCounts = <String, int>{};
      for (final video in videos) {
        topicCounts[video.topic] = (topicCounts[video.topic] ?? 0) + 1;
      }
      final popularTopics = topicCounts.entries
          .toList()
          ..sort((a, b) => b.value.compareTo(a.value));

      // Status count
      final statusCount = <String, int>{};
      for (final video in videos) {
        statusCount[video.status] = (statusCount[video.status] ?? 0) + 1;
      }

      final stats = VideoHistoryStats(
        totalVideos: totalVideos,
        completedVideos: completedVideos,
        failedVideos: failedVideos,
        favoriteVideos: favoriteVideos,
        totalDuration: totalDuration,
        popularTopics: popularTopics.take(10).map((e) => e.key).toList(),
        lastVideoDate: videos.isNotEmpty ? videos.first.createdAt : null,
        statusCount: statusCount,
      );

      state = state.copyWith(stats: stats);

    } catch (e) {
      debugPrint('Error loading stats: $e');
    }
  }

  String _getSortField() {
    switch (state.sortBy) {
      case 'oldest':
        return 'createdAt';
      case 'topic':
        return 'topic';
      case 'duration':
        return 'duration';
      default:
        return 'createdAt';
    }
  }

  bool _isDescending() {
    return state.sortBy != 'oldest';
  }

  void clearError() {
    state = state.copyWith(error: null);
  }

  void clearFilters() {
    state = state.copyWith(
      searchQuery: '',
      selectedTags: [],
      sortBy: 'newest',
    );
    loadVideoHistory(refresh: true);
  }
}

// Provider
final videoHistoryProvider = StateNotifierProvider<VideoHistoryNotifier, VideoHistoryState>((ref) {
  return VideoHistoryNotifier();
});

// Helper providers
final videoHistoryStatsProvider = Provider<VideoHistoryStats>((ref) {
  return ref.watch(videoHistoryProvider).stats;
});

final favoriteVideosProvider = Provider<List<VideoHistory>>((ref) {
  return ref.watch(videoHistoryProvider).favorites;
});

final videoHistoryTagsProvider = Provider<List<String>>((ref) {
  return ref.watch(videoHistoryProvider.notifier).getAllTags();
});
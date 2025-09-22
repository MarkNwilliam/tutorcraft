import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:intl/intl.dart';
import 'usage_provider.dart';
import 'video_history_provider.dart';
import '../providers/revenuecat_provider.dart';

// Video model
class Video {
  final String id;
  final String topic;
  final String status;
  final int progress;
  final String? videoUrl;
  final String? localPath;
  final String? thumbnailUrl;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final DateTime? completedAt;
  final String userId;
  final int? duration;
  final int? videoSize;
  final Map<String, dynamic>? metadata;
  final List<String>? tags;
  final int viewCount;
  final bool isFavorite;

  Video({
    required this.id,
    required this.topic,
    required this.status,
    this.progress = 0,
    this.videoUrl,
    this.localPath,
    this.thumbnailUrl,
    required this.createdAt,
    this.updatedAt,
    this.completedAt,
    required this.userId,
    this.duration,
    this.videoSize,
    this.metadata,
    this.tags,
    this.viewCount = 0,
    this.isFavorite = false,
  });

  // Factory constructor from Firebase document
  factory Video.fromFirebase(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    
    return Video(
      id: doc.id,
      topic: data['topic'] ?? '',
      status: data['status'] ?? 'unknown',
      videoUrl: data['videoUrl'],
      localPath: data['localPath'],
      thumbnailUrl: data['thumbnailUrl'],
      createdAt: (data['createdAt'] as Timestamp).toDate(),
      updatedAt: data['updatedAt'] != null 
          ? (data['updatedAt'] as Timestamp).toDate() 
          : null,
      completedAt: data['completedAt'] != null 
          ? (data['completedAt'] as Timestamp).toDate() 
          : null,
      userId: data['userId'] ?? '',
      duration: data['duration'] ?? 0,
      videoSize: data['videoSize'] ?? 0,
      metadata: data['metadata'] != null 
          ? Map<String, dynamic>.from(data['metadata']) 
          : null,
      tags: data['tags'] != null 
          ? List<String>.from(data['tags']) 
          : [],
      viewCount: data['viewCount'] ?? 0,
      isFavorite: data['isFavorite'] ?? false,
    );
  }

  Video copyWith({
    String? id,
    String? topic,
    String? status,
    int? progress,
    String? videoUrl,
    String? localPath,
    String? thumbnailUrl,
    DateTime? createdAt,
    DateTime? updatedAt,
    DateTime? completedAt,
    String? userId,
    int? duration,
    int? videoSize,
    Map<String, dynamic>? metadata,
    List<String>? tags,
    int? viewCount,
    bool? isFavorite,
  }) {
    return Video(
      id: id ?? this.id,
      topic: topic ?? this.topic,
      status: status ?? this.status,
      progress: progress ?? this.progress,
      videoUrl: videoUrl ?? this.videoUrl,
      localPath: localPath ?? this.localPath,
      thumbnailUrl: thumbnailUrl ?? this.thumbnailUrl,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      completedAt: completedAt ?? this.completedAt,
      userId: userId ?? this.userId,
      duration: duration ?? this.duration,
      videoSize: videoSize ?? this.videoSize,
      metadata: metadata ?? this.metadata,
      tags: tags ?? this.tags,
      viewCount: viewCount ?? this.viewCount,
      isFavorite: isFavorite ?? this.isFavorite,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'topic': topic,
      'status': status,
      'progress': progress,
      'videoUrl': videoUrl,
      'localPath': localPath,
      'thumbnailUrl': thumbnailUrl,
      'createdAt': createdAt.toIso8601String(),
      'updatedAt': updatedAt?.toIso8601String(),
      'completedAt': completedAt?.toIso8601String(),
      'userId': userId,
      'duration': duration,
      'videoSize': videoSize,
      'metadata': metadata,
      'tags': tags,
      'viewCount': viewCount,
      'isFavorite': isFavorite,
    };
  }

  factory Video.fromJson(Map<String, dynamic> json) {
    return Video(
      id: json['id'],
      topic: json['topic'],
      status: json['status'],
      progress: json['progress'] ?? 0,
      videoUrl: json['videoUrl'],
      localPath: json['localPath'],
      thumbnailUrl: json['thumbnailUrl'],
      createdAt: DateTime.parse(json['createdAt']),
      updatedAt: json['updatedAt'] != null 
          ? DateTime.parse(json['updatedAt']) 
          : null,
      completedAt: json['completedAt'] != null 
          ? DateTime.parse(json['completedAt']) 
          : null,
      userId: json['userId'] ?? '',
      duration: json['duration'] ?? 0,
      videoSize: json['videoSize'] ?? 0,
      metadata: json['metadata'] != null 
          ? Map<String, dynamic>.from(json['metadata']) 
          : null,
      tags: json['tags'] != null 
          ? List<String>.from(json['tags']) 
          : [],
      viewCount: json['viewCount'] ?? 0,
      isFavorite: json['isFavorite'] ?? false,
    );
  }
}

// Video state
class VideoState {
  final Video? currentVideo;
  final List<Video> recentVideos;
  final bool isLoading;
  final String? error;
  final bool hasReachedLimit;

  VideoState({
    this.currentVideo,
    this.recentVideos = const [],
    this.isLoading = false,
    this.error,
    this.hasReachedLimit = false,
  });

  VideoState copyWith({
    Video? currentVideo,
    List<Video>? recentVideos,
    bool? isLoading,
    String? error,
    bool? hasReachedLimit,
  }) {
    return VideoState(
      currentVideo: currentVideo,
      recentVideos: recentVideos ?? this.recentVideos,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      hasReachedLimit: hasReachedLimit ?? this.hasReachedLimit,
    );
  }
}

// Video API service
class VideoApiService {
  static const String baseUrl = '';
  static final Dio _dio = Dio(
    BaseOptions(
      connectTimeout: const Duration(seconds: 900),
      receiveTimeout: const Duration(seconds: 900),
    ),
  );
  
  static Future<String> generateVideo(String topic) async {
    try {
      final response = await _dio.post(
        '$baseUrl/generate_video',
        data: {'topic': topic},
        options: Options(headers: {'Content-Type': 'application/json'}),
      );

      if (response.statusCode == 200) {
        return response.data['video_url'] as String;
      } else {
        throw Exception('Failed to generate video: ${response.statusCode}');
      }
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionTimeout) {
        throw Exception('Connection timeout - check your internet');
      } else if (e.type == DioExceptionType.receiveTimeout) {
        throw Exception('Request timeout - generation taking too long');
      } else {
        throw Exception('Network error: ${e.message}');
      }
    } catch (e) {
      throw Exception('Unexpected error: $e');
    }
  }

  static Future<String> downloadVideo(String videoUrl, String videoId, {void Function(int, int)? onProgress}) async {
    try {
      // Ensure the download URL uses HTTPS
      String downloadUrl = videoUrl;
      if (downloadUrl.startsWith('http://')) {
        downloadUrl = downloadUrl.replaceFirst('http://', 'https://');
      }

      final directory = await getApplicationDocumentsDirectory();
      final videosDir = Directory('${directory.path}/videos');
      
      if (!await videosDir.exists()) {
        await videosDir.create(recursive: true);
      }
      
      final localPath = '${videosDir.path}/video_$videoId.mp4';
      
      // Check if file already exists
      final existingFile = File(localPath);
      if (await existingFile.exists()) {
        return localPath;
      }

      // Download the file
      await _dio.download(
        downloadUrl,
        localPath,
        onReceiveProgress: onProgress,
      );
      
      return localPath;
    } on DioException catch (e) {
      throw Exception('Download failed: ${e.message}');
    } catch (e) {
      throw Exception('Download error: $e');
    }
  }
}

// Updated VideoNotifier with Firebase storage integration
class VideoNotifier extends StateNotifier<VideoState> {
  final Ref ref;
  String? _currentVideoHistoryId;
  
  VideoNotifier(this.ref) : super(VideoState()) {
    _loadRecentVideosFromLocal();
  }

Future<void> generateVideo(String topic, {List<String> tags = const []}) async {
  try {
    // Get current user
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      state = state.copyWith(
        error: 'Please sign in to generate videos',
        isLoading: false,
      );
      return;
    }

    // Check premium status
    final revenueCatState = ref.read(revenueCatProvider);
    final isPremium = revenueCatState.isPremium;

    // For non-premium users, check usage limit
    if (!isPremium) {
      final usageNotifier = ref.read(usageProvider.notifier);
      final canGenerate = await usageNotifier.canGenerateVideo(user.uid, 'free');
      
      if (!canGenerate) {
        state = state.copyWith(
          hasReachedLimit: true,
          error: 'You\'ve reached your monthly limit of 5 free videos. Upgrade to premium for unlimited video generation.',
          isLoading: false,
        );
        return;
      }
    }

    // Create unique video ID
    final videoId = DateTime.now().millisecondsSinceEpoch.toString();

    // Initialize video generation
    state = state.copyWith(
      isLoading: true,
      error: null,
      hasReachedLimit: false,
      currentVideo: Video(
        id: videoId,
        topic: topic,
        status: 'generating',
        progress: 0,
        createdAt: DateTime.now(),
        userId: user.uid,
      ),
    );

    // Save initial video record to Firebase history
    final historyNotifier = ref.read(videoHistoryProvider.notifier);
    _currentVideoHistoryId = await historyNotifier.saveVideoToHistory(
      userId: user.uid,
      topic: topic,
      status: 'generating',
      metadata: {
        'platform': 'mobile',
        'version': '1.0.0',
        'startedAt': DateTime.now().toIso8601String(),
        'isPremium': isPremium,
        'subscription_status': isPremium ? 'premium' : 'free',
      },
      tags: tags,
    );

    // Simulate progress for better UX
    await _simulateProgress(0, 70);
    
    // Generate video via API
    String videoUrl = await VideoApiService.generateVideo(topic);

    if (videoUrl.startsWith('http://')) {
      videoUrl = videoUrl.replaceFirst('http://', 'https://');
    }
    
    // Update with video URL
    state = state.copyWith(
      currentVideo: state.currentVideo?.copyWith(
        status: 'downloading',
        progress: 80,
        videoUrl: videoUrl,
      ),
    );

    // Update Firebase history with video URL
    if (_currentVideoHistoryId != null) {
      await historyNotifier.updateVideoInHistory(
        videoId: _currentVideoHistoryId!,
        status: 'downloading',
        videoUrl: videoUrl,
      );
    }

    // Download video locally with progress tracking
    int downloadedBytes = 0;
    int totalBytes = 0;
    
    final localPath = await VideoApiService.downloadVideo(
      videoUrl, 
      videoId,
      onProgress: (received, total) {
        downloadedBytes = received;
        totalBytes = total;
        if (total != -1 && state.currentVideo != null) {
          final progress = 80 + ((received / total) * 20).toInt();
          state = state.copyWith(
            currentVideo: state.currentVideo!.copyWith(progress: progress.clamp(80, 99)),
          );
        }
      },
    );

    // Record usage only for non-premium users
    if (!isPremium) {
      final usageNotifier = ref.read(usageProvider.notifier);
      await usageNotifier.recordVideoGeneration(user.uid, topic);
    }

    // Mark as completed
    final completedVideo = state.currentVideo!.copyWith(
      status: 'completed',
      progress: 100,
      localPath: localPath,
    );

    state = state.copyWith(
      currentVideo: completedVideo,
      isLoading: false,
      recentVideos: [completedVideo, ...state.recentVideos],
    );

    // Update Firebase history with final completion details
    if (_currentVideoHistoryId != null) {
      await historyNotifier.updateVideoInHistory(
        videoId: _currentVideoHistoryId!,
        status: 'completed',
        localPath: localPath,
        duration: await _getVideoDuration(localPath),
        metadata: {
          'platform': 'mobile',
          'version': '1.0.0',
          'startedAt': DateTime.now().subtract(const Duration(minutes: 2)).toIso8601String(),
          'completedAt': DateTime.now().toIso8601String(),
          'videoSize': totalBytes > 0 ? totalBytes : await _getVideoFileSize(localPath),
          'isPremium': isPremium,
          'subscription_status': isPremium ? 'premium' : 'free',
        },
      );
    }

    // Save to local storage
    await _saveRecentVideos();
    
    debugPrint('Video generation completed for user: ${user.uid} (Premium: $isPremium)');
    
  } catch (e) {
    // Update Firebase history with failure status
    if (_currentVideoHistoryId != null) {
      final historyNotifier = ref.read(videoHistoryProvider.notifier);
      await historyNotifier.updateVideoInHistory(
        videoId: _currentVideoHistoryId!,
        status: 'failed',
        metadata: {
          'platform': 'mobile',
          'version': '1.0.0',
          'error': e.toString(),
          'failedAt': DateTime.now().toIso8601String(),
        },
      );
    }

    state = state.copyWith(
      isLoading: false,
      error: 'Failed to generate video: ${e.toString()}',
      currentVideo: state.currentVideo?.copyWith(
        status: 'failed',
        progress: 0,
      ),
    );
    
    debugPrint('Video generation failed: $e');
  }
}
  // Helper methods for video file information
  Future<int> _getVideoDuration(String filePath) async {
    try {
      // Return default duration to avoid heavy operations
      return 30; // 30 seconds default
    } catch (e) {
      debugPrint('Error getting video duration: $e');
      return 30; // Fallback to default
    }
  }

  Future<int> _getVideoFileSize(String filePath) async {
    try {
      // Use compute to move file operations to a separate isolate
      return await compute(_getFileSizeIsolate, filePath)
          .timeout(const Duration(seconds: 5), onTimeout: () => 0);
    } catch (e) {
      debugPrint('Error getting video file size: $e');
      return 0;
    }
  }

  // Isolate function for file operations (must be static)
  static int _getFileSizeIsolate(String filePath) {
    try {
      final file = File(filePath);
      if (file.existsSync()) {
        return file.lengthSync();
      }
      return 0;
    } catch (e) {
      return 0;
    }
  }

  // Method to replay/view a video from history
  Future<void> viewVideoFromHistory(String historyId) async {
    try {
      final historyNotifier = ref.read(videoHistoryProvider.notifier);
      await historyNotifier.recordVideoView(historyId);
      debugPrint('Video view recorded for history ID: $historyId');
    } catch (e) {
      debugPrint('Error recording video view: $e');
    }
  }

  // Method to load user's video history from Firebase
  Future<void> loadVideoHistory() async {
    final historyNotifier = ref.read(videoHistoryProvider.notifier);
    await historyNotifier.loadVideoHistory(refresh: true);
  }

  // Method to check current usage without generating video
  Future<void> checkUsageLimits() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return;

    try {
      const userSubscription = 'free';
      final usageNotifier = ref.read(usageProvider.notifier);
      final canGenerate = await usageNotifier.canGenerateVideo(user.uid, userSubscription);
      
      state = state.copyWith(hasReachedLimit: !canGenerate);
      
      // Also load usage stats
      await usageNotifier.loadUsageStats(user.uid);
      
    } catch (e) {
      debugPrint('Error checking usage limits: $e');
    }
  }

  // Method to get current usage count for UI display
  Future<int> getCurrentUsage() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return 0;

    try {
      final usageNotifier = ref.read(usageProvider.notifier);
      return await usageNotifier.getCurrentUsage(user.uid);
    } catch (e) {
      debugPrint('Error getting current usage: $e');
      return 0;
    }
  }

  Future<void> _simulateProgress(int start, int end) async {
    for (int progress = start + 10; progress <= end; progress += 10) {
      await Future.delayed(const Duration(milliseconds: 300));
      if (state.currentVideo != null && mounted) {
        state = state.copyWith(
          currentVideo: state.currentVideo!.copyWith(progress: progress),
        );
      }
    }
  }

  // Load videos from Firebase
  Future<void> loadRecentVideos() async {
    try {
      state = state.copyWith(isLoading: true);
      
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        await _loadRecentVideosFromLocal();
        return;
      }

      // Query Firebase for user's video history
      final querySnapshot = await FirebaseFirestore.instance
          .collection('video_history')
          .where('userId', isEqualTo: user.uid)
          .orderBy('createdAt', descending: true)
          .limit(10)
          .get();

      final videos = querySnapshot.docs
          .map((doc) => Video.fromFirebase(doc))
          .where((video) => video.status == 'completed')
          .toList();

      state = state.copyWith(
        recentVideos: videos,
        isLoading: false,
      );

      // Also save to local storage for offline access
      await _saveRecentVideos();

    } catch (e) {
      debugPrint('Error loading videos from Firebase: $e');
      await _loadRecentVideosFromLocal();
    }
  }

  // Load videos from local storage only
  Future<void> _loadRecentVideosFromLocal() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final videosJson = prefs.getString('recent_videos');
      
      if (videosJson != null) {
        final List<dynamic> videosList = json.decode(videosJson);
        final recentVideos = videosList.map((json) => Video.fromJson(json)).toList();
        
        state = state.copyWith(
          recentVideos: recentVideos,
          isLoading: false,
        );
      } else {
        state = state.copyWith(isLoading: false);
      }
    } catch (e) {
      debugPrint('Error loading recent videos from local: $e');
      state = state.copyWith(isLoading: false);
    }
  }

  Future<void> _saveRecentVideos() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final videosJson = state.recentVideos
          .take(10)
          .map((video) => video.toJson())
          .toList();
      
      await prefs.setString('recent_videos', json.encode(videosJson));
    } catch (e) {
      debugPrint('Error saving recent videos: $e');
    }
  }

  void clearError() {
    state = state.copyWith(error: null, hasReachedLimit: false);
  }

  void resetCurrentVideo() {
    state = state.copyWith(currentVideo: null);
  }

  // Add mounted check for safety
  bool mounted = true;
  @override
  void dispose() {
    mounted = false;
    super.dispose();
  }
}

// Provider
final videoProvider = StateNotifierProvider<VideoNotifier, VideoState>((ref) {
  return VideoNotifier(ref);
});
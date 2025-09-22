import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:glassmorphism/glassmorphism.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:intl/intl.dart';
import '../screens/video_player_screen.dart';

// Simple video model for direct Firebase access
class FirebaseVideo {
  final String id;
  final String topic;
  final String status;
  final String? videoUrl;
  final String? localPath;
  final String? thumbnailUrl;
  final DateTime createdAt;
  final int duration;
  final String userId;
  final String? userEmail;

  FirebaseVideo({
    required this.id,
    required this.topic,
    required this.status,
    this.videoUrl,
    this.localPath,
    this.thumbnailUrl,
    required this.createdAt,
    this.duration = 0,
    required this.userId,
    this.userEmail,
  });

  factory FirebaseVideo.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return FirebaseVideo(
      id: doc.id,
      topic: data['topic'] ?? 'No topic',
      status: data['status'] ?? 'unknown',
      videoUrl: data['videoUrl'],
      localPath: data['localPath'],
      thumbnailUrl: data['thumbnailUrl'],
      createdAt: (data['createdAt'] as Timestamp?)?.toDate() ?? DateTime.now(),
      duration: data['duration'] ?? 0,
      userId: data['userId'] ?? '',
      userEmail: data['userEmail'],
    );
  }
}

// Provider to fetch videos directly from Firebase
final firebaseVideosProvider = StreamProvider<List<FirebaseVideo>>((ref) {
  final user = FirebaseAuth.instance.currentUser;
  if (user == null) {
    debugPrint('❌ No user logged in, cannot fetch videos');
    return Stream.value([]);
  }

  debugPrint('👤 Fetching videos for user: ${user.uid}, email: ${user.email}');
  
  return FirebaseFirestore.instance
      .collection('video_history')
      .where('userId', isEqualTo: user.uid)
      .orderBy('createdAt', descending: true)
      .snapshots()
      .map((snapshot) {
    debugPrint('📥 Received ${snapshot.docs.length} videos from Firebase');
    
    final videos = snapshot.docs.map((doc) {
      debugPrint('📄 Video document: ${doc.id} - ${doc.data()['topic']}');
      return FirebaseVideo.fromFirestore(doc);
    }).toList();

    // Filter only completed videos for display
    final completedVideos = videos.where((v) => v.status == 'completed').toList();
    debugPrint('✅ Filtered to ${completedVideos.length} completed videos');
    
    return completedVideos;
  });
});

class RecentVideosList extends ConsumerWidget {
  const RecentVideosList({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    debugPrint('🔄 Building RecentVideosList widget');
    
    final videosAsync = ref.watch(firebaseVideosProvider);
    
    return videosAsync.when(
      loading: () {
        debugPrint('⏳ Loading videos from Firebase...');
        return const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Loading your videos...'),
            ],
          ),
        );
      },
      error: (error, stackTrace) {
        debugPrint('❌ Error loading videos: $error');
        debugPrint('Stack trace: $stackTrace');
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(LucideIcons.alertCircle, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              const Text('Failed to load videos'),
              const SizedBox(height: 8),
              Text(
                error.toString(),
                style: Theme.of(context).textTheme.bodySmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () {
                  debugPrint('🔄 Retrying video load...');
                  ref.refresh(firebaseVideosProvider);
                },
                child: const Text('Try Again'),
              ),
            ],
          ),
        );
      },
      data: (videos) {
        debugPrint('✅ Loaded ${videos.length} videos successfully');
        
        if (videos.isEmpty) {
          debugPrint('📭 No videos found in collection');
          return const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(LucideIcons.video, size: 48, color: Colors.grey),
                SizedBox(height: 16),
                Text('No videos yet'),
                SizedBox(height: 8),
                Text(
                  'Create your first video to see it here!',
                  style: TextStyle(color: Colors.grey),
                ),
              ],
            ),
          );
        }

        debugPrint('🎬 Displaying ${videos.length} videos in list');
        return ListView.separated(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: videos.length,
          separatorBuilder: (context, index) => const SizedBox(height: 16),
          itemBuilder: (context, index) {
            final video = videos[index];
            debugPrint('📋 Building video item $index: ${video.topic}');
            
            return GlassmorphicContainer(
              width: double.infinity,
              height: 100,
              borderRadius: 16,
              blur: 20,
              alignment: Alignment.center,
              border: 2,
              linearGradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Colors.white.withOpacity(0.1),
                  Colors.white.withOpacity(0.05),
                ],
              ),
              borderGradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Colors.white.withOpacity(0.5),
                  Colors.white.withOpacity(0.2),
                ],
              ),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  borderRadius: BorderRadius.circular(16),
                  onTap: () {
                    debugPrint('▶️ Playing video: ${video.topic}');
                    _playVideo(context, video);
                  },
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Row(
                      children: [
                        _buildThumbnail(context, video),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                video.topic,
                                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                  fontWeight: FontWeight.w600,
                                ),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                              const SizedBox(height: 4),
                              Row(
                                children: [
                                  Icon(
                                    LucideIcons.clock,
                                    size: 14,
                                    color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    '${video.duration}s',
                                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                      color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Icon(
                                    LucideIcons.calendar,
                                    size: 14,
                                    color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    _formatDate(video.createdAt),
                                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                      color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                        Icon(
                          LucideIcons.playCircle,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildThumbnail(BuildContext context, FirebaseVideo video) {
    debugPrint('🖼️ Building thumbnail for video: ${video.topic}');
    
    if (video.thumbnailUrl != null && video.thumbnailUrl!.isNotEmpty) {
      debugPrint('🌐 Using network thumbnail: ${video.thumbnailUrl}');
      return ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: Image.network(
          video.thumbnailUrl!,
          width: 80,
          height: 80,
          fit: BoxFit.cover,
          loadingBuilder: (context, child, loadingProgress) {
            if (loadingProgress == null) {
              debugPrint('✅ Thumbnail loaded successfully');
              return child;
            }
            debugPrint('⏳ Loading thumbnail: ${loadingProgress.cumulativeBytesLoaded}/${loadingProgress.expectedTotalBytes}');
            return _buildPlaceholderThumbnail(context);
          },
          errorBuilder: (context, error, stackTrace) {
            debugPrint('❌ Thumbnail load failed: $error');
            return _buildPlaceholderThumbnail(context);
          },
        ),
      );
    }
    
    debugPrint('📦 Using placeholder thumbnail');
    return _buildPlaceholderThumbnail(context);
  }

  Widget _buildPlaceholderThumbnail(BuildContext context) {
    return Container(
      width: 80,
      height: 80,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primary.withOpacity(0.2),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Icon(
        LucideIcons.video,
        color: Theme.of(context).colorScheme.primary,
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);
    
    if (difference.inDays > 7) {
      return DateFormat('MMM d, yyyy').format(date);
    } else if (difference.inDays > 0) {
      return '${difference.inDays} days ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours} hours ago';
    } else {
      return 'Today';
    }
  }

  void _playVideo(BuildContext context, FirebaseVideo video) {
    debugPrint('🎯 Attempting to play video: ${video.topic}');
    debugPrint('📹 Video URL: ${video.videoUrl}');
    debugPrint('💾 Local path: ${video.localPath}');
    debugPrint('📊 Status: ${video.status}');
    
    if (video.status != 'completed') {
      debugPrint('⛔ Video not ready for playback. Status: ${video.status}');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Video is not ready yet (Status: ${video.status})'))
      );
      return;
    }

    final videoPath = video.videoUrl ?? video.localPath;
    if (videoPath == null || videoPath.isEmpty) {
      debugPrint('❌ No video path available for playback');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Video file not available'))
      );
      return;
    }

    debugPrint('🚀 Navigating to video player with path: $videoPath');
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => VideoPlayerScreen(
          videoPath: videoPath,
          title: video.topic,
        ),
      ),
    );
  }
}
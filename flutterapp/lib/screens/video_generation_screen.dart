import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:glassmorphism/glassmorphism.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../providers/video_provider.dart';
import 'video_player_screen.dart';

class VideoGenerationScreen extends ConsumerStatefulWidget {
  final String topic;

  const VideoGenerationScreen({
    Key? key,
    required this.topic,
  }) : super(key: key);

  @override
  ConsumerState<VideoGenerationScreen> createState() => _VideoGenerationScreenState();
}

class _VideoGenerationScreenState extends ConsumerState<VideoGenerationScreen> {
  @override
  void initState() {
    super.initState();
    // Start generating video when screen loads
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(videoProvider.notifier).generateVideo(widget.topic);
    });
  }

  @override
  void dispose() {
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final videoState = ref.watch(videoProvider);
    final currentVideo = videoState.currentVideo;

    // Show loading indicator while initializing
    if (currentVideo == null && !videoState.isLoading && videoState.error == null) {
      return Scaffold(
        backgroundColor: const Color(0xFF0F0F23),
        body: const Center(
          child: CircularProgressIndicator(color: Color(0xFF6366F1)),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFF0F0F23),
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: Container(
          margin: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.3),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white.withOpacity(0.2)),
          ),
          child: IconButton(
            icon: const Icon(LucideIcons.arrowLeft, color: Colors.white, size: 20),
            onPressed: () => Navigator.pop(context),
          ),
        ),
        title: const Text(
          'Creating Your Video',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w600,
            fontSize: 18,
          ),
        ),
        centerTitle: true,
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [
              Color(0xFF0F0F23),
              Color(0xFF1E1B4B),
              Color(0xFF312E81),
            ],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: SingleChildScrollView(
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: MediaQuery.of(context).size.height - 
                            MediaQuery.of(context).padding.top - 
                            MediaQuery.of(context).padding.bottom - 48, // Account for padding
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    // Topic display with enhanced design
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [
                            Colors.white.withOpacity(0.1),
                            Colors.white.withOpacity(0.05),
                          ],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: Colors.white.withOpacity(0.2),
                          width: 1,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.2),
                            blurRadius: 20,
                            offset: const Offset(0, 5),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: const Color(0xFF6366F1).withOpacity(0.2),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              LucideIcons.video,
                              color: Color(0xFF6366F1),
                              size: 24,
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Topic',
                                  style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 12,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  widget.topic,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                  ),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ).animate().fadeIn().slideY(begin: -0.2, duration: 600.ms),
                    
                    const SizedBox(height: 40),
                    
                    // Progress visualization with enhanced design
                    if (currentVideo != null) 
                      _buildProgressIndicator(currentVideo, theme)
                          .animate().scale(begin: const Offset(0.8, 0.8), duration: 800.ms)
                          .then().shimmer(duration: 2000.ms),
                    
                    const SizedBox(height: 30),
                    
                    // Status message with animation
                    if (currentVideo != null) 
                      _buildStatusMessage(currentVideo, theme)
                          .animate().fadeIn(delay: 300.ms),
                    
                    const SizedBox(height: 40),
                    
                    // Action buttons with priority for URL streaming
                    if (currentVideo?.status == 'completed') 
                      _buildCompletionActions(context, theme, currentVideo!)
                          .animate().slideY(begin: 0.3, duration: 600.ms),
                    
                    // Show "Stream Now" button as soon as URL is available
                    if (currentVideo?.videoUrl != null && currentVideo?.status != 'completed')
                      _buildStreamNowButton(context, theme, currentVideo!)
                          .animate().scale(begin: const Offset(0.9, 0.9), duration: 1000.ms)
                          .then().fadeIn(duration: 500.ms),
                    
                    if (videoState.error != null)
                      _buildErrorState(context, theme, videoState.error!)
                          .animate().shake(),
                    
                    // Show loading indicator when initializing
                    if (videoState.isLoading && currentVideo == null)
                      const Padding(
                        padding: EdgeInsets.all(40.0),
                        child: CircularProgressIndicator(color: Color(0xFF6366F1)),
                      ).animate().scale(
                        begin: const Offset(0.8, 0.8),
                        end: const Offset(1.2, 1.2),
                        duration: 1000.ms,
                      ).then().scale(
                        begin: const Offset(1.2, 1.2),
                        end: const Offset(1.0, 1.0),
                        duration: 1000.ms,
                      ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildProgressIndicator(Video video, ThemeData theme) {
    return Stack(
      alignment: Alignment.center,
      children: [
        Container(
          width: 200,
          height: 200,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(
              colors: [
                const Color(0xFF6366F1).withOpacity(0.1),
                const Color(0xFF8B5CF6).withOpacity(0.1),
              ],
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF6366F1).withOpacity(0.3),
                blurRadius: 30,
                offset: const Offset(0, 10),
              ),
            ],
          ),
        ),
        SizedBox(
          width: 180,
          height: 180,
          child: CircularProgressIndicator(
            value: video.progress / 100,
            strokeWidth: 6,
            backgroundColor: Colors.white.withOpacity(0.1),
            valueColor: AlwaysStoppedAnimation<Color>(
              video.status == 'failed' 
                ? const Color(0xFFEF4444)
                : video.status == 'completed'
                  ? const Color(0xFF10B981)
                  : const Color(0xFF6366F1),
            ),
            strokeCap: StrokeCap.round,
          ),
        ),
        Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (video.status == 'generating' || video.status == 'downloading')
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: const LinearGradient(
                    colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF6366F1).withOpacity(0.4),
                      blurRadius: 15,
                      offset: const Offset(0, 5),
                    ),
                  ],
                ),
                child: const Center(
                  child: SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  ),
                ),
              )
            else
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _getStatusColor(video.status, theme),
                  boxShadow: [
                    BoxShadow(
                      color: _getStatusColor(video.status, theme).withOpacity(0.4),
                      blurRadius: 15,
                      offset: const Offset(0, 5),
                    ),
                  ],
                ),
                child: Icon(
                  _getStatusIcon(video.status),
                  size: 20,
                  color: Colors.white,
                ),
              ),
            const SizedBox(height: 8),
            Text(
              '${video.progress}%',
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              _getDetailedStatus(video),
              style: TextStyle(
                fontSize: 11,
                color: Colors.white.withOpacity(0.7),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildStreamNowButton(BuildContext context, ThemeData theme, Video video) {
    return Container(
      width: double.infinity,
      height: 50,
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF10B981), Color(0xFF059669)],
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF10B981).withOpacity(0.4),
            blurRadius: 15,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => _streamVideoNow(context, video),
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(LucideIcons.zap, color: Colors.white, size: 18),
              SizedBox(width: 8),
              Text(
                'Stream Now (Fast)',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusMessage(Video video, ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        children: [
          Text(
            _getStatusMessage(video.status),
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 6),
          Text(
            _getSubStatusMessage(video),
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 13,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  Widget _buildCompletionActions(BuildContext context, ThemeData theme, Video video) {
    return Column(
      children: [
        // Primary action - Watch Video
        Container(
          width: double.infinity,
          height: 50,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
            ),
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF6366F1).withOpacity(0.4),
                blurRadius: 15,
                offset: const Offset(0, 5),
              ),
            ],
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: () => _playVideoOptimized(context, video),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(LucideIcons.play, color: Colors.white, size: 18),
                  SizedBox(width: 8),
                  Text(
                    'Watch Video',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        
        // Secondary actions
        Row(
          children: [
            Expanded(
              child: Container(
                height: 44,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.white.withOpacity(0.3)),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    borderRadius: BorderRadius.circular(14),
                    onTap: () => Navigator.pop(context),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(LucideIcons.plus, color: Colors.white, size: 16),
                        SizedBox(width: 6),
                        Text(
                          'New Video',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Container(
                height: 44,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.white.withOpacity(0.3)),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    borderRadius: BorderRadius.circular(14),
                    onTap: () => _shareVideo(context, video),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(LucideIcons.share2, color: Colors.white, size: 16),
                        SizedBox(width: 6),
                        Text(
                          'Share',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildErrorState(BuildContext context, ThemeData theme, String error) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        children: [
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFFEF4444).withOpacity(0.1),
            ),
            child: const Icon(
              LucideIcons.alertCircle,
              size: 30,
              color: Color(0xFFEF4444),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Oops! Something went wrong',
            style: TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            error,
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 13,
            ),
            textAlign: TextAlign.center,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                height: 44,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF6366F1), Color(0xFF8B5CF6)],
                  ),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    borderRadius: BorderRadius.circular(14),
                    onTap: () {
                      ref.read(videoProvider.notifier).clearError();
                      ref.read(videoProvider.notifier).generateVideo(widget.topic);
                    },
                    child: const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      child: Text(
                        'Try Again',
                        style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Container(
                height: 44,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.white.withOpacity(0.3)),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    borderRadius: BorderRadius.circular(14),
                    onTap: () => Navigator.pop(context),
                    child: const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      child: Text(
                        'Go Back',
                        style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // OPTIMIZED: Stream video URL immediately for fastest playback
  void _streamVideoNow(BuildContext context, Video video) {
    if (video.videoUrl != null) {
      Navigator.push(
        context, 
        MaterialPageRoute(
          builder: (context) => VideoPlayerScreen(
            videoPath: video.videoUrl!, // Use URL directly for streaming
            title: widget.topic,
          ),
        ),
      );
    }
  }

  // OPTIMIZED: Priority-based video playing
  void _playVideoOptimized(BuildContext context, Video video) {
    // Priority 1: Stream URL immediately (fastest)
    if (video.videoUrl != null) {
      Navigator.push(
        context, 
        MaterialPageRoute(
          builder: (context) => VideoPlayerScreen(
            videoPath: video.videoUrl!, // Stream from URL
            title: widget.topic,
          ),
        ),
      );
      return;
    }
    
    // Priority 2: Local file if available
    if (video.localPath != null && File(video.localPath!).existsSync()) {
      Navigator.push(
        context, 
        MaterialPageRoute(
          builder: (context) => VideoPlayerScreen(
            videoPath: video.localPath!,
            title: widget.topic,
          ),
        ),
      );
      return;
    }
    
    // Fallback: Show message
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Video is still being prepared...'),
        backgroundColor: Color(0xFF6366F1),
      ),
    );
  }

  void _shareVideo(BuildContext context, Video video) {
    // TODO: Implement share functionality with URL priority
    final shareContent = video.videoUrl ?? video.localPath ?? 'Video not ready';
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Ready to share: $shareContent'),
        backgroundColor: const Color(0xFF10B981),
      ),
    );
  }

  IconData _getStatusIcon(String status) {
    switch (status) {
      case 'completed':
        return LucideIcons.checkCircle;
      case 'failed':
        return LucideIcons.xCircle;
      default:
        return LucideIcons.loader;
    }
  }

  Color _getStatusColor(String status, ThemeData theme) {
    switch (status) {
      case 'completed':
        return const Color(0xFF10B981);
      case 'failed':
        return const Color(0xFFEF4444);
      default:
        return const Color(0xFF6366F1);
    }
  }

  String _getStatusMessage(String status) {
    switch (status) {
      case 'generating':
        return 'AI is crafting your video...';
      case 'downloading':
        return 'Almost ready to stream!';
      case 'completed':
        return 'Your video is ready!';
      case 'failed':
        return 'Generation failed';
      default:
        return 'Processing your request...';
    }
  }

  String _getSubStatusMessage(Video video) {
    if (video.videoUrl != null && video.status != 'completed') {
      return 'Stream available now! Download continuing in background.';
    }
    switch (video.status) {
      case 'generating':
        return 'This usually takes 3-5 minutes...';
      case 'downloading':
        return 'You can stream while download completes';
      case 'completed':
        return 'Best quality available for streaming and offline viewing';
      default:
        return '';
    }
  }

  String _getDetailedStatus(Video video) {
    if (video.videoUrl != null && video.status != 'completed') {
      return 'Ready to stream';
    }
    switch (video.status) {
      case 'generating':
        return 'Creating content...';
      case 'downloading':
        return 'Optimizing quality...';
      case 'completed':
        return 'Complete';
      default:
        return 'Processing...';
    }
  }
}
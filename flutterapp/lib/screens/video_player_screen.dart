import 'package:flutter/material.dart';
import 'package:better_player_plus/better_player_plus.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:share_plus/share_plus.dart';
import 'dart:io';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../widgets/recent_videos_list.dart';

class VideoPlayerScreen extends StatefulWidget {
  final String videoPath;
  final String? title;

  const VideoPlayerScreen({
    Key? key,
    required this.videoPath,
    this.title,
  }) : super(key: key);

  @override
  State<VideoPlayerScreen> createState() => _VideoPlayerScreenState();
}

class _VideoPlayerScreenState extends State<VideoPlayerScreen> {
  BetterPlayerController? _betterPlayerController;
  bool _isLoading = true;
  bool _hasError = false;
  String _errorMessage = '';
  bool _isNetworkUrl = false;

  @override
  void initState() {
    super.initState();
    _initializePlayer();
  }

  Future<void> _initializePlayer() async {
    try {
      // Determine if it's a network URL or local file
      _isNetworkUrl = widget.videoPath.startsWith('http');
      debugPrint(_isNetworkUrl 
          ? '🌐 Loading NETWORK video: ${widget.videoPath}'
          : '💾 Loading LOCAL file: ${widget.videoPath}');

      BetterPlayerConfiguration config = BetterPlayerConfiguration(
        autoPlay: false,
        aspectRatio: 16 / 9,
        fit: BoxFit.contain,
        controlsConfiguration: BetterPlayerControlsConfiguration(
          enablePlayPause: true,
          enableFullscreen: true,
          enableSkips: true,
          skipBackIcon: LucideIcons.rewind,
          skipForwardIcon: LucideIcons.fastForward,
          playIcon: LucideIcons.play,
          pauseIcon: LucideIcons.pause,
          fullscreenEnableIcon: LucideIcons.maximize,
          fullscreenDisableIcon: LucideIcons.minimize,
          iconsColor: Colors.white,
          controlBarColor: Colors.black.withOpacity(0.7),
          controlBarHeight: 50,
          progressBarPlayedColor: const Color(0xFF6366F1),
          progressBarBufferedColor: Colors.white38,
          progressBarBackgroundColor: Colors.white24,
          progressBarHandleColor: const Color(0xFF6366F1),
        ),
      );

      BetterPlayerDataSource dataSource;

      if (_isNetworkUrl) {
        // NETWORK URL - use network data source
        dataSource = BetterPlayerDataSource(
          BetterPlayerDataSourceType.network,
          widget.videoPath,
          bufferingConfiguration: BetterPlayerBufferingConfiguration(
            minBufferMs: 10000,
            maxBufferMs: 30000,
            bufferForPlaybackMs: 5000,
            bufferForPlaybackAfterRebufferMs: 10000,
          ),
        );
      } else {
        // LOCAL FILE - check if file exists first
        final file = File(widget.videoPath);
        final exists = await file.exists();
        
        if (!exists) {
          throw Exception('Local file does not exist: ${widget.videoPath}');
        }

        dataSource = BetterPlayerDataSource(
          BetterPlayerDataSourceType.file,
          widget.videoPath,
        );
      }

      _betterPlayerController = BetterPlayerController(
        config,
        betterPlayerDataSource: dataSource,
      );

      // Add event listeners for better debugging
      _betterPlayerController?.addEventsListener((event) {
        if (event.betterPlayerEventType == BetterPlayerEventType.initialized) {
          setState(() => _isLoading = false);
        } else if (event.betterPlayerEventType == BetterPlayerEventType.exception) {
          final error = event.parameters?['exception'] ?? 'Unknown error';
          _handleError('Playback error: $error');
        }
      });

      // Set timeout for initialization
      Future.delayed(const Duration(seconds: 15), () {
        if (_isLoading && mounted) {
          _handleError('Video loading timeout');
        }
      });

    } catch (e) {
      _handleError('Failed to initialize player: $e');
    }
  }

  void _handleError(String message) {
    debugPrint('❌ Error: $message');
    if (mounted) {
      setState(() {
        _hasError = true;
        _errorMessage = message;
        _isLoading = false;
      });
    }
  }

  Future<void> _retryPlayback() async {
    setState(() {
      _isLoading = true;
      _hasError = false;
      _errorMessage = '';
    });
    
    _betterPlayerController?.dispose();
    _betterPlayerController = null;
    
    await _initializePlayer();
  }

  @override
  void dispose() {
    _betterPlayerController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F0F23),
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          widget.title ?? "Educational Video",
          style: const TextStyle(
            fontSize: 18, 
            fontWeight: FontWeight.w600,
            color: Colors.white,
          ),
        ),
        centerTitle: true,
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
        child: Column(
          children: [
            /// Video Player Section
            Container(
              margin: const EdgeInsets.fromLTRB(16, 100, 16, 16),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.3),
                    blurRadius: 20,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: AspectRatio(
                  aspectRatio: 16 / 9,
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.black,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: _buildVideoPlayer(),
                  ),
                ),
              ),
            ),

            /// Error/Status Display
            if (_hasError) _buildErrorSection(),

            /// Source Indicator
            if (!_isLoading && !_hasError)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0),
                child: Text(
                  _isNetworkUrl ? '🌐 Streaming from network' : '💾 Playing from device',
                  style: TextStyle(
                    color: _isNetworkUrl ? Colors.blue : Colors.green,
                    fontSize: 12,
                  ),
                ),
              ),

            const SizedBox(height: 16),

            /// Video History Section
            if (!_isLoading && !_hasError) _buildVideoHistorySection(),
          ],
        ),
      ),
      floatingActionButton: Container(
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFFEC4899), Color(0xFFF472B6)],
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFFEC4899).withOpacity(0.3),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: FloatingActionButton(
          backgroundColor: Colors.transparent,
          elevation: 0,
          child: const Icon(LucideIcons.share2, color: Colors.white),
          onPressed: () {
            Share.share("Check out this video: ${widget.title ?? "Untitled"}");
          },
        ),
      ),
    );
  }

  Widget _buildVideoPlayer() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: Color(0xFF6366F1)),
            SizedBox(height: 16),
            Text("Loading video...", style: TextStyle(color: Colors.white)),
          ],
        ),
      );
    }

    if (_hasError) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(LucideIcons.alertTriangle, color: Colors.red, size: 48),
            const SizedBox(height: 16),
            const Text(
              "Unable to play video",
              style: TextStyle(color: Colors.white, fontSize: 16),
            ),
            const SizedBox(height: 8),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Text(
                _errorMessage,
                style: const TextStyle(color: Colors.white54, fontSize: 12),
                textAlign: TextAlign.center,
                maxLines: 3,
              ),
            ),
          ],
        ),
      );
    }

    return BetterPlayer(controller: _betterPlayerController!);
  }

  Widget _buildErrorSection() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.red.withOpacity(0.2),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.red),
        ),
        child: Column(
          children: [
            const Row(
              children: [
                Icon(LucideIcons.alertTriangle, color: Colors.red, size: 16),
                SizedBox(width: 8),
                Text("Playback Error", style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 8),
            Text(_errorMessage, style: const TextStyle(color: Colors.red, fontSize: 12)),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: _retryPlayback,
              style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
              child: const Text("Retry", style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVideoHistorySection() {
    return Expanded(
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 20,
              offset: const Offset(0, -5)
            ),
          ],
        ),
        child: Column(
          children: [
            // Section Header
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 16),
              child: Row(
                children: [
                  const Icon(LucideIcons.history, color: Color(0xFF6366F1), size: 24),
                  const SizedBox(width: 12),
                  Text(
                    'Your Video History',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Colors.black,
                    ),
                  ),
                ],
              ),
            ),
            
            // Divider
            const Divider(height: 1, color: Colors.grey),
            
            // Video History List
            Expanded(
              child: Consumer(
                builder: (context, ref, child) {
                  return Container(
                    color: Colors.white, // Ensure white background
                    child: const RecentVideosList(),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:glassmorphism/glassmorphism.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/video_provider.dart';
import '../providers/auth_provider.dart';
import '../screens/video_generation_screen.dart';
import '../screens/auth_screen.dart';

class TopicInputCard extends ConsumerStatefulWidget {
  final Function(String)? onTemplateSelected;

  const TopicInputCard({Key? key, this.onTemplateSelected}) : super(key: key);

  @override
  ConsumerState<TopicInputCard> createState() => _TopicInputCardState();
}

class _TopicInputCardState extends ConsumerState<TopicInputCard> {
  final TextEditingController _controller = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  bool _isFocused = false;

  @override
  void initState() {
    super.initState();
    _focusNode.addListener(() {
      setState(() {
        _isFocused = _focusNode.hasFocus;
      });
    });

    // Listen for template selections if callback is provided
    if (widget.onTemplateSelected != null) {
      // This allows external components to set the text
    }
  }

  // Add this method to set text from outside
  void setTopicText(String text) {
    setState(() {
      _controller.text = text;
      _focusNode.requestFocus(); // Focus on the input field
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _generateVideo() async {
    print('🔍 _generateVideo called');
    print('📝 Text content: "${_controller.text.trim()}"');
    
    if (_controller.text.trim().isEmpty) {
      print('❌ Text is empty, returning early');
      return;
    }
    
    final authState = ref.read(authProvider);
    print('🔐 Auth state: ${authState.isAuthenticated}');
    
    if (!authState.isAuthenticated) {
      print('🚪 Navigating to auth screen');
      final result = await Navigator.push<bool>(
        context,
        MaterialPageRoute(
          builder: (context) => const AuthScreen(),
        ),
      );
      
      print('🔙 Auth screen result: $result');
      print('🔐 Auth state after return: ${ref.read(authProvider).isAuthenticated}');
      
      if (result == true || (mounted && ref.read(authProvider).isAuthenticated)) {
        print('✅ Proceeding to video generation');
        _proceedToVideoGeneration();
      } else {
        print('❌ Authentication failed or cancelled');
      }
      return;
    }
    
    print('✅ User authenticated, proceeding directly');
    _proceedToVideoGeneration();
  }

  void _proceedToVideoGeneration() {
    print('🎬 Navigating to video generation screen');
    print('📝 Topic: "${_controller.text.trim()}"');
    
    try {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => VideoGenerationScreen(
            topic: _controller.text.trim(),
          ),
        ),
      );
      print('✅ Navigation initiated successfully');
    } catch (e) {
      print('❌ Navigation error: $e');
    }
  }

  void _clearText() {
    setState(() {
      _controller.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final videoState = ref.watch(videoProvider);
    final authState = ref.watch(authProvider);
    
    return ConstrainedBox(
      constraints: const BoxConstraints(
        minWidth: 300,
        maxWidth: 400,
        minHeight: 160,
        maxHeight: 200,
      ),
      child: GlassmorphicContainer(
        width: double.infinity,
        height: 180,
        borderRadius: 24,
        blur: 20,
        alignment: Alignment.center,
        border: 2,
        linearGradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            theme.colorScheme.surface.withOpacity(0.8),
            theme.colorScheme.surface.withOpacity(0.4),
          ],
        ),
        borderGradient: LinearGradient(
          colors: _isFocused 
            ? [
                theme.colorScheme.primary.withOpacity(0.6),
                theme.colorScheme.secondary.withOpacity(0.6),
              ]
            : [
                Colors.white.withOpacity(0.3),
                Colors.white.withOpacity(0.1),
              ],
        ),
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primary.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      LucideIcons.sparkles,
                      color: theme.colorScheme.primary,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          authState.isAuthenticated 
                            ? 'What would you like to learn?' 
                            : 'Welcome to VideoGen!',
                          style: theme.textTheme.bodyLarge?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          authState.isAuthenticated 
                            ? 'Enter a topic to generate a video'
                            : 'Sign in to create educational videos',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.primary,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  if (!authState.isAuthenticated)
                    IconButton(
                      onPressed: () {
                        print('🔐 Login button tapped');
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const AuthScreen(),
                          ),
                        );
                      },
                      icon: Icon(
                        LucideIcons.logIn,
                        size: 20,
                        color: theme.colorScheme.primary,
                      ),
                      tooltip: 'Sign In',
                    ),
                ],
              ),
              
              const SizedBox(height: 16),
              
              // Text Input with proper constraints
              Flexible(
                child: Container(
                  constraints: const BoxConstraints(
                    minHeight: 60,
                    maxHeight: 80,
                  ),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surface.withOpacity(0.6),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: _isFocused 
                        ? theme.colorScheme.primary.withOpacity(0.5)
                        : Colors.transparent,
                      width: 2,
                    ),
                  ),
                  child: authState.isAuthenticated
                    ? TextField(
                        controller: _controller,
                        focusNode: _focusNode,
                        maxLines: 2,
                        onChanged: (value) {
                          // Force rebuild when text changes to update button state
                          setState(() {});
                        },
                        decoration: InputDecoration(
                          hintText: 'e.g., "Explain quantum physics"',
                          hintStyle: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.colorScheme.onSurface.withOpacity(0.5),
                          ),
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 12,
                          ),
                          suffixIcon: Container(
                            width: 100,
                            padding: const EdgeInsets.only(right: 8),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                // Clear button
                                if (_controller.text.isNotEmpty)
                                  GestureDetector(
                                    onTap: () {
                                      print('🗑️ Clear button tapped');
                                      _clearText();
                                    },
                                    child: Container(
                                      padding: const EdgeInsets.all(4),
                                      child: Icon(
                                        LucideIcons.x,
                                        size: 16,
                                        color: theme.colorScheme.onSurface.withOpacity(0.5),
                                      ),
                                    ),
                                  ),
                                
                                const SizedBox(width: 4),
                                
                                // Send button
                                GestureDetector(
                                  onTap: () {
                                    print('🔴 SEND BUTTON TAPPED!');
                                    print('📝 Text: "${_controller.text}"');
                                    print('🔒 Auth: ${authState.isAuthenticated}');
                                    print('⏳ Loading: ${videoState.isLoading}');
                                    
                                    if (_controller.text.trim().isEmpty) {
                                      print('❌ Text is empty - showing snackbar');
                                      ScaffoldMessenger.of(context).showSnackBar(
                                        const SnackBar(
                                          content: Text('Please enter a topic first'),
                                          duration: Duration(seconds: 2),
                                        ),
                                      );
                                      return;
                                    }
                                    
                                    if (videoState.isLoading) {
                                      print('❌ Video is loading - ignoring tap');
                                      return;
                                    }
                                    
                                    print('✅ Calling _generateVideo()');
                                    _generateVideo();
                                  },
                                  child: Container(
                                    padding: const EdgeInsets.all(8),
                                    decoration: BoxDecoration(
                                      gradient: _controller.text.trim().isEmpty
                                        ? null
                                        : LinearGradient(
                                            colors: [
                                              theme.colorScheme.primary,
                                              theme.colorScheme.secondary,
                                            ],
                                          ),
                                      color: _controller.text.trim().isEmpty
                                        ? theme.colorScheme.onSurface.withOpacity(0.2)
                                        : null,
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: videoState.isLoading
                                      ? SizedBox(
                                          width: 14,
                                          height: 14,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                            valueColor: AlwaysStoppedAnimation<Color>(
                                              Colors.white,
                                            ),
                                          ),
                                        )
                                      : Icon(
                                          LucideIcons.send,
                                          color: _controller.text.trim().isEmpty
                                            ? theme.colorScheme.onSurface.withOpacity(0.5)
                                            : Colors.white,
                                          size: 14,
                                        ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        onSubmitted: (value) {
                          print('📝 TextField submitted: "$value"');
                          _generateVideo();
                        },
                        textInputAction: TextInputAction.send,
                        style: theme.textTheme.bodyLarge,
                      )
                    : GestureDetector(
                        onTap: () {
                          print('🔐 Auth container tapped');
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => const AuthScreen(),
                            ),
                          );
                        },
                        child: Container(
                          width: double.infinity,
                          padding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 12,
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  'Tap to sign in and start creating',
                                  style: theme.textTheme.bodyMedium?.copyWith(
                                    color: theme.colorScheme.onSurface.withOpacity(0.5),
                                  ),
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.all(6),
                                decoration: BoxDecoration(
                                  gradient: LinearGradient(
                                    colors: [
                                      theme.colorScheme.primary,
                                      theme.colorScheme.secondary,
                                    ],
                                  ),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Icon(
                                  LucideIcons.arrowRight,
                                  color: Colors.white,
                                  size: 14,
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
        ),
      ),
    );
  }
}
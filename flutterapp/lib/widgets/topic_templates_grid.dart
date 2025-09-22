import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:glassmorphism/glassmorphism.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../providers/video_provider.dart';
import '../providers/auth_provider.dart';
import '../screens/video_generation_screen.dart';

class TopicTemplatesGrid extends StatelessWidget {
  final Function(String)? onTemplateSelected;


  const TopicTemplatesGrid({Key? key, this.onTemplateSelected}) : super(key: key);

  void _handleTemplateSelection(BuildContext context, String templateTitle) {
    // First scroll to top (if callback provided)
    if (onTemplateSelected != null) {
      onTemplateSelected!(templateTitle);
    }
    
    // Show confirmation or navigate directly
    _showTemplateConfirmation(context, templateTitle);
  }

  void _showTemplateConfirmation(BuildContext context, String templateTitle) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          backgroundColor: Theme.of(context).colorScheme.surface,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: Text(
            'Use Template?',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          content: Text(
            'Generate a video about "$templateTitle"?',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(
                'Cancel',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                ),
              ),
            ),
            ElevatedButton(
              onPressed: () {
                print("Generating video for template: $templateTitle");
                Navigator.pop(context);
                _navigateToVideoGeneration(context, templateTitle);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.primary,
                foregroundColor: Theme.of(context).colorScheme.onPrimary,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text('Generate Video'),
            ),
          ],
        );
      },
    );
  }

  void _navigateToVideoGeneration(BuildContext context, String templateTitle) {
    // Navigate to video generation screen with the template title
    print("Navigating to video generation for topic: $templateTitle");  
 Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => VideoGenerationScreen(
            topic: templateTitle,
          ),
        ),
      );
  }

  @override
  Widget build(BuildContext context) {
    final templates = [
      {
        'title': 'Introduction to Algebra',
        'icon': LucideIcons.functionSquare,
        'color': Colors.blue,
        'description': 'Learn basic algebraic concepts and equations',
      },
      {
        'title': 'World History Timeline',
        'icon': LucideIcons.history,
        'color': Colors.orange,
        'description': 'Explore major events in world history',
      },
      {
        'title': 'Photosynthesis Process',
        'icon': LucideIcons.leaf,
        'color': Colors.green,
        'description': 'Understand how plants convert light to energy',
      },
      {
        'title': 'Grammar Basics',
        'icon': LucideIcons.bookOpen,
        'color': Colors.purple,
        'description': 'Master essential grammar rules and structures',
      },
      {
        'title': 'Solar System',
        'icon': LucideIcons.globe,
        'color': Colors.indigo,
        'description': 'Discover planets and celestial bodies',
      },
      {
        'title': 'Human Anatomy',
        'icon': LucideIcons.heart,
        'color': Colors.red,
        'description': 'Learn about the human body systems',
      },
    ];

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 16,
        mainAxisSpacing: 16,
        childAspectRatio: 0.85, // Changed from 1.3 to 0.85 to provide more height
      ),
      itemCount: templates.length,
      itemBuilder: (context, index) {
        final template = templates[index];
        
        return GlassmorphicContainer(
          width: double.infinity,
          height: double.infinity, // Let it use available height
          borderRadius: 20,
          blur: 20,
          alignment: Alignment.center,
          border: 2,
          linearGradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Theme.of(context).colorScheme.surface.withOpacity(0.8),
              Theme.of(context).colorScheme.surface.withOpacity(0.4),
            ],
          ),
          borderGradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Colors.white.withOpacity(0.3),
              Colors.white.withOpacity(0.1),
            ],
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(20),
              onTap: () => _handleTemplateSelection(context, template['title'] as String),
              onLongPress: () {
                _showTemplateDetails(context, template);
              },
              child: Padding(
                padding: const EdgeInsets.all(12.0), // Reduced padding from 16 to 12
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  mainAxisSize: MainAxisSize.min, // Added to prevent overflow
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: (template['color'] as Color).withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        template['icon'] as IconData,
                        color: template['color'] as Color,
                        size: 20, // Reduced from 24 to 20
                      ),
                    ),
                    const SizedBox(height: 8), // Reduced from 12 to 8
                    Flexible( // Wrapped with Flexible to prevent overflow
                      child: Text(
                        template['title'] as String,
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                          fontSize: 11, // Reduced from 12 to 11
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Flexible( // Wrapped with Flexible to prevent overflow
                      child: Text(
                        template['description'] as String,
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          fontSize: 9, // Reduced from 10 to 9
                          color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ).animate().scale(delay: (index * 100).ms);
      },
    );
  }

  void _showTemplateDetails(BuildContext context, Map<String, dynamic> template) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true, // Added to prevent overflow in bottom sheet
      builder: (context) => Container(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.of(context).size.height * 0.8, // Limit height
        ),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        ),
        padding: const EdgeInsets.all(24),
        child: SingleChildScrollView( // Added scroll view for safety
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: (template['color'] as Color).withOpacity(0.2),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(
                  template['icon'] as IconData,
                  color: template['color'] as Color,
                  size: 32,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                template['title'] as String,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                template['description'] as String,
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.pop(context);
                    _handleTemplateSelection(context, template['title'] as String);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: template['color'] as Color,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: const Text('Use This Template'),
                ),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(
                  'Cancel',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
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
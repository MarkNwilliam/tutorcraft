from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService
from manim_voiceover.services.azure import AzureService
import json
import requests
import tempfile
import os
import io
from PIL import Image
from typing import Optional 
from manim.opengl import *

class TimelineAnimation(VoiceoverScene, MovingCameraScene):
    def __init__(self):
        super().__init__()
        self.headers = {
            'User-Agent': 'TimelineAnimation/1.0 (https://example.com; contact@example.com)'
        }
    
    def get_wikimedia_image(self, search_term: str) -> Optional[str]:
        """
        Improved image fetcher from Wikimedia with better error handling and file management.
        
        Args:
            search_term: Term to search for images on Wikimedia
            
        Returns:
            Path to downloaded image file or None if failed
        """
        print(f"Searching Wikimedia for: {search_term}")
        
        try:
            # Step 1: Search Wikipedia for relevant articles
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": search_term,
                "srlimit": 3
            }
            
            response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params=search_params,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('query', {}).get('search'):
                print("No matching articles found")
                return None
                
            article_title = data['query']['search'][0]['title']
            print(f"Found article: {article_title}")
            
            # Step 2: Get images from the article
            img_params = {
                "action": "query",
                "format": "json",
                "titles": article_title,
                "prop": "images",
                "imlimit": 10
            }
            
            img_response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params=img_params,
                headers=self.headers
            )
            img_response.raise_for_status()
            img_data = img_response.json()
            
            pages = img_data['query']['pages']
            page_id = list(pages.keys())[0]
            
            if 'images' not in pages[page_id]:
                print("No images in article")
                return None
                
            # Filter out SVGs and logos
            image_titles = [
                img['title'] for img in pages[page_id]['images']
                if not img['title'].lower().endswith('.svg')
                and 'logo' not in img['title'].lower()
                and 'icon' not in img['title'].lower()
            ]
            
            if not image_titles:
                print("No suitable images found")
                return None
                
            # Step 3: Get image URL
            img_info_params = {
                "action": "query",
                "format": "json",
                "titles": image_titles[0],
                "prop": "imageinfo",
                "iiprop": "url"
            }
            
            img_info_response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params=img_info_params,
                headers=self.headers
            )
            img_info_response.raise_for_status()
            img_info_data = img_info_response.json()
            
            img_info_pages = img_info_data['query']['pages']
            img_info_id = list(img_info_pages.keys())[0]
            
            if 'imageinfo' not in img_info_pages[img_info_id]:
                print("No image info available")
                return None
                
            img_url = img_info_pages[img_info_id]['imageinfo'][0]['url']
            print(f"Found image URL: {img_url}")
            
            # Step 4: Download and process image
            img_response = requests.get(img_url, headers=self.headers)
            img_response.raise_for_status()
            
            # Convert to RGB if needed and save as PNG
            with Image.open(io.BytesIO(img_response.content)) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                temp_dir = tempfile.mkdtemp()
                temp_path = os.path.join(temp_dir, f"wikimedia_{hash(search_term)}.png")
                img.save(temp_path, format="PNG")
                
                print(f"Image saved to: {temp_path}")
                return temp_path
                
        except Exception as e:
            print(f"Error fetching Wikimedia image: {e}")
            return None
    
    def create_image_mobject(self, image_path: str, scale_factor: float = 0.5, fixed_height: float = 1.5) -> ImageMobject:
        """
        Create an ImageMobject with consistent sizing.

        Args:
            image_path (str): Path to the image file
            scale_factor (float): Additional scaling factor
            fixed_height (float): Fixed height for the image

        Returns:
            ImageMobject: Processed image with consistent sizing
        """
        try:
            if not os.path.exists(image_path):
                print(f"Image path does not exist: {image_path}")
                return OpenGLImageMobject()  # Return an empty ImageMobject as a placeholder

            # Open the image and process it
            with Image.open(image_path) as img:
                # Convert to RGB to ensure color integrity
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize image while maintaining aspect ratio
                original_width, original_height = img.size
                aspect_ratio = original_width / original_height
                new_width = int(fixed_height * aspect_ratio * 100)  # Scale up for better quality
                new_height = int(fixed_height * 100)
                resized_img = img.resize((new_width, new_height), Image.LANCZOS)

                # Save resized image to a temporary file
                temp_dir = tempfile.mkdtemp()
                temp_path = os.path.join(temp_dir, f"resized_{hash(image_path)}.png")
                resized_img.save(temp_path, format="PNG")

            # Create Manim ImageMobject
            img_mobject = OpenGLImageMobject(temp_path)
            img_mobject.height = fixed_height  # Set consistent height
            img_mobject.scale(scale_factor)

            return img_mobject  # Return the ImageMobject

        except Exception as e:
            print(f"Error creating image mobject: {e}")
            return OpenGLImageMobject()  # Return an empty ImageMobject as a fallback
    
    def create_placeholder(self, text: str) -> VGroup:
        """Create a placeholder rectangle with text."""
        rect = Rectangle(width=1.5, height=1, color=BLUE_E, fill_opacity=0.6)
        label = Text(text, font_size=14, color=WHITE).move_to(rect.get_center())
        return VGroup(rect, label)
    
    def format_event_text(self, text: str, font_size: float = 20) -> Text:
        """Format event text with appropriate line breaks."""
        words = text.split()
        lines = [" ".join(words[i:i+3]) for i in range(0, len(words), 3)]
        return Text("\n".join(lines), font_size=font_size, line_spacing=0.8)
    
    def construct(self):
        # Set up the text-to-speech service
        try:
            self.set_speech_service(GTTSService())
        except Exception as e:
            print(f"Error with GTTSService: {e}")
            print("Please check your internet connection or try using a different speech service.")
            return

        # Load data from JSON file
        try:
            with open('eventswithwikiimages.json', 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return

        # Process events data
        events = [
            (event['year'], event['text'], event['narration'], event.get('image_description', '')) 
            for event in data['events']
        ]
        
        # Setup background
        background_path = os.path.join(os.path.dirname(__file__), "examples/resources/blackboard.jpg")
        if os.path.exists(background_path):
            background = OpenGLImageMobject(background_path)
            background.scale_to_fit_height(config.frame_height * 3)
            background.scale_to_fit_width(config.frame_width * 3)
            background.move_to(ORIGIN)
            self.add(background)
        else:
            print(f"Background image not found at: {background_path}")

        # Calculate dynamic sizing
        num_events = len(events)
        base_font_size = max(72 / (num_events / 4), 16)
        event_font_size = max(base_font_size * 0.25, 12)
        year_font_size = max(base_font_size * 0.33, 14)
        dot_radius = max(0.1 * (10 / num_events), 0.05)
        timeline_width = max(num_events * 1.5, 8)
        
        # Show intro
        intro_title = Text(data['title']['main'], font_size=base_font_size, color=BLUE)
        intro_subtitle = Text(data['title']['subtitle'], font_size=base_font_size * 0.5)
        intro_subtitle.next_to(intro_title, DOWN, buff=0.5)
        intro_group = VGroup(intro_title, intro_subtitle)
        
        with self.voiceover(text=data['title']['narration']) as tracker:
            self.play(
                Write(intro_title),
                Write(intro_subtitle),
                run_time=tracker.duration
            )
        self.wait(0.5)
        self.play(FadeOut(intro_group))

        # Create timeline
        timeline = Line(
            LEFT * (timeline_width/2),
            RIGHT * (timeline_width/2),
            color=WHITE
        )
        
        # Create visual elements
        dots = VGroup(metaclass=ConvertToOpenGL)
        year_labels = VGroup(metaclass=ConvertToOpenGL)
        event_texts = VGroup(metaclass=ConvertToOpenGL)
        images = Group()
        
        # Pre-calculate positions
        positions = [timeline.point_from_proportion(i/(num_events-1)) for i in range(num_events)]
        
        # Process each event
        for i, (year, text, _, image_description) in enumerate(events):
            print(f"\nProcessing event {i}: {year} with image description: {image_description}")
            
            # Create dot
            dot = Dot(radius=dot_radius, color=BLUE).move_to(positions[i])
            dots.add(dot)
            
            # Create year label
            year_label = Text(str(year), font_size=year_font_size).next_to(dot, UP, buff=0.15)
            year_labels.add(year_label)
            
            # Create event text
            event_text = self.format_event_text(text, event_font_size)
            event_text.next_to(dot, DOWN, buff=0.35)
            event_texts.add(event_text)
            
            # Handle image
            image_mob = self.create_placeholder("No Image")
            if image_description:
                image_path = self.get_wikimedia_image(image_description)
                if image_path:
                    print("Image path "+ image_path)
                    image_mob = self.create_image_mobject(image_path)
                    image_mob.next_to(year_label, UP, buff=0.25)
            
            images.add(image_mob)
        
        # Create timeline group
        timeline_group = Group(timeline, dots, year_labels, event_texts, images)
        
        # Scale to fit frame
        width_scale = (config.frame_width - 1) / timeline_group.width
        height_scale = (config.frame_height - 1) / timeline_group.height
        scale_factor = min(width_scale, height_scale) * 0.9
        timeline_group.scale(scale_factor)
        
        # Initial timeline creation
        self.play(Create(timeline))
        
        # Animation parameters
        zoom_in_scale = max(0.7 - (num_events * 0.02), 0.3)
        zoom_out_scale = min(1.5 + (num_events * 0.05), 2.5)
        
        # Animate events with voiceover
        for i, (_, _, narration, _) in enumerate(events):
            animations = [
                FadeIn(dots[i]),
                FadeIn(year_labels[i]),
                FadeIn(event_texts[i]),
                FadeIn(images[i])
            ]
            
            with self.voiceover(text=narration) as tracker:
                self.play(
                    *animations,
                    run_time=tracker.duration * 0.5
                )
                
                self.play(
                    self.camera.frame.animate.scale(zoom_in_scale).move_to(dots[i]),
                    run_time=tracker.duration * 0.5
                )
            
            if i < len(events) - 1:
                self.play(
                    self.camera.frame.animate.scale(zoom_out_scale).move_to(ORIGIN),
                    run_time=1
                )
        
        # Return to full view
        self.play(
            self.camera.frame.animate.scale(zoom_out_scale).move_to(ORIGIN),
            run_time=2
        )
        
        # Clean up timeline
        self.play(FadeOut(timeline_group))
        
        # Show conclusion
        start_year = events[0][0]
        end_year = events[-1][0]
        conclusion_text_formatted = data['conclusion']['format'].format(
            start_year=start_year,
            end_year=end_year
        )
        
        conclusion_title = Text(data['conclusion']['title'], 
                              font_size=base_font_size, 
                              color=YELLOW)
        conclusion_text = Text(
            conclusion_text_formatted,
            font_size=base_font_size * 0.5,
            line_spacing=1.5
        ).next_to(conclusion_title, DOWN, buff=0.5)
        
        conclusion_narration = data['conclusion']['narration'].format(
            start_year=start_year,
            end_year=end_year
        )
        
        with self.voiceover(text=conclusion_narration) as tracker:
            self.play(
                Write(conclusion_title),
                Write(conclusion_text),
                run_time=tracker.duration
            )
        self.wait(0.5)

        # Outro
        outro_logo_path = "/Users/mac/texttoeducationalvideos/yeefm logo.png"
        if os.path.exists(outro_logo_path):
            logo = OpenGLImageMobject(outro_logo_path).scale(0.5)
            outro_text = Text("Download YeeFM and Subscribe", font_size=40)
            logo.next_to(outro_text, UP, buff=0.5)
            outro_group = Group(logo, outro_text).move_to(ORIGIN)

            with self.voiceover(text="Download YeeFM and Subscribe") as tracker:
                self.play(FadeIn(logo), FadeIn(outro_text), run_time=tracker.duration)
            
            self.wait(0.5)
        
        # Clean up
        self.play(*[FadeOut(mob) for mob in self.mobjects])


if __name__ == "__main__":
    config.pixel_height = 1080
    config.pixel_width = 1920
    config.frame_height = 9
    config.frame_width = 16
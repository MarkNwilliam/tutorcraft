import json
from manim import *
from manim import config, ORIGIN, BOLD ,BLUE, PURPLE, RED, GRAY 
from manim_voiceover import VoiceoverScene
from code_video import CodeScene, AutoScaled, SequenceDiagram, TextBox, Connection
from manim_voiceover.services.azure import AzureService
from manim_voiceover.services.gtts import GTTSService
from code_video.widgets import DEFAULT_FONT
from manim.mobject.types.image_mobject import ImageMobject
from manim.opengl import *
import tempfile
import os
import shutil  # For directory removal
import requests
from PIL import Image
import io
from xml.etree import ElementTree
import cairosvg
import re
import json
import concurrent.futures
from wikipedia_image_fetcher import WikipediaImageFetcher
from image_utils import ImageUtils
from json_cleaner import clean_json  
from video_utils import VideoUtils
import requests
from manim_chemistry import *
from get_compound import get_compound_info, download_mol_file
import geopandas as gpd
import matplotlib.pyplot as plt
import os

class DirectVideoGenerator(CodeScene, VoiceoverScene, VideoUtils):
    def __init__(self, json_content):
        super().__init__()
        self.all_content = json_content if isinstance(json_content, dict) else json.loads(json_content)
        self.headers = {
            'User-Agent': 'DocVideoMaker/1.0 (https://example.com; contact@example.com)'
        }
        self.image_fetcher = WikipediaImageFetcher(headers={
        'User-Agent': 'DocVideoMaker/1.0 (https://example.com; contact@example.com)'
    })
        self.image_utils = ImageUtils(self.headers)

        
    def create_diagram_with_voiceover(self, diagram):
        """
        Creates the diagram with voiceover narration for each interaction
        
        Args:
            diagram: The sequence diagram to animate
        """
        from manim.animation.creation import Create
        
        for interaction in diagram.get_interactions():
            voiceover_text = interaction.voiceover_text  # Use voiceover_text for narration
            if voiceover_text:
                with self.voiceover(text=voiceover_text) as tracker:
                    self.play(Create(interaction), run_time=tracker.duration)
            else:
                self.play(Create(interaction))

        
    def create_title_scene(self, title_data):
        if 'background' in title_data:
            self.add_background(title_data['background'])
        else:
            self.add_background("./examples/resources/blackboard.jpg")
        
        with self.voiceover(title_data['voiceover']):
            # Automatically scale the main text to fit within the video width
            title = MarkupText(title_data['main_text'], font_size=48, fill_opacity=1, weight=BOLD)
            title.width = min(title.width, config.frame_width * 0.8)  # Ensure it fits within 80% of the frame width
            title.move_to(ORIGIN)  # Center the title
            self.play(Create(title))
            
            if 'subtitle' in title_data:
                # Automatically scale the subtitle to fit within the video width
                subtitle = MarkupText(title_data['subtitle'], font_size=36)
                subtitle.width = min(subtitle.width, config.frame_width * 0.8)  # Ensure it fits within 80% of the frame width
                subtitle.next_to(title, direction=DOWN, buff=0.5)  # Add a margin below the title
                self.play(FadeIn(subtitle))
            
            self.wait(title_data.get('duration', 3))
        
        self.clear()

    def create_overview_scene(self, overview_data):
        self.add_background("./examples/resources/blackboard.jpg")
    
        with self.voiceover(overview_data['voiceover']):
            if 'subtitle' in overview_data:
                subtitle = Title(overview_data['subtitle'])
                subtitle.scale(0.8)
                subtitle.to_edge(UP)
                self.play(FadeIn(subtitle, run_time=1.5))
                self.wait(overview_data.get('subtitle_duration', 0.5))
            
            # Remove AutoScaled and properly center the text
            text = MarkupText(overview_data['text'], font_size=36)
            
            # Scale text to fit within frame if too wide
            if text.width > config.frame_width * 0.8:
                text.width = config.frame_width * 0.8
            
            # Center the text
            text.move_to(ORIGIN)
            
            self.play(FadeIn(text, run_time=2))
            self.wait(overview_data.get('duration', 0.5))
        
        self.clear()

    def create_code_scene(self, code_data):
        

        try:
            formatted_code = self.format_code(code_data['code'])
            print("Formatted code:")
            print(formatted_code)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(formatted_code)
                temp_path = temp_file.name

            try:
                tex = self.create_code(temp_path)
                
                with self.voiceover(code_data.get('intro_voiceover', f"Let's look at {code_data['title']}")):
                    self.play(Create(tex))
                self.wait(1)

                with self.voiceover(code_data['intro']['text']):
                    self.highlight_none(tex)
                    self.wait(1)

                total_lines = len(formatted_code.splitlines())
                print(f"Total lines after formatting: {total_lines}")

                for section in code_data['sections']:
                    print(f"Processing section: {section['title']}")
                    start_line = min(section['highlight_start'], total_lines)
                    end_line = min(section['highlight_end'], total_lines)
                    
                    with self.voiceover(section['voiceover']):
                        self.highlight_lines(
                            tex, 
                            start_line,
                            end_line,
                            section['title']
                        )
                        self.wait(section.get('duration', 2))

                with self.voiceover(code_data['conclusion']['text']):
                    self.highlight_none(tex)
                    self.wait(2)

            finally:
                os.unlink(temp_path)
            
            self.clear()
            
        except Exception as e:
            print(f"Error in create_code_scene: {type(e).__name__}: {e}")
            print(f"Current code structure:")
            print(formatted_code)
            raise

    def create_sequence_diagram(self, sequence_data):
        print("here is the sequence data", sequence_data)   
        background_path = sequence_data.get('background')
        if background_path:
            self.add_background(background_path)
        else:
            self.add_background("./examples/resources/blackboard.jpg")
        
        if 'title' in sequence_data:
            title = Text(sequence_data['title'], font=DEFAULT_FONT)
            title.scale(0.8)
            title.to_edge(UP)
            self.add(title)

        diagram = AutoScaled(SequenceDiagram())
        actors = {}
        actor_names = sequence_data["actors"]
        actor_objects = diagram.add_objects(*actor_names)
        
        for name, obj in zip(actor_names, actor_objects):
            actors[name] = obj

        for interaction in sequence_data["interactions"]:
            source = actors[interaction["from"]]
            
            if interaction["type"] == "note":
                source.note(
                    message=interaction["message"],
                    voiceover=interaction["voiceover"]
                )
            else:
                target = actors[interaction["to"]]
                source.to(
                    target,
                    message=interaction["message"],
                    voiceover=interaction["voiceover"]
                )

        title = Text(sequence_data["title"], font=DEFAULT_FONT)
        title.scale(0.8)
        title.to_edge(UP)

        self.add(title)
        diagram.next_to(title, DOWN)
        self.play(Create(diagram))

        self.create_diagram_with_voiceover(diagram)
        self.wait(0.4)
        self.clear()

    def add_background(self, path):
        """This will now use the inherited method from VideoUtils"""
        super().add_background(path)

    def get_wikipedia_images(self, article_title, num_images=2, save_dir="./downloaded_images"):
        return self.image_fetcher.get_wikipedia_images(article_title, num_images, save_dir)

    def create_image_text_scene(self, scene_data):
        """Simplified scene with title, text, and images - OpenGL compatible"""
        print("=== STARTING IMAGE TEXT SCENE ===")
        
        # Add background if it exists
        try:
            self.add_background("./examples/resources/blackboard.jpg")
            print("Background added successfully")
        except:
            print("Background failed to load, continuing without it")

        with self.voiceover(scene_data['voiceover']):
            
            # 1. CREATE AND SHOW TITLE
            print("Creating title...")
            title = Title(scene_data['title'], font_size=48, color=WHITE)
            title.to_edge(UP, buff=0.5)
            self.play(Write(title), run_time=1)
            print(f"Title created and displayed: '{scene_data['title']}'")

            # 2. CREATE AND SHOW TEXT
            print("Creating text...")
            text_content = scene_data['text']
            text = Text(text_content, color=WHITE, line_spacing=1.2, font_size=48, disable_ligatures=True,
    should_center=True )
            
            # Scale text if too wide
            max_width = 13.5
            if text.get_width() > max_width:
                text.scale(max_width / text.get_width())
                print(f"Text scaled to fit width: {text.get_width()}")
            
            # Position text below title
            text.next_to(title, DOWN, buff=0.5)
            self.play(FadeIn(text), run_time=1)
            print("Text displayed successfully")

            # 3. GET IMAGE PATHS
            print("Getting image paths...")
            num_images = scene_data.get('num_images', 1)
            wikipedia_topic = scene_data.get('wikipedia_topic', 'placeholder')
            
            try:
                image_paths = self.get_wikipedia_images(wikipedia_topic, num_images)
                print(f"Retrieved {len(image_paths) if image_paths else 0} image paths")
                if image_paths:
                    for i, path in enumerate(image_paths):
                        print(f"  Image {i+1}: {path}")
            except Exception as e:
                print(f"Error getting images: {e}")
                image_paths = []

            # 4. CREATE IMAGE OBJECTS
            print("Creating image objects...")
            images = []
            
            if not image_paths:
                print("No images found, creating placeholder")
                # Create a simple placeholder
                placeholder = Rectangle(
                    width=4, 
                    height=3, 
                    color=BLUE, 
                    fill_opacity=0.3,
                    stroke_color=WHITE,
                    stroke_width=2
                )
                placeholder_text = Text(
                    "No Image Available", 
                    font_size=20, 
                    color=WHITE
                ).move_to(placeholder.get_center())
                
                placeholder_group = VGroup(placeholder, placeholder_text)
                images.append(placeholder_group)
                print("Placeholder created")
            
            else:
                # Try to load actual images
                for i, path in enumerate(image_paths):
                    print(f"Loading image {i+1}: {path}")
                    
                    try:
                        # Check if file exists
                        import os
                        if not os.path.exists(path):
                            raise FileNotFoundError(f"File not found: {path}")
                        
                        # Check file size
                        file_size = os.path.getsize(path)
                        if file_size < 500:  # Less than 500 bytes is suspicious
                            raise ValueError(f"File too small ({file_size} bytes): {path}")
                        
                        print(f"  File exists, size: {file_size} bytes")
                        
                        # Create image
                        img = OpenGLImageMobject(path)
                        
                        print(f"  OpenGLImageMobject created successfully")
                        
                        # Scale to reasonable size
                        target_width = 4
                        if img.get_width() > 0:
                            scale_factor = target_width / img.get_width()
                            img.scale(scale_factor)
                            print(f"  Image scaled by {scale_factor:.2f}")
                        
                        images.append(img)
                        print(f"  Image {i+1} loaded successfully")
                        
                    except Exception as e:
                        print(f"  Failed to load image {i+1}: {str(e)}")
                        
                        # Create error placeholder
                        error_rect = Rectangle(
                            width=4, 
                            height=3, 
                            color=RED, 
                            fill_opacity=0.2,
                            stroke_color=WHITE,
                            stroke_width=2
                        )
                        error_text = Text(
                            f"Image {i+1}\nLoad Error", 
                            font_size=16, 
                            color=WHITE
                        ).move_to(error_rect.get_center())
                        
                        error_group = VGroup(error_rect, error_text)
                        images.append(error_group)
                        print(f"  Error placeholder created for image {i+1}")

            # 5. POSITION AND DISPLAY IMAGES
            print(f"Displaying {len(images)} images...")
            
            if images:
                # Calculate position below text
                text_bottom = text.get_bottom()[1]
                image_y = text_bottom - 1.0  # 1 unit below text
                
                if len(images) == 1:
                    # Single image - center it
                    img = images[0]
                    img.move_to([0, image_y - img.get_height()/2, 1])
                    print(f"Single image positioned at center, y={image_y}")
                    
                else:
                    # Multiple images - arrange horizontally
                    total_width = sum(img.get_width() for img in images)
                    spacing = 0.5
                    total_space_needed = total_width + spacing * (len(images) - 1)
                    
                    # Scale down if needed
                    max_total_width = 12
                    if total_space_needed > max_total_width:
                        scale_factor = max_total_width / total_space_needed
                        for img in images:
                            img.scale(scale_factor)
                        total_width *= scale_factor
                        print(f"Images scaled down by {scale_factor:.2f} to fit")
                    
                    # Position images
                    start_x = -total_width/2 - spacing*(len(images)-1)/2
                    current_x = start_x
                    
                    for i, img in enumerate(images):
                        x_pos = current_x + img.get_width()/2
                        y_pos = image_y - img.get_height()/2
                        img.move_to([x_pos, y_pos, 0])
                        current_x += img.get_width() + spacing
                        print(f"Image {i+1} positioned at ({x_pos:.1f}, {y_pos:.1f})")

                # Display all images
                print("Adding images to scene...")
                for i, img in enumerate(images):
                    try:
                        # Simple approach - just add the image
                        self.add(img)
                        print(f"Image {i+1} added to scene")
                        
                        # Small delay between images
                        if len(images) > 1:
                            self.wait(0.2)
                            
                    except Exception as e:
                        print(f"Failed to add image {i+1} to scene: {e}")
                        
                        # Last resort - try a simple rectangle
                        try:
                            fallback = Rectangle(
                                width=2, 
                                height=1.5, 
                                color=GRAY, 
                                fill_opacity=0.5
                            ).move_to(img.get_center() if hasattr(img, 'get_center') else [0, -2, 0])
                            
                            self.add(fallback)
                            print(f"Added fallback rectangle for image {i+1}")
                        except Exception as e2:
                            print(f"Even fallback failed for image {i+1}: {e2}")

                print("All images processed")
            
            else:
                print("No images to display")
                no_img_text = Text("No images available", font_size=20, color=GRAY)
                no_img_text.move_to([0, -2, 0])
                self.add(no_img_text)

            # 6. WAIT AND CLEANUP
            duration = scene_data.get('duration', 5)
            print(f"Waiting {duration} seconds...")
            self.wait(duration)
            
            print("Clearing scene...")
            self.clear()
            print("=== IMAGE TEXT SCENE COMPLETE ===")


    def create_multi_image_text_scene(self, image_text_data):
        """Scene with multiple images and text"""
        print(f"Creating scene: {image_text_data.get('title', 'Untitled')}")
        print(f"Image paths: {image_text_data.get('image_paths', [])}")
        self.add_background("./examples/resources/blackboard.jpg")
        
        with self.voiceover(image_text_data['voiceover']):
            if 'title' in image_text_data:
                title = Title(image_text_data['title'])
                title.to_edge(UP)
                self.play(FadeIn(title, run_time=1))
            
            images = []
            if 'wikipedia_topics' in image_text_data:
                num_images = image_text_data.get('num_images', 2)
                keywords = image_text_data['wikipedia_topics']
                print(f"Searching for images using keywords: {keywords}")
                
                image_paths = []
                for keyword in keywords:
                    print(f"Trying keyword: {keyword}")
                    image_paths = self.get_wikipedia_images(keyword, num_images)
                    if image_paths:
                        print(f"Images found for keyword: {keyword}")
                        break
                    else:
                        print(f"No images found for keyword: {keyword}")
                
                if not image_paths:
                    print(f"No images found for any of the keywords: {keywords}")
                    for i in range(num_images):
                        print(f"Creating placeholder for image {i+1}")
                        placeholder = Rectangle(width=4, height=3, color=RED)
                        placeholder_text = Text(f"No image {i+1} found", font_size=20).move_to(placeholder.get_center())
                        placeholder_group = Group(placeholder, placeholder_text)
                        # Move placeholder to Z=2 using move_to
                        current_pos = placeholder_group.get_center()
                        placeholder_group.move_to([current_pos[0], current_pos[1], 2])
                        images.append(placeholder_group)
                else:
                    for path in image_paths:
                        print(f"\n--- Attempting to load image: {path} ---")
                        print(f"Image path exists: {os.path.exists(path)}")
                        if os.path.exists(path):
                            print(f"Image path permissions: {oct(os.stat(path).st_mode)[-3:]}")
                            print(f"Image file size: {os.path.getsize(path)} bytes")
                        
                        try:
                            print("Loading image with OpenGLImageMobject...")
                            img = OpenGLImageMobject(path)
                            print(f"Image loaded successfully - dimensions: {img.width} x {img.height}")
                            
                            if 'image_width' in image_text_data:
                                print(f"Setting custom width: {image_text_data['image_width']}")
                                img.width = image_text_data['image_width']
                            else:
                                print("Setting default width: 3")
                                img.width = 3
                            
                            # MOVE IMAGE TO Z=2 USING move_to (OpenGL compatible)
                            current_pos = img.get_center()
                            img.move_to([current_pos[0], current_pos[1], 2])
                            print("Image moved to Z=2 using move_to (above all other elements)")
                            
                            print("Adding image to collection")
                            images.append(img)
                            
                        except Exception as e:
                            print(f"Error loading image: {str(e)}")
                            print(f"Error type: {type(e).__name__}")
                            print("Creating placeholder for failed image")
                            placeholder = Rectangle(width=3, height=2.25, color=RED)
                            placeholder_text = Text("Image load failed", font_size=18)
                            placeholder_text.move_to(placeholder.get_center())
                            error_group = Group(placeholder, placeholder_text)
                            # Move error placeholder to Z=2 using move_to
                            current_pos = error_group.get_center()
                            error_group.move_to([current_pos[0], current_pos[1], 2])
                            images.append(error_group)
            
            elif 'image_paths' in image_text_data:
                for path in image_text_data['image_paths']:
                    try:
                        img = OpenGLImageMobject(path)
                        if 'image_width' in image_text_data:
                            img.width = image_text_data['image_width']
                        else:
                            img.width = 3
                        # Move image to Z=2 using move_to
                        current_pos = img.get_center()
                        img.move_to([current_pos[0], current_pos[1], 2])
                        images.append(img)
                    except Exception as e:
                        print(f"Error loading image: {e}")
                        placeholder = Rectangle(width=3, height=2.25, color=RED)
                        placeholder_text = Text("Image load failed", font_size=18).move_to(placeholder.get_center())
                        error_group = Group(placeholder, placeholder_text)
                        # Move error placeholder to Z=2 using move_to
                        current_pos = error_group.get_center()
                        error_group.move_to([current_pos[0], current_pos[1], 2])
                        images.append(error_group)
            
            text = MarkupText(image_text_data['text'], font_size=35, line_spacing=1.2, disable_ligatures=True,  color= WHITE)

                        # Scale text if too wide
            max_width = 12
            if text.get_width() > max_width:
                text.scale(max_width / text.get_width())
                print(f"Text scaled to fit width: {text.get_width()}")
            


            
            # POSITION TEXT FIRST
            if 'title' in image_text_data:
                text.next_to(title, DOWN, buff=0.5)
            else:
                text.to_edge(UP, buff=1)
            
            # MOVE TEXT TO Z=1 
            current_text_pos = text.get_center()
            text.move_to([current_text_pos[0], current_text_pos[1], 1])
            
            # CALCULATE POSITION FOR IMAGES (LIKE IN THE WORKING FUNCTION)
            text_bottom = text.get_bottom()[1]
            image_y = text_bottom - 1.0  # 1 unit below text
            
            # POSITION IMAGES INDIVIDUALLY (NO Group.arrange!)
            if images:
                total_width = sum(img.get_width() for img in images)
                spacing = 0.5
                total_space_needed = total_width + spacing * (len(images) - 1)
                
                # Scale down if needed
                max_total_width = 12
                if total_space_needed > max_total_width:
                    scale_factor = max_total_width / total_space_needed
                    for img in images:
                        img.scale(scale_factor)
                    total_width *= scale_factor
                    print(f"Images scaled down by {scale_factor:.2f} to fit")
                
                # Position images horizontally (like the working function)
                start_x = -total_width/2 - spacing*(len(images)-1)/2
                current_x = start_x
                
                for i, img in enumerate(images):
                    x_pos = current_x + img.get_width()/2
                    y_pos = image_y - img.get_height()/2
                    # KEEP THE Z=2 POSITIONING!
                    img.move_to([x_pos, y_pos, 2])  # This maintains Z=2
                    current_x += img.get_width() + spacing
                    print(f"Image {i+1} positioned at ({x_pos:.1f}, {y_pos:.1f}, 2)")
            
            # ADD TO SCENE
            self.play(FadeIn(text), run_time=1)
            for img in images:
                self.play(FadeIn(img), run_time=0.5)
            
            self.wait(image_text_data.get('duration', 5))

            self.clear()


    def create_triangle_scene(self, triangle_data):
        """Scene with three connected components in a triangle layout"""
        self.add_background("./examples/resources/blackboard.jpg")
        
        with self.voiceover(triangle_data['voiceover']):
            if 'title' in triangle_data:
                title = Title(triangle_data['title'])
                title.to_edge(UP)
                self.play(FadeIn(title, run_time=1))
            
            top = TextBox(triangle_data['top_text'], shadow=False)
            left = TextBox(triangle_data['left_text'], shadow=False)
            right = TextBox(triangle_data['right_text'], shadow=False)
            
            if 'title' in triangle_data:
                top.next_to(title, DOWN, buff=1)
            else:
                top.move_to(UP* 0.5)
            
            left.next_to(top, DOWN + LEFT, buff=2)
            right.next_to(top, DOWN + RIGHT, buff=2)
            
            connections = []
            if 'top_to_left' in triangle_data:
                conn1 = Connection(top, left, triangle_data['top_to_left'])
                connections.append(conn1)
            if 'top_to_right' in triangle_data:
                conn2 = Connection(top, right, triangle_data['top_to_right'], padding=-0.7)
                connections.append(conn2)
            if 'left_to_right' in triangle_data:
                conn3 = Connection(left, right, triangle_data['left_to_right'])
                connections.append(conn3)
            if 'right_to_left' in triangle_data:
                conn4 = Connection(right, left, triangle_data['right_to_left'])
                connections.append(conn4)
            if 'left_to_top' in triangle_data:
                conn5 = Connection(left, top, triangle_data['left_to_top'])
                connections.append(conn5)
            if 'right_to_top' in triangle_data:
                conn6 = Connection(right, top, triangle_data['right_to_top'], padding=-0.6)
                connections.append(conn6)
            
            elements = VGroup(top, left, right, *connections)
            #AutoScaled(elements)
            elements.shift(RIGHT * 0.3)
            
            # Get the scaled components
            scaled_top = elements[0]
            scaled_left = elements[1]
            scaled_right = elements[2]
            scaled_connections = elements[3:] if connections else []
            
            self.play(FadeIn(scaled_top))
            
            if connections:
                for i, conn in enumerate(scaled_connections):  # Use scaled_connections here
                    self.play(Create(conn))
                    if i == 0 and 'top_to_left' in triangle_data:
                        self.play(FadeIn(scaled_left))  # Use scaled_left here
                    elif i == 1 and 'top_to_right' in triangle_data:
                        self.play(FadeIn(scaled_right))  # Use scaled_right here
                
                if i == len(scaled_connections) - 1:  # Use scaled_connections length
                    remaining = []
                    if 'top_to_left' not in triangle_data and scaled_left not in self.mobjects:  # Use scaled_left
                        remaining.append(scaled_left)
                    if 'top_to_right' not in triangle_data and scaled_right not in self.mobjects:  # Use scaled_right
                        remaining.append(scaled_right)
                    if remaining:
                        self.play(*[FadeIn(mob) for mob in remaining])
            else:
                self.play(FadeIn(scaled_left), FadeIn(scaled_right))  # Use scaled elements
            
            self.wait(triangle_data.get('duration', 5))
            self.clear()
    
    def create_data_processing_flow(self, flow_data):
        """Data processing flow animation"""
        color_map = {
            "green": GREEN,
            "red": RED,
            "blue": BLUE,
            "purple": PURPLE
        }

        self.add_background("./examples/resources/blackboard.jpg")

        blocks = []
        for block_config in flow_data['blocks']:
            block = Rectangle(width=2, height=1, color=color_map[block_config['color']], fill_opacity=0.3)
            
            block_text = Text(block_config['text'], font_size=20, color=WHITE)
            margin = 0.2
            while block_text.width > block.width - margin or block_text.height > block.height - margin:
                block_text.scale(0.9)
            
            text_background = Rectangle(
                width=block_text.width + 0.2,
                height=block_text.height + 0.2,
                color=BLACK,
                fill_opacity=0.5,
                stroke_opacity=0
            )
            text_background.move_to(block_text.get_center())
            
            text_group = VGroup(text_background, block_text)
            text_group.move_to(block.get_center())
            
            block_group = VGroup(block, text_group)
            blocks.append((block_group, block_config))

        blocks[0][0].shift(LEFT*3 + UP*1.5)
        blocks[1][0].shift(LEFT*3 + DOWN*1.5)
        blocks[2][0].shift(ORIGIN)
        blocks[3][0].shift(RIGHT*3)

        arrows = [
            Line(blocks[0][0].get_right(), blocks[2][0].get_left(), color=GREEN, tip_length=0.1).add_tip(),
            Line(blocks[1][0].get_right(), blocks[2][0].get_left(), color=RED, tip_length=0.1).add_tip(),
            Line(blocks[2][0].get_right(), blocks[3][0].get_left(), color=PURPLE, tip_length=0.1).add_tip()
        ]

        for block, block_config in blocks:
            with self.voiceover(text=block_config['voiceover']):
                if block_config['type'] in ['input1', 'input2']:
                    self.play(FadeIn(block))
                elif block_config['type'] == 'processor':
                    self.play(
                        Create(arrows[0]),
                        Create(arrows[1]),
                        FadeIn(block)
                    )
                elif block_config['type'] == 'output':
                    self.play(
                        Create(arrows[2]),
                        FadeIn(block)
                    )

        with self.voiceover(text=flow_data['narration']['conclusion']):
            self.wait(1)

        self.play(
            *[FadeOut(block) for block, _ in blocks],
            *[FadeOut(arrow) for arrow in arrows]
        )


    def create_data_processing_flow(self, flow_data):
        """Data processing flow animation"""
        color_map = {
            "green": GREEN,
            "red": RED,
            "blue": BLUE,
            "purple": PURPLE
        }

        self.add_background("./examples/resources/blackboard.jpg")

        blocks = []
        for block_config in flow_data['blocks']:
            block = Rectangle(width=2, height=1, color=color_map[block_config['color']], fill_opacity=0.3)
            
            block_text = Text(block_config['text'], font_size=20, color=WHITE)
            margin = 0.2
            while block_text.width > block.width - margin or block_text.height > block.height - margin:
                block_text.scale(0.9)
            
            text_background = Rectangle(
                width=block_text.width + 0.2,
                height=block_text.height + 0.2,
                color=BLACK,
                fill_opacity=0.5,
                stroke_opacity=0
            )
            text_background.move_to(block_text.get_center())
            
            text_group = VGroup(text_background, block_text)
            text_group.move_to(block.get_center())
            
            block_group = VGroup(block, text_group)
            blocks.append((block_group, block_config))

        blocks[0][0].shift(LEFT*3 + UP*1.5)
        blocks[1][0].shift(LEFT*3 + DOWN*1.5)
        blocks[2][0].shift(ORIGIN)
        blocks[3][0].shift(RIGHT*3)

        arrows = [
            Line(blocks[0][0].get_right(), blocks[2][0].get_left(), color=GREEN, tip_length=0.1).add_tip(),
            Line(blocks[1][0].get_right(), blocks[2][0].get_left(), color=RED, tip_length=0.1).add_tip(),
            Line(blocks[2][0].get_right(), blocks[3][0].get_left(), color=PURPLE, tip_length=0.1).add_tip()
        ]

        for block, block_config in blocks:
            with self.voiceover(text=block_config['voiceover']):
                if block_config['type'] in ['input1', 'input2']:
                    self.play(FadeIn(block))
                elif block_config['type'] == 'processor':
                    self.play(
                        Create(arrows[0]),
                        Create(arrows[1]),
                        FadeIn(block)
                    )
                elif block_config['type'] == 'output':
                    self.play(
                        Create(arrows[2]),
                        FadeIn(block)
                    )

        with self.voiceover(text=flow_data['narration']['conclusion']):
            self.wait(1)

        self.play(
            *[FadeOut(block) for block, _ in blocks],
            *[FadeOut(arrow) for arrow in arrows]
        )

    def create_timeline_scene(self, timeline_data):
        """
        Creates a timeline animation scene with proper layout, image handling, AND camera movement.
        Enhanced version combining the working layout fixes with camera scaling/movement from original.
        """
        # --- FIXED Background Setup ---
        bg_path = timeline_data.get("background_image", "./examples/resources/blackboard.jpg")
        try:
            # Create background properly sized
            background = OpenGLImageMobject(bg_path)
            # Scale to fit frame exactly
            background.scale_to_fit_width(config.frame_width * 4)
            background.scale_to_fit_height(config.frame_height * 4)

            background.move_to(ORIGIN)
            # Ensure background is at Z=0 (behind everything)
            background.move_to([0, 0, 0])
            self.add(background)
            print("Background added with proper scaling")
        except Exception as e:
            print(f"Failed to load background: {e}")
            # Add a solid color background as fallback
            bg_rect = Rectangle(
                width=config.frame_width,
                height=config.frame_height,
                color=BLACK,
                fill_opacity=1
            ).move_to(ORIGIN)
            self.add(bg_rect)

        # --- Timeline setup with better spacing ---
        events = [
            (event['year'], event['text'], event['narration'], event.get('image_description', ''))
            for event in timeline_data['events']
        ]
        num_events = len(events)
        
        # Create timeline line - keep it reasonable size
        timeline_width = min(12, config.frame_width * 0.8)  # Max 12 units or 80% of frame
        timeline = Line(LEFT * 15, RIGHT * 15, color=WHITE, stroke_width=20)
        
        # Calculate positions along timeline
        positions = [timeline.point_from_proportion(i / (num_events - 1)) for i in range(num_events)]

        # --- Title with proper positioning ---
        title_y = config.frame_height/2 - 1  # 1 unit from top
        if "title" in timeline_data:
            title = Title(timeline_data["title"], font_size=48)
            title.move_to([0, title_y, 1])  # Z=1 to be above background
            self.play(FadeIn(title))
            timeline_y = title_y - 4.5  # Position timeline 2 units below title
        else:
            timeline_y = 1  # Default position if no title

        # Position timeline
        timeline.move_to([0, timeline_y, 1])

        # --- Create timeline elements with FIXED positioning ---
        dots, year_labels, event_texts, images = [], [], [], []
        
        for i, (year, text, _, image_desc) in enumerate(events):
            # Timeline dot
            dot = Dot(color=BLUE, radius=0.1).move_to([positions[i][0], timeline_y, 1])
            dots.append(dot)
            
            # Year label - position above dot
            year_label = Text(str(year), font_size=24, color=WHITE)
            year_label.next_to(dot, UP, buff=0.3)
            year_label.move_to([year_label.get_center()[0], year_label.get_center()[1], 1])
            year_labels.append(year_label)
            
            # Event text - position below dot with proper wrapping
            words = text.split()
            # Wrap text to 4 words per line for better readability
            lines = [" ".join(words[j:j + 4]) for j in range(0, len(words), 4)]
            event_text = Text("\n".join(lines), font_size=18, line_spacing=0.8, color=WHITE)
            event_text.next_to(dot, DOWN, buff=0.5)
            event_text.move_to([event_text.get_center()[0], event_text.get_center()[1], 1])
            event_texts.append(event_text)
            
            # --- FIXED Image Loading and Positioning ---
            image_group = None
            
            if image_desc:
                print(f"Loading image for event {i+1} ({year}): '{image_desc}'")
                try:
                    # Use the working image loading method
                    image_paths = self.get_wikipedia_images(image_desc, num_images=1)
                    
                    if image_paths and len(image_paths) > 0:
                        image_path = image_paths[0]
                        print(f"Got image path: {image_path}")
                        
                        if os.path.exists(image_path):
                            print(f"Loading image file: {image_path}")
                            
                            # Create and properly size the image
                            img = OpenGLImageMobject(image_path)
                            
                            # Scale to consistent height
                            target_height = 2.0
                            if img.get_height() > 0:
                                scale_factor = target_height / img.get_height()
                                img.scale(scale_factor)
                                print(f"Image scaled to height {target_height} (factor: {scale_factor:.2f})")
                            
                            # Position image above year label
                            image_y = year_label.get_top()[1] + 0.5
                            img.move_to([positions[i][0], image_y + img.get_height()/2, 2])
                            
                            # Background border for image
                            bg_rect = Rectangle(
                                width=img.get_width(),
                                height=img.get_height(),
                                color=WHITE,
                                fill_opacity=0,   # transparent, just border
                                stroke_color=WHITE,
                                stroke_width=2
                            )
                            bg_rect.move_to([img.get_center()[0], img.get_center()[1], 1.5])
                            
                            # Group image and border
                            image_group = Group(bg_rect, img)
                            print(f"Image positioned at ({positions[i][0]:.1f}, {image_y + img.get_height()/2:.1f})")
                        else:
                            print(f"Image file does not exist: {image_path}")
                    
                    if image_group is None:
                        # Fallback: Placeholder card
                        placeholder = Rectangle(
                            width=2, height=1.5, 
                            color=WHITE, fill_opacity=0.1,
                            stroke_color=RED, stroke_width=2
                        )
                        placeholder_text = Text("Image\nNot Found", font_size=14, color=WHITE)
                        placeholder_text.move_to(placeholder.get_center())
                        
                        image_y = year_label.get_top()[1] + 0.5
                        image_group = Group(placeholder, placeholder_text)
                        image_group.move_to([positions[i][0], image_y + 0.75, 2])
                        print(f"Created placeholder for event {i+1}")
                        
                except Exception as e:
                    print(f"Error loading image for event {i+1}: {e}")
                    # Emergency fallback
                    placeholder = Rectangle(
                        width=2, height=1.5, 
                        color=WHITE, fill_opacity=0.1,
                        stroke_color=RED, stroke_width=2
                    )
                    placeholder_text = Text("Image\nError", font_size=14, color=WHITE)
                    placeholder_text.move_to(placeholder.get_center())
                    
                    image_y = year_label.get_top()[1] + 0.5
                    image_group = Group(placeholder, placeholder_text)
                    image_group.move_to([positions[i][0], image_y + 0.75, 2])
                    print(f"Created error placeholder for event {i+1}")
            
            images.append(image_group)

        # --- Animate timeline creation ---
        print("Starting timeline animation...")
        self.play(Create(timeline), run_time=1)
        self.wait(0.5)

        # --- RESTORED: Initial camera setup from original code ---
        self.camera.set_euler_angles(phi=0 * DEGREES, theta=0 * DEGREES)
        self.camera.scale(1.2)  # simulate zoom
        print("Camera initialized with proper settings")

        # --- Animate through events one by one WITH CAMERA MOVEMENT ---
        for i in range(num_events):
            print(f"Animating event {i+1}: {events[i][0]} with camera movement")
            
            with self.voiceover(text=events[i][2]) as tracker:
                # Prepare animations - include camera movement to focus on current event
                animations = [
                    FadeIn(dots[i]),
                    FadeIn(year_labels[i]),
                    FadeIn(event_texts[i]),
                    # RESTORED: Camera movement from original code
                    self.camera.animate.move_to(dots[i]).scale(0.5)  # zoom in on current event
                ]
                
                # Add image animation if image exists
                if images[i] is not None:
                    animations.append(FadeIn(images[i]))
                    print(f"Adding image animation for event {i+1}")
                else:
                    # Add empty animation group to maintain consistency with original
                    animations.append(AnimationGroup())
                    print(f"No image to animate for event {i+1}")
                
                # Play animations with camera zoom in (40% of duration)
                self.play(*animations, run_time=tracker.duration * 0.4)
                
                # Hold focused view (20% of duration)
                self.wait(tracker.duration * 0.2)
                
                # RESTORED: Camera zoom back out to show full timeline
                self.play(
                    self.camera.animate.move_to(ORIGIN).scale(2),  # return to full timeline view
                    run_time=tracker.duration * 0.4
                )

        # Final pause to show complete timeline
        self.wait(2)
        
        # Clear scene
        print("Clearing timeline scene...")
        self.clear()
        print("Timeline scene complete")


    def create_bullet_points_scene(self, bullet_data):
        """Scene with title, subtitle, and bullet points"""
        self.add_background("./examples/resources/blackboard.jpg")
        
        with self.voiceover(bullet_data['voiceover']):
            # Title
            title = Text(bullet_data['title'], font_size=60, weight=BOLD).to_edge(UP)
            underline = Line(
                start=title.get_left(),
                end=title.get_right(),
                stroke_width=3
            ).next_to(title, DOWN, buff=0.2)

            # Subtitle
            subtitle = Text(bullet_data['subtitle'], font_size=36, weight=BOLD).next_to(underline, DOWN, buff=0.6)

            # Bullet points
            bullets = VGroup(
                *[Text(f"- {point}", font_size=28).scale(0.9) for point in bullet_data['points']]
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(subtitle, DOWN, buff=0.5).to_edge(LEFT)

            # Add animations
            self.play(Write(title))
            self.play(Create(underline))
            self.play(FadeIn(subtitle, shift=DOWN))
            for bullet in bullets:
                self.play(FadeIn(bullet, shift=RIGHT))
                self.wait(0.5)

            self.wait(bullet_data.get('duration', 2))
        
        self.clear()

    def goodbye(self):
        text = Text(
            "Thank you for watching! You can generate other tutorial videos with our platform.",
            font_size=40
        )
        text.width = min(text.width, config.frame_width * 0.8)  # Ensure it fits within 80% of the frame width
        text.move_to(ORIGIN)

        with self.voiceover(text="Thank you for watching! You can generate other tutorial videos with our platform.") as tracker:
            self.play(FadeIn(text), run_time=tracker.duration)
        
        self.wait(0.5)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

    def create_plan_scene(self, plan_data):
        """Scene with title and schedule table"""
        self.add_background("./examples/resources/blackboard.jpg")
        
        with self.voiceover(plan_data['voiceover']):
            # Title
            title = Text(plan_data["title"], font_size=60, weight=BOLD).to_edge(UP)
            underline = Line(
                start=title.get_left(),
                end=title.get_right(),
                stroke_width=3
            ).next_to(title, DOWN, buff=0.2)

            self.play(Write(title))
            self.play(Create(underline))

            # Create schedule rows
            rows = VGroup()
            for entry in plan_data["schedule"]:
                day_text = Text(entry["day"], font_size=34, weight=BOLD)
                activity_text = Text(entry["activity"], font_size=28).next_to(day_text, RIGHT, buff=1.5).align_to(day_text, UP)
                
                row = VGroup(day_text, activity_text)
                rows.add(row)

            # Arrange rows vertically
            rows.arrange(DOWN, buff=1.2).next_to(underline, DOWN, buff=1.0).to_edge(LEFT)

            # Add lines between rows
            separators = VGroup()
            for i in range(len(rows)):
                row = rows[i]
                line = Line(
                    start=LEFT*6,
                    end=RIGHT*6,
                    stroke_width=2
                ).next_to(row, UP, buff=0.6)
                separators.add(line)

            # Animate rows
            for i, row in enumerate(rows):
                self.play(FadeIn(separators[i]))
                self.play(FadeIn(row, shift=RIGHT))
                self.wait(0.8)

            self.wait(plan_data.get('duration', 2))
        
        self.clear()

    def create_multi_section_bullets_scene(self, section_data):
        """Scene with title and multiple sections with subtitles and bullet points"""
        self.add_background("./examples/resources/blackboard.jpg")
        
        with self.voiceover(section_data['voiceover']):
            # Title (large and bold)
            title = Text(section_data["title"], font_size=48, weight=BOLD, color=WHITE)
            title.to_edge(UP, buff=1.0)
            self.play(Write(title))

            # Separator line under title
            line = Line(
                start=LEFT * 6, end=RIGHT * 6, color=WHITE, stroke_width=3
            ).next_to(title, DOWN, buff=0.4)
            self.play(Create(line))

            # Create sections with proper alignment
            all_content = VGroup()
            
            for section in section_data["sections"]:
                # Subtitle (medium size, bold, left-aligned)
                subtitle = Text(
                    section["subtitle"],
                    font_size=28,
                    weight=BOLD,
                    color=WHITE
                )
                
                # Create bullets with consistent left alignment
                bullet_texts = []
                for item in section["bullets"]:
                    bullet = Text(f"- {item}", font_size=22, color=WHITE)
                    bullet_texts.append(bullet)
                
                # Arrange bullets vertically with left alignment
                bullets = VGroup(*bullet_texts)
                bullets.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
                
                # Position bullets relative to subtitle
                bullets.next_to(subtitle, DOWN, buff=0.4, aligned_edge=LEFT)
                
                # Group subtitle and bullets together
                section_group = VGroup(subtitle, bullets)
                all_content.add(section_group)
            
            # Arrange all sections vertically with tighter spacing
            all_content.arrange(DOWN, aligned_edge=LEFT, buff=0.6)
            
            # Position all content below the line, left-aligned
            all_content.next_to(line, DOWN, buff=0.6)
            all_content.to_edge(LEFT, buff=1.5)
            
            # Check if content fits and scale down if needed
            bottom_y = all_content.get_bottom()[1]  # Get y-coordinate only
            if bottom_y < -3.5:  # Bottom of visible area
                scale_factor = 3.5 / abs(bottom_y)
                all_content.scale(scale_factor)
                all_content.next_to(line, DOWN, buff=0.6)
                all_content.to_edge(LEFT, buff=1.5)
            
            # Animate sections appearing
            for section_group in all_content:
                self.play(
                    FadeIn(section_group[0]),  # subtitle
                    LaggedStartMap(FadeIn, section_group[1], lag_ratio=0.1)  # bullets
                )
                self.wait(0.5)

            self.wait(section_data.get('duration', 3))
        
        self.clear()

    def create_simple_bullets_scene(self, bullet_data):
        """Scene with title and simple bullet points"""
        self.add_background("./examples/resources/blackboard.jpg")
        
        with self.voiceover(bullet_data['voiceover']):
            # Title
            title = Text(bullet_data["title"], font_size=48, weight=BOLD, color=WHITE)
            title.to_edge(UP)
            self.play(Write(title))
            
            # Bullet points
            bullet_group = VGroup(
                *[Text(f"- {item}", font_size=32, color=WHITE).align_to(LEFT, LEFT) for item in bullet_data["bullets"]]
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.4).next_to(title, DOWN, buff=1).to_edge(LEFT)

            # Animate bullets appearing one by one
            self.play(LaggedStartMap(FadeIn, bullet_group, shift=RIGHT, lag_ratio=0.2))
            
            self.wait(bullet_data.get('duration', 3))
        
        self.clear()


    # Add this method to your DirectVideoGenerator class
    def create_quick_lecture_slide(self, slide_data):
        """Quick lecture slide with title, subtitle, bullet points, and image - OpenGL compatible"""
        self.background_color = "#f7f5f3"  
        
        with self.voiceover(slide_data['voiceover']):
            # Extract data from the slide_data
            title = slide_data["title"]
            subtitle = slide_data.get("subtitle", "")
            points = slide_data["points"]
            
            # Try to get an image using our image fetching system
            image_path = None
            if "wikipedia_topic" in slide_data:
                try:
                    image_paths = self.get_wikipedia_images(slide_data["wikipedia_topic"], num_images=1)
                    if image_paths and len(image_paths) > 0:
                        image_path = image_paths[0]
                        print(f"Found image for lecture slide: {image_path}")
                except Exception as e:
                    print(f"Error getting Wikipedia image: {e}")
            
            # If no image from Wikipedia, try direct path
            if not image_path and "image_path" in slide_data:
                image_path = slide_data["image_path"]
            
            # Create title and subtitle
            title_text = Text(title, font_size=38, weight=BOLD, color=WHITE).to_edge(UP, buff=0.7)
            subtitle_text = Text(subtitle, font_size=20, color=GRAY_B).next_to(title_text, DOWN, buff=0.2)
            
            # Create separator line
            line = Line(LEFT*6, RIGHT*6, color=WHITE, stroke_width=2).next_to(subtitle_text, DOWN, buff=0.3)
            
            # Create bullet points
            bullets = VGroup(*[Text(f"• {p}", font_size=19, color=WHITE) for p in points])
            bullets.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            bullets.next_to(line, DOWN, buff=0.6).to_edge(LEFT, buff=1.0)
            
            # Create image or placeholder - FIXED FOR OPENGL
            img = None
            try:
                if image_path and os.path.exists(image_path):
                    print(f"Attempting to load image: {image_path}")
                    
                    # Method 1: Try with absolute path
                    abs_path = os.path.abspath(image_path)
                    print(f"Absolute path: {abs_path}")
                    
                    # For OpenGL, sometimes we need to use ImageMobject instead of OpenGLImageMobject
                    try:
                        # Try OpenGLImageMobject first
                        img = OpenGLImageMobject(abs_path)
                        print("Successfully loaded with OpenGLImageMobject")
                    except Exception as e1:
                        print(f"OpenGLImageMobject failed: {e1}")
                        try:
                            # Fallback to regular ImageMobject
                            from manim import ImageMobject
                            img = ImageMobject(abs_path)
                            print("Successfully loaded with ImageMobject")
                        except Exception as e2:
                            print(f"ImageMobject also failed: {e2}")
                            img = None
                    
                    if img is not None:
                        # Scale the image appropriately
                        img.scale_to_fit_height(3.5)
                        if img.width > 4.5:
                            img.scale_to_fit_width(4.5)
                        img.next_to(line, DOWN, buff=0.6).to_edge(RIGHT, buff=1.0)
                        print("Image scaled and positioned successfully")
                    else:
                        raise Exception("Both image loading methods failed")
                        
            except Exception as e:
                print(f"Error loading image: {e}")
                # Create a more visible placeholder
                img = Rectangle(width=4, height=3, color=BLUE, fill_opacity=0.3, stroke_width=2)
                img.next_to(line, DOWN, buff=0.6).to_edge(RIGHT, buff=1.0)
                placeholder_text = Text("Image\nNot Loaded", font_size=16, color=WHITE)
                placeholder_text.move_to(img.get_center())
                img = VGroup(img, placeholder_text)
            
            # Quick animations
            self.play(Write(title_text), FadeIn(subtitle_text))
            self.play(Create(line))
            self.play(LaggedStartMap(FadeIn, bullets, lag_ratio=0.2))
            
            if img is not None:
                self.play(FadeIn(img))
            
            self.wait(slide_data.get('duration', 3))
        
        self.clear()



    def create_dual_image_comparison(self, comparison_data):
        """Scene with two images side by side for comparison"""
        #self.add_background("./examples/resources/blackboard.jpg")
        
        with self.voiceover(comparison_data['voiceover']):
            # Extract data
            title = comparison_data["title"]
            subtitle = comparison_data.get("subtitle", "")
            left_text = comparison_data["left_text"]
            right_text = comparison_data["right_text"]
            
            # Try to get images using our image fetching system
            left_image_path = None
            right_image_path = None
            
            if "left_wikipedia_topic" in comparison_data:
                try:
                    left_image_paths = self.get_wikipedia_images(comparison_data["left_wikipedia_topic"], num_images=1)
                    if left_image_paths and len(left_image_paths) > 0:
                        left_image_path = left_image_paths[0]
                        print(f"Found left image: {left_image_path}")
                except Exception as e:
                    print(f"Error getting left Wikipedia image: {e}")
            
            if "right_wikipedia_topic" in comparison_data:
                try:
                    right_image_paths = self.get_wikipedia_images(comparison_data["right_wikipedia_topic"], num_images=1)
                    if right_image_paths and len(right_image_paths) > 0:
                        right_image_path = right_image_paths[0]
                        print(f"Found right image: {right_image_path}")
                except Exception as e:
                    print(f"Error getting right Wikipedia image: {e}")
            
            # Use direct paths if Wikipedia topics not available
            if not left_image_path and "left_image_path" in comparison_data:
                left_image_path = comparison_data["left_image_path"]
            
            if not right_image_path and "right_image_path" in comparison_data:
                right_image_path = comparison_data["right_image_path"]
            
            # Title
            title_text = Text(title, font_size=38, color=WHITE).to_edge(UP, buff=0.7)
            
            # Subtitle
            subtitle_text = Text(subtitle, font_size=22, color=GRAY).next_to(title_text, DOWN, buff=0.25)
            
            # Separator line
            line = Line(LEFT*6, RIGHT*6, color=WHITE, stroke_width=2).next_to(subtitle_text, DOWN, buff=0.3)
            
            # LEFT image
            try:
                if left_image_path and os.path.exists(left_image_path):
                    left_image = OpenGLImageMobject(left_image_path)
                    left_image.scale_to_fit_height(2.8)
                    if left_image.width > 4:
                        left_image.scale_to_fit_width(4)
                else:
                    raise FileNotFoundError("Left image not found")
            except Exception as e:
                print(f"Error loading left image: {e}")
                left_image = Rectangle(width=3, height=2, color=BLUE, fill_opacity=0.2)
                error_text = Text("Left Image\nNot Found", font_size=14, color=WHITE)
                error_text.move_to(left_image.get_center())
                left_image = VGroup(left_image, error_text)
            
            left_image.next_to(line, DOWN, buff=0.6).to_edge(LEFT, buff=1.0)
            
            # LEFT text
            left_bullet = Text(f"• {left_text}", font_size=16, color=WHITE)
            left_bullet.next_to(left_image, DOWN, buff=0.6).to_edge(LEFT, buff=1.0)
            if left_bullet.width > 4.5:
                left_bullet.scale_to_fit_width(4.5)
            
            # RIGHT image
            try:
                if right_image_path and os.path.exists(right_image_path):
                    right_image = OpenGLImageMobject(right_image_path)
                    right_image.scale_to_fit_height(2.8)
                    if right_image.width > 4:
                        right_image.scale_to_fit_width(4)
                else:
                    raise FileNotFoundError("Right image not found")
            except Exception as e:
                print(f"Error loading right image: {e}")
                right_image = Rectangle(width=3, height=2, color=RED, fill_opacity=0.2)
                error_text = Text("Right Image\nNot Found", font_size=14, color=WHITE)
                error_text.move_to(right_image.get_center())
                right_image = VGroup(right_image, error_text)
            
            right_image.next_to(line, DOWN, buff=0.6).to_edge(RIGHT, buff=1.0)
            
            # RIGHT text
            right_bullet = Text(f"• {right_text}", font_size=16, color=WHITE)
            right_bullet.next_to(right_image, DOWN, buff=0.6).to_edge(RIGHT, buff=1.0)
            if right_bullet.width > 4.5:
                right_bullet.scale_to_fit_width(4.5)
            
            # Animate
            self.play(Write(title_text), FadeIn(subtitle_text))
            self.play(Create(line))
            
            # Show LEFT side first
            self.play(FadeIn(left_image), FadeIn(left_bullet))
            self.wait(0.5)
            
            # Show RIGHT side
            self.play(FadeIn(right_image), FadeIn(right_bullet))
            
            self.wait(comparison_data.get('duration', 3))
        
        self.clear()



    # Add this method to your DirectVideoGenerator class
    def create_economic_cycle(self, cycle_data):
        """Scene with rounded rectangles in a circular flow diagram"""
        self.add_background("./examples/resources/blackboard.jpg")
        
        with self.voiceover(cycle_data['voiceover']):
            # Title if provided
            if "title" in cycle_data:
                title = Text(cycle_data["title"], font_size=48, weight=BOLD, color=WHITE)
                title.to_edge(UP)
                self.play(Write(title))
            
            # Extract cycle data
            boxes = cycle_data["boxes"]
            connections = cycle_data["connections"]
            
            # Dynamically create the box groups
            groups = []
            for box_info in boxes:
                # Create rounded rectangle
                box = RoundedRectangle(corner_radius=0.2, width=4.5, height=1.2).set_color(BLUE)
                
                # Create text with proper formatting
                text_lines = box_info["text"].split('\n')
                text_objects = []
                for i, line in enumerate(text_lines):
                    text_obj = Text(line, font_size=24, color=WHITE)
                    text_objects.append(text_obj)
                
                # Arrange text vertically within the box
                text_group = VGroup(*text_objects).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                
                # Scale text if needed to fit in box
                max_text_width = box.width * 0.9
                max_text_height = box.height * 0.9
                if text_group.width > max_text_width or text_group.height > max_text_height:
                    scale_factor = min(max_text_width / text_group.width, max_text_height / text_group.height)
                    text_group.scale(scale_factor)
                
                # Center text in box
                text_group.move_to(box.get_center())
                
                # Create group and position it
                group = VGroup(box, text_group).shift(box_info["position"])
                groups.append(group)

            # Dynamically create the curved arrows
            arrows = []
            for conn in connections:
                start_group = groups[conn["start_index"]]
                end_group = groups[conn["end_index"]]
                
                # Use getattr to dynamically get the correct side of the box
                start_point = getattr(start_group, f"get_{conn['start_side']}")()
                end_point = getattr(end_group, f"get_{conn['end_side']}")()
                
                # Calculate angle for the arc based on positions
                start_pos = start_group.get_center()
                end_pos = end_group.get_center()
                
                # Determine arc direction based on positions
                angle_direction = -PI/2  # Default clockwise
                
                # Adjust angle based on relative positions for better visual flow
                if start_pos[0] > end_pos[0] and start_pos[1] > end_pos[1]:
                    angle_direction = PI/2  # Counter-clockwise for certain positions
                
                arrow = ArcBetweenPoints(start_point, end_point, angle=angle_direction).add_tip()
                arrow.set_color(WHITE)
                arrows.append(arrow)

            # Animation sequence
            for i, group in enumerate(groups):
                self.play(Create(group))
                if i < len(arrows):
                    self.play(Create(arrows[i]))
                self.wait(0.3)
            
            # Highlight the cyclical nature
            if len(groups) > 0:
                self.play(*[Flash(group, color=YELLOW, flash_radius=0.3) for group in groups], run_time=2)
            
            self.wait(cycle_data.get('duration', 3))
        
        self.clear()


        # Add this method to your DirectVideoGenerator class
    def create_fraud_triangle(self, triangle_data):
        """Scene with triangle diagram and text elements at vertices"""
        self.add_background("./examples/resources/blackboard.jpg")
        
        with self.voiceover(triangle_data['voiceover']):
            # Extract text data from the input
            title_text = triangle_data.get("title", "FRAUD\nTRIANGLE")
            pressure_text = triangle_data.get("pressure", "PRESSURE")
            opportunity_text = triangle_data.get("opportunity", "OPPORTUNITY")
            rationalization_text = triangle_data.get("rationalization", "RATIONALIZATION")
            
            # Create the main triangle
            fraud_triangle = Triangle().set_fill(BLACK, opacity=1).set_stroke(WHITE, width=4)
            fraud_triangle.scale(2.5)
            self.play(Create(fraud_triangle))

            # Create the title text
            title_obj = Text(title_text, font_size=28, weight=BOLD, color=WHITE)
            title_obj.move_to(fraud_triangle.get_center()).shift(DOWN * 0.6)
            self.play(Write(title_obj))

            # Get triangle vertices for positioning
            triangle_vertices = fraud_triangle.get_vertices()
            top_vertex = triangle_vertices[0]
            bottom_left_vertex = triangle_vertices[1]
            bottom_right_vertex = triangle_vertices[2]

            # Create the text for the three points of the triangle
            pressure_obj = Text(pressure_text, font_size=20, slant=ITALIC, weight=BOLD, color=WHITE)
            pressure_obj.move_to(top_vertex + UP * 0.4)
            
            opportunity_obj = Text(opportunity_text, font_size=20, slant=ITALIC, weight=BOLD, color=WHITE)
            opportunity_obj.move_to(bottom_right_vertex + DOWN * 0.4 + RIGHT * 0.2)
            
            rationalization_obj = Text(rationalization_text, font_size=18, weight=BOLD, color=WHITE)
            rationalization_obj.move_to(bottom_left_vertex + DOWN * 0.4 + LEFT * 0.2)

            # Animate the creation of the surrounding text
            self.play(
                Write(pressure_obj),
                Write(opportunity_obj),
                Write(rationalization_obj),
                run_time=2
            )
            
            # Add optional description if provided
            if "description" in triangle_data:
                desc_text = Text(triangle_data["description"], font_size=16, color=WHITE)
                desc_text.to_edge(DOWN, buff=0.5)
                self.play(FadeIn(desc_text))
            
            # Add optional connecting lines if specified
            if triangle_data.get("show_connecting_lines", False):
                # Create lines from vertices to text
                pressure_line = Line(top_vertex, pressure_obj.get_bottom(), color=WHITE, stroke_width=2)
                opportunity_line = Line(bottom_right_vertex, opportunity_obj.get_top(), color=WHITE, stroke_width=2)
                rationalization_line = Line(bottom_left_vertex, rationalization_obj.get_top(), color=WHITE, stroke_width=2)
                
                self.play(
                    Create(pressure_line),
                    Create(opportunity_line),
                    Create(rationalization_line)
                )

            self.wait(triangle_data.get('duration', 3))
        
        self.clear()


    def create_central_box_diagram(self, diagram_data):
        """Central box diagram with surrounding boxes and arrows (like GDP diagram)"""
        self.add_background("./examples/resources/blackboard.jpg")
        
        with self.voiceover(diagram_data['voiceover']):
            # Extract data
            center_text = diagram_data.get("center", "CENTER")
            elements = diagram_data.get("elements", [])
            
            # Predetermined colors and positions
            colors = [BLUE, GREEN, YELLOW, ORANGE, RED, PURPLE, PINK, GOLD]
            
            # Create central box with predetermined color and position
            center_box = Rectangle(width=2.5, height=1, color=BLUE)
            center_text_obj = Text(center_text, font_size=32, color=WHITE).move_to(center_box.get_center())
            center_group = VGroup(center_box, center_text_obj)
            
            # Center position is predetermined (left side)
            center_group.shift(LEFT*3)
            
            self.play(Create(center_group))
            
            # Create surrounding elements with predetermined positions and colors
            element_groups = []
            arrows = []
            
            for i, element in enumerate(elements):
                # Use predetermined color cycling through the color list
                element_color = colors[i % len(colors)]
                
                # Create element box
                element_box = Rectangle(width=4, height=1, color=element_color)
                element_text = Text(element["text"], font_size=28, color=WHITE).move_to(element_box.get_center())
                element_group = VGroup(element_box, element_text)
                
                # Predetermined positions (right side, vertically arranged)
                # Start from top and go down
                vertical_spacing = 1.5
                start_y = (len(elements) - 1) * vertical_spacing / 2
                position_y = start_y - i * vertical_spacing
                
                element_group.shift(RIGHT*3 + UP*position_y)
                
                # Create arrow from element to center
                arrow_start = element_group.get_left()
                arrow_end = center_group.get_right()
                
                # Adjust arrow end point based on element position
                if position_y > 0:  # If element is above center
                    arrow_end = center_group.get_top()
                elif position_y < 0:  # If element is below center
                    arrow_end = center_group.get_bottom()
                
                arrow = Arrow(arrow_start, arrow_end, buff=0.3, color=WHITE)
                
                element_groups.append(element_group)
                arrows.append(arrow)
                
                # Animate element and arrow
                self.play(Create(element_group), Create(arrow))
                self.wait(0.3)
            
            # Add optional title if provided
            if "title" in diagram_data:
                title_text = Text(diagram_data["title"], font_size=36, weight=BOLD, color=WHITE)
                title_text.to_edge(UP)
                self.play(Write(title_text))
            
            self.wait(diagram_data.get('duration', 3))
        
        self.clear()



    def create_gdp_measurement(self, gdp_data):
        """GDP measurement diagram with camera movements - simplified with standard colors"""

        background = OpenGLImageMobject("./examples/resources/blackboard.jpg")
        background.scale_to_fit_width(config.frame_width * 3)
        background.scale_to_fit_height(config.frame_height * 3)

        
        with self.voiceover(gdp_data['voiceover']):
            # Title
            title = Text(gdp_data.get("title", "How is GDP Measured?"), font_size=32, color=WHITE).to_edge(UP)
            self.play(Write(title))
            self.wait(1)
            
            # SECTION ONE: Left definition box
            left_box = Rectangle(width=4, height=2, color=GREEN, fill_opacity=0.1)
            left_text = Text(
                gdp_data.get("definition", "The total production\nof goods and services\nin the economy"),
                font_size=18,
                color=WHITE
            )
            left_group = VGroup(left_box, left_text).move_to(np.array([-6, 0, 0]))
            
            # Focus camera on section one
            self.play(
                self.camera.animate.scale(0.8).move_to([-6, 0, 0]),
                run_time=2
            )
            self.play(Create(left_group))
            self.wait(2)
            
            # Helper to make uniform boxes (using standard BLUE color)
            def make_box(text, width=2.8, height=1, font_size=18):
                box = Rectangle(width=width, height=height, color=BLUE, fill_opacity=0.08)
                txt = Text(text, font_size=font_size, color=WHITE).move_to(box.get_center())
                return VGroup(box, txt)
            
            # SECTION TWO: Middle column (Production, Income, Expenditure)
            mid_x = -1.5
            middle_concepts = gdp_data.get("middle_concepts", ["Production", "Income", "Expenditure"])
            
            prod_group = make_box(middle_concepts[0]).move_to(np.array([mid_x, 1.5, 0]))
            inc_group = make_box(middle_concepts[1]).move_to(np.array([mid_x, 0.0, 0]))
            exp_group = make_box(middle_concepts[2]).move_to(np.array([mid_x, -1.5, 0]))
            
            # Move camera to show both sections
            self.play(
                self.camera.animate.scale(1.2).move_to([-6, 0, 0]),
                run_time=2
            )
            
            # Show middle column with arrows from left definition
            arrow1 = Arrow(left_group.get_right(), prod_group.get_left(), buff=0.2, stroke_width=3, color=WHITE)
            arrow2 = Arrow(left_group.get_right(), inc_group.get_left(), buff=0.2, stroke_width=3, color=WHITE)
            arrow3 = Arrow(left_group.get_right(), exp_group.get_left(), buff=0.2, stroke_width=3, color=WHITE)
            
            self.play(
                Create(prod_group), Create(arrow1),
                Create(inc_group), Create(arrow2),
                Create(exp_group), Create(arrow3),
                run_time=3
            )
            self.wait(2)
            
            # SECTION THREE: GDP (P,I,E) column
            gdp_x = 3
            gdp_concepts = gdp_data.get("gdp_concepts", ["GDP (P)", "GDP (I)", "GDP (E)"])
            
            gdp_p_group = make_box(gdp_concepts[0]).move_to(np.array([gdp_x, 1.5, 0]))
            gdp_i_group = make_box(gdp_concepts[1]).move_to(np.array([gdp_x, 0.0, 0]))
            gdp_e_group = make_box(gdp_concepts[2]).move_to(np.array([gdp_x, -1.5, 0]))
            
            # Move camera to show all three sections
            self.play(
                self.camera.animate.scale(1.4).move_to([-1, 0, 0]),
                run_time=2
            )
            
            # Arrows from middle to GDP boxes
            arrow4 = Arrow(prod_group.get_right(), gdp_p_group.get_left(), buff=0.2, stroke_width=3, color=WHITE)
            arrow5 = Arrow(inc_group.get_right(), gdp_i_group.get_left(), buff=0.2, stroke_width=3, color=WHITE)
            arrow6 = Arrow(exp_group.get_right(), gdp_e_group.get_left(), buff=0.2, stroke_width=3, color=WHITE)
            
            self.play(
                Create(gdp_p_group), Create(arrow4),
                Create(gdp_i_group), Create(arrow5),
                Create(gdp_e_group), Create(arrow6),
                run_time=3
            )
            self.wait(2)
            
            # SECTION FOUR: Average box (final section)
            avg_x = 7.5
            avg_box = Rectangle(width=3.2, height=1.8, color=TEAL, fill_opacity=0.08)
            avg_text = Text(
                gdp_data.get("average_text", "Average of\nthese three –\nGDP (A)"),
                font_size=18,
                color=WHITE
            )
            avg_group = VGroup(avg_box, avg_text).move_to(np.array([avg_x, 0.0, 0]))
            
            # Move camera to show all sections
            self.play(
                self.camera.animate.scale(0.7).move_to([6, 0, 0]),
                run_time=2
            )
            
            # Connect each GDP box to the average box
            line1 = Line(gdp_p_group.get_right(), avg_group.get_left(), stroke_width=3, color=WHITE)
            line2 = Line(gdp_i_group.get_right(), avg_group.get_left(), stroke_width=3, color=WHITE)
            line3 = Line(gdp_e_group.get_right(), avg_group.get_left(), stroke_width=3, color=WHITE)
            
            self.play(Create(avg_group), run_time=2)
            self.wait(1)
            self.play(Create(line1), Create(line2), Create(line3), run_time=2)
            self.wait(2)
            
            # Final zoom out to show the complete diagram
            self.play(
                self.camera.animate.scale(1.3).move_to([0.5, 0, 0]),
                run_time=3
            )
            
            # Hold the final view
            self.wait(gdp_data.get('duration', 3))
        
        self.clear()



    def create_visual_concept_map(self, scene_data):
        """Create a visual concept map with a central concept and connected factors"""

        background = OpenGLImageMobject("./examples/resources/blackboard.jpg")
        background.scale_to_fit_width(config.frame_width * 3)
        background.scale_to_fit_height(config.frame_height * 3)
        background.move_to(ORIGIN)
        self.add(background) 
        
        # Helper function to create rounded rectangles with text
        def make_factor_box(text, width=3.5, height=1.5, color=GREEN, font_size=20):
            box = RoundedRectangle(
                width=width, 
                height=height, 
                corner_radius=0.3,
                color=color, 
                fill_opacity=1,
                fill_color=color
            )
            txt = Text(text, font_size=font_size,         
                    stroke_width=2,  
                    warn_missing_font=True,
                   
                    fill_opacity=1,  
                     weight=BOLD, 
                     disable_ligatures=True,
                     color=WHITE, 
                     line_spacing=1.1, 
                     use_svg_cache=False)
            return VGroup(box, txt)
        
        # Get data from scene_data or use defaults
        central_concept = scene_data.get('central_concept', {'text': 'Central Concept'})
        factors = scene_data.get('factors', [])
        
        # If no factors provided, use default ones
        if not factors:
            factors = [
                {'text': 'Factor 1', 'position': 'top'},
                {'text': 'Factor 2', 'position': 'left'},
                {'text': 'Factor 3', 'position': 'right'},
                {'text': 'Factor 4', 'position': 'bottom'}
            ]
        
        # Define default colors for positions
        position_colors = {
            'top': GREEN,
            'left': BLUE,
            'right': RED,
            'bottom': GRAY
        }
        
        # Define default sizes for positions
        position_sizes = {
            'top': {'width': 5, 'height': 1.2, 'font_size': 18},
            'left': {'width': 3.2, 'height': 2.2, 'font_size': 16},
            'right': {'width': 3.2, 'height': 1.8, 'font_size': 18},
            'bottom': {'width': 4, 'height': 1.4, 'font_size': 18}
        }
        
        with self.voiceover(scene_data.get('voiceover', 'This is a visual concept map.')):
            # SECTION ONE: Center - Central concept box
            central_box = RoundedRectangle(
                width=4.5, 
                height=2, 
                corner_radius=0.3,
                color=DARK_BLUE, 
                fill_opacity=0.9,
                fill_color=DARK_BLUE
            )
            central_text = Text(central_concept.get('text', 'Central Concept'), 
                                    stroke_width=2,  
                    warn_missing_font=True,
                    font_size= 24, 
                    fill_opacity=1,  
                     weight=BOLD, 
                     disable_ligatures=True,
                     color=WHITE, 
                     line_spacing=1.1, 
                     use_svg_cache=False)
            central_group = VGroup(central_box, central_text).move_to(ORIGIN)
            
            # Start camera focused on center
            self.play(
                self.camera.animate.scale(0.6).move_to(ORIGIN),
                run_time=2
            )
            self.play(Create(central_group), run_time=2)
            self.wait(1)
            
            # Process each factor
            factor_groups = []
            lines = []
            
            for i, factor in enumerate(factors):
                position = factor.get('position', ['top', 'left', 'right', 'bottom'][i % 4])
                
                # Get defaults based on position
                color = position_colors.get(position, GREEN)
                size_info = position_sizes.get(position, {'width': 3.5, 'height': 1.5, 'font_size': 20})
                
                # Determine position coordinates
                if position == 'top':
                    coords = np.array([0, 3.5, 0])
                    line_start = central_group.get_top()
                    line_end_func = lambda group: group.get_bottom()
                    camera_move = [0, 1, 0]
                    camera_scale = 1.4
                elif position == 'left':
                    coords = np.array([-4.5, 0, 0])
                    line_start = central_group.get_left()
                    line_end_func = lambda group: group.get_right()
                    camera_move = [-1, 0.5, 0]
                    camera_scale = 1.5
                elif position == 'right':
                    coords = np.array([4.5, 0, 0])
                    line_start = central_group.get_right()
                    line_end_func = lambda group: group.get_left()
                    camera_move = [0.5, 0.5, 0]
                    camera_scale = 0.8
                else:  # bottom
                    coords = np.array([0, -3.5, 0])
                    line_start = central_group.get_bottom()
                    line_end_func = lambda group: group.get_top()
                    camera_move = [0, -1, 0]
                    camera_scale = 1.4
                
                # Create factor box with default values
                factor_group = make_factor_box(
                    factor['text'], 
                    width=size_info['width'],
                    height=size_info['height'],
                    color=color,
                    font_size=size_info['font_size']
                ).move_to(coords)
                
                # Create connection line
                line = Arrow(line_start, line_end_func(factor_group), 
                            stroke_width=4, color=GRAY, buff=0.1)
                
                factor_groups.append(factor_group)
                lines.append(line)
                
                # Expand camera to show the factor
                self.play(
                    self.camera.animate.scale(camera_scale).move_to(camera_move),
                    run_time=2
                )
                
                # Create connection line and factor
                self.play(Create(factor_group), Create(line), run_time=2)
                self.wait(1)
            
            # Final view: show all factors
            self.play(
                self.camera.animate.scale(1).move_to([0, 0, 0]),
                run_time=2
            )
            
            # Add a subtle pulsing effect to the center concept
            self.play(
                central_group.animate.scale(1.1),
                run_time=0.8
            )
            self.play(
                central_group.animate.scale(1/1.1),
                run_time=0.8
            )
            
            # Hold the final view
            self.wait(scene_data.get('duration', 1.5))

        self.clear() 

    def create_circular_flow_diagram(self, scene_data):
        """Create a circular flow diagram with a central concept and connected elements"""
        
        # Set background
        background = OpenGLImageMobject("./examples/resources/blackboard.jpg")
        background.scale_to_fit_width(config.frame_width * 3)
        background.scale_to_fit_height(config.frame_height * 3)
        background.move_to(ORIGIN)
        self.add(background) 
        
        # Get data from scene_data or use defaults
        central_concept = scene_data.get('central_concept', {'text': 'Central Concept'})
        elements = scene_data.get('elements', [])
        
        # If no elements provided, use default ones
        if not elements:
            elements = [
                {'text': 'Element 1', 'position': 'top_left'},
                {'text': 'Element 2', 'position': 'top_right'},
                {'text': 'Element 3', 'position': 'bottom_right'},
                {'text': 'Element 4', 'position': 'bottom_left'}
            ]
        
        # Define colors
        text_color = WHITE  # Changed to white for better visibility on blackboard
        arrow_color = "#FF7B7B"  # Coral/pink color
        box_color = "#FFE5E5"   # Light pink for the central box
        
        with self.voiceover(scene_data.get('voiceover', 'This is a circular flow diagram.')):
            # Create the central box
            central_box = RoundedRectangle(
                width=3.5, 
                height=1.2, 
                corner_radius=0.1,
                fill_color=box_color,
                fill_opacity=0.8,
                stroke_color=text_color,
                stroke_width=2
            )
            
            # Central text - split if it contains a newline
            central_text_parts = central_concept.get('text', 'Central Concept').split('\n')
            central_text = VGroup(*[
                Text(part, font_size=28, color=text_color, weight=BOLD,
                    stroke_width=2,  
                    warn_missing_font=True,
                    fill_opacity=1,  
                     disable_ligatures=True,
                     line_spacing=1.1, 
                     use_svg_cache=False) 
                for part in central_text_parts
            ]).arrange(DOWN, buff=0.1)
            
            central_group = VGroup(central_box, central_text)
            
            # Start camera focused on center
            self.play(
                self.camera.animate.scale(0.8).move_to(ORIGIN),
                run_time=2
            )
            self.play(
                Write(central_box),
                Write(central_text),
                run_time=1.5
            )
            self.wait(0.5)
            
            # Position elements around the central concept
            element_groups = []
            radius = 3.5
            
            position_mapping = {
                'top_left': LEFT * radius + UP * 1.5,
                'top_right': RIGHT * radius + UP * 1.5,
                'bottom_right': RIGHT * radius + DOWN * 1.5,
                'bottom_left': LEFT * radius + DOWN * 1.5,
                'top': UP * radius,
                'right': RIGHT * radius,
                'bottom': DOWN * radius,
                'left': LEFT * radius
            }
            
            for i, element in enumerate(elements):
                position = element.get('position', list(position_mapping.keys())[i % len(position_mapping)])
                coords = position_mapping.get(position, UP * radius)
                
                # Create element text
                element_text = Text(element['text'], font_size=24, color=text_color, weight=BOLD)
                element_text.move_to(coords)
                element_groups.append(element_text)
                
            # Create arrows between elements with proper positioning
            arrows = []
            
            # For 4 elements in a cycle (most common case)
            if len(element_groups) == 4:
                # Arrow from top_left to top_right
                arrow1_start = element_groups[0].get_right() + RIGHT * 0.3
                arrow1_end = element_groups[1].get_left() + LEFT * 0.3
                arrow1 = CurvedArrow(
                    arrow1_start, arrow1_end,
                    color=arrow_color, stroke_width=8,
                    angle=-TAU/6
                )
                arrows.append(arrow1)
                
                # Arrow from top_right to bottom_right
                arrow2_start = element_groups[1].get_bottom() + DOWN * 0.2
                arrow2_end = element_groups[2].get_top() + UP * 0.2
                arrow2 = CurvedArrow(
                    arrow2_start, arrow2_end,
                    color=arrow_color, stroke_width=8,
                    angle=TAU/6
                )
                arrows.append(arrow2)
                
                # Arrow from bottom_right to bottom_left
                arrow3_start = element_groups[2].get_left() + LEFT * 0.3
                arrow3_end = element_groups[3].get_right() + RIGHT * 0.3
                arrow3 = CurvedArrow(
                    arrow3_start, arrow3_end,
                    color=arrow_color, stroke_width=8,
                    angle=-TAU/6
                )
                arrows.append(arrow3)
                
                # Arrow from bottom_left to top_left
                arrow4_start = element_groups[3].get_top() + UP * 0.2
                arrow4_end = element_groups[0].get_bottom() + DOWN * 0.2
                arrow4 = CurvedArrow(
                    arrow4_start, arrow4_end,
                    color=arrow_color, stroke_width=8,
                    angle=TAU/6
                )
                arrows.append(arrow4)
                
                # Animation sequence for 4 elements
                self.play(Write(element_groups[0]), run_time=1)
                self.play(Create(arrow1), run_time=1)
                self.play(Write(element_groups[1]), run_time=1)
                self.play(Create(arrow2), run_time=1)
                self.play(Write(element_groups[2]), run_time=1)
                self.play(Create(arrow3), run_time=1)
                self.play(Write(element_groups[3]), run_time=1)
                self.play(Create(arrow4), run_time=1)
            
            else:
                # Generic approach for other numbers of elements
                for i, element_text in enumerate(element_groups):
                    self.play(Write(element_text), run_time=1)
                    
                    if i < len(element_groups) - 1:
                        # Create arrow to next element
                        start_pos = element_text.get_center()
                        end_pos = element_groups[i+1].get_center()
                        
                        # Determine arrow connection points based on relative positions
                        if element_text.get_center()[0] < element_groups[i+1].get_center()[0]:
                            # Rightward arrow
                            start_pos = element_text.get_right() + RIGHT * 0.3
                            end_pos = element_groups[i+1].get_left() + LEFT * 0.3
                        else:
                            # Leftward arrow
                            start_pos = element_text.get_left() + LEFT * 0.3
                            end_pos = element_groups[i+1].get_right() + RIGHT * 0.3
                        
                        if element_text.get_center()[1] < element_groups[i+1].get_center()[1]:
                            # Upward arrow
                            start_pos = element_text.get_top() + UP * 0.2
                            end_pos = element_groups[i+1].get_bottom() + DOWN * 0.2
                        else:
                            # Downward arrow
                            start_pos = element_text.get_bottom() + DOWN * 0.2
                            end_pos = element_groups[i+1].get_top() + UP * 0.2
                        
                        arrow = CurvedArrow(
                            start_pos, end_pos,
                            color=arrow_color, stroke_width=8,
                            angle=-TAU/8
                        )
                        arrows.append(arrow)
                        self.play(Create(arrow), run_time=1)
                
                # Connect last element to first if needed
                if len(element_groups) > 1:
                    start_pos = element_groups[-1].get_center()
                    end_pos = element_groups[0].get_center()
                    
                    # Determine connection points
                    if element_groups[-1].get_center()[0] < element_groups[0].get_center()[0]:
                        # Rightward arrow
                        start_pos = element_groups[-1].get_right() + RIGHT * 0.3
                        end_pos = element_groups[0].get_left() + LEFT * 0.3
                    else:
                        # Leftward arrow
                        start_pos = element_groups[-1].get_left() + LEFT * 0.3
                        end_pos = element_groups[0].get_right() + RIGHT * 0.3
                    
                    if element_groups[-1].get_center()[1] < element_groups[0].get_center()[1]:
                        # Upward arrow
                        start_pos = element_groups[-1].get_top() + UP * 0.2
                        end_pos = element_groups[0].get_bottom() + DOWN * 0.2
                    else:
                        # Downward arrow
                        start_pos = element_groups[-1].get_bottom() + DOWN * 0.2
                        end_pos = element_groups[0].get_top() + UP * 0.2
                    
                    closing_arrow = CurvedArrow(
                        start_pos, end_pos,
                        color=arrow_color, stroke_width=8,
                        angle=TAU/8
                    )
                    arrows.append(closing_arrow)
                    self.play(Create(closing_arrow), run_time=1)
            
            self.wait(1)
            
            # Highlight the cycle by pulsing the arrows
            arrow_group = VGroup(*arrows)
            
            for _ in range(2):
                self.play(
                    arrow_group.animate.set_stroke(width=12),
                    run_time=0.5
                )
                self.play(
                    arrow_group.animate.set_stroke(width=8),
                    run_time=0.5
                )
            
            self.wait(1)
            
            # Final emphasis on the central concept
            self.play(
                central_box.animate.set_fill(opacity=1.0),
                central_text.animate.scale(1.1),
                run_time=1
            )
            
            # Hold the final view
            self.wait(scene_data.get('duration', 3))
            
        self.clear()

    
    def create_chemistry_scene(self, scene_data):
        """Create a chemistry scene showing 3D molecular structures with OpenGL"""
        
        # Set background
        background = OpenGLImageMobject("./examples/resources/blackboard.jpg")
        background.scale_to_fit_width(config.frame_width * 3)
        background.scale_to_fit_height(config.frame_height * 3)
        background.move_to(ORIGIN)
        self.add(background)
        
        # Get compound data from scene_data
        compound_name = scene_data.get('compound', 'morphine')
        title_text = scene_data.get('title', f'{compound_name.capitalize()} Molecular Structure')
        
        with self.voiceover(scene_data.get('voiceover', f'This is the molecular structure of {compound_name}.')):
            # Download MOL file
            mol_file = f"{compound_name.lower()}.mol"
            self.download_mol_file(mol_file, compound_name)
            
            # Create the scene
            if os.path.exists(mol_file):
                try:
                    # Create 3D molecule object - this is OpenGL compatible!
                    molecule = ThreeDMolecule.molecule_from_file(mol_file)
                    molecule.scale_to_fit_width(4)
                    
                    # Create title
                    title = Text(title_text, font_size=36, color=WHITE)
                    title.to_edge(UP, buff=0.5)
                    
                    # Add compound information if available
                    #compound_info = self.get_compound_info(compound_name)
                    
                    # Display molecule and title
                    self.play(Write(title), run_time=1.5)
                    self.play(Create(molecule), run_time=2)
                    self.wait(1)
                    
                    # Show additional information if available
                    ##if compound_info:
                    ##   info_text = Text(compound_info, font_size=20, color=WHITE)
                    ##    info_text.next_to(molecule, DOWN, buff=0.5)
                    ##    self.play(Write(info_text), run_time=1.5)
                    ##    self.wait(1)
                    
                    # Highlight different parts of the molecule
                    self.play(
                        molecule.animate.set_color_by_gradient(BLUE, GREEN, YELLOW),
                        run_time=2
                    )
                    
                    # Rotate molecule for better 3D view
                    self.play(
                        molecule.animate.rotate(PI/2, axis=UP),
                        run_time=3
                    )
                    
                    # Additional 3D rotation for dramatic effect
                    self.play(
                        molecule.animate.rotate(PI/4, axis=RIGHT),
                        run_time=2
                    )
                    
                    self.wait(scene_data.get('duration', 3))
                    
                except Exception as e:
                    print(f"Error creating 3D molecule: {e}")
                    self.show_chemistry_error(compound_name)
            else:
                self.show_chemistry_error(compound_name)
        
        self.clear()

    def download_mol_file(self, filename, compound_name):
        """Download MOL file from PubChem"""
        try:
            # Get compound CID
            search_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}/property/MolecularFormula/JSON"
            response = requests.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                cid = data['PropertyTable']['Properties'][0]['CID']
                
                # Download MOL file
                mol_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF"
                mol_response = requests.get(mol_url, timeout=10)
                
                if mol_response.status_code == 200:
                    with open(filename, 'w') as f:
                        f.write(mol_response.text)
                    print(f"Downloaded {filename}")
                    return True
        except Exception as e:
            print(f"Download failed: {e}")
        
        return False

    def get_compound_info(self, compound_name):
        """Get additional compound information from PubChem"""
        try:
            # Get basic compound information
            info_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}/property/MolecularFormula,MolecularWeight,IUPACName/JSON"
            response = requests.get(info_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                props = data['PropertyTable']['Properties'][0]
                
                info_lines = [
                    f"Molecular Formula: {props.get('MolecularFormula', 'N/A')}",
                    f"Molecular Weight: {props.get('MolecularWeight', 'N/A')}",
                    f"IUPAC Name: {props.get('IUPACName', 'N/A')[:50]}..." if props.get('IUPACName') and len(props.get('IUPACName', '')) > 50 else f"IUPAC Name: {props.get('IUPACName', 'N/A')}"
                ]
                
                return "\n".join(info_lines)
        except Exception as e:
            print(f"Error getting compound info: {e}")
        
        return None

    def show_chemistry_error(self, compound_name):
        """Show error message when compound cannot be loaded"""
        error_title = Text("Chemistry Structure Error", font_size=32, color=RED)
        error_msg = Text(f"Could not load: {compound_name}", font_size=24, color=WHITE)
        
        error_group = VGroup(error_title, error_msg).arrange(DOWN, buff=0.5)
        self.play(Write(error_group), run_time=2)
        self.wait(2)

    def create_country_map_scene(self, scene_data):
        """Create a country map scene showing a geographic map"""
        
        # Set background
        #background = OpenGLImageMobject("./examples/resources/blackboard.jpg")
        #background.scale_to_fit_width(config.frame_width * 3)
        #background.scale_to_fit_height(config.frame_height * 3)
        #background.move_to(ORIGIN)
        #self.add(background)
        
        # Get country data from scene_data
        country_name = scene_data.get('country', 'Uganda')
        title_text = scene_data.get('title', f'{country_name} Map')
        
        with self.voiceover(scene_data.get('voiceover', f'This is a map of {country_name}.')):
            # Generate the country map
            self.create_country_map(country_name)
            
            # Create and display title
            title = Text(title_text, font_size=48, color=WHITE)
            title.to_edge(UP, buff=1)
            self.play(Write(title), run_time=1.5)
            
            # Load and display the map
            if os.path.exists('country_map.png'):
                try:
                    country_map = OpenGLImageMobject('country_map.png')
                    country_map.scale_to_fit_width(4.5)  # Slightly smaller for better fit
                    country_map.move_to(ORIGIN + DOWN * 0.3)
                    self.play(FadeIn(country_map), run_time=2)
                    
                    # Add some highlighting effect
      
                    
                except Exception as e:
                    print(f"Error loading map: {e}")
                    # Show error message
                    error_text = Text("Map not available", font_size=32, color=RED)
                    error_text.move_to(ORIGIN)
                    self.play(Write(error_text), run_time=1)
            else:
                # Show placeholder if no map
                placeholder = Rectangle(width=8, height=5, color=BLUE, fill_opacity=0.3)
                placeholder_text = Text("Map not found", color=WHITE, font_size=24)
                placeholder_group = VGroup(placeholder, placeholder_text)
                placeholder_group.move_to(ORIGIN)
                self.play(Create(placeholder_group), run_time=1.5)
            
            # Hold the scene
            self.wait(scene_data.get('duration', 3))
        
        # Clean up
        if os.path.exists('country_map.png'):
            try:
                os.remove('country_map.png')
            except:
                pass
        
        self.clear()

    def create_country_map(self, country_name):
        """Generate country map using the country name"""
        try:
            print(f"Generating map for {country_name}...")
            
            # Download world data
            world_url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
            world = gpd.read_file(world_url)
            
            # Find country by name (case insensitive)
            country = world[world['NAME'].str.upper() == country_name.upper()]
            
            # If not found by NAME, try NAME_LONG
            if country.empty:
                country = world[world['NAME_LONG'].str.upper() == country_name.upper()]
            
            # If still not found, try partial match
            if country.empty:
                country = world[world['NAME'].str.contains(country_name, case=False, na=False)]
            
            if not country.empty:
                # Create the map
                fig, ax = plt.subplots(figsize=(10, 6))
                country.plot(ax=ax, 
                        color='#2E8B57',      # Sea green
                        edgecolor='white',    # White border
                        linewidth=3)
                
                # Dark background
                fig.patch.set_facecolor('black')
                ax.set_facecolor('black')
                ax.set_axis_off()
                
                plt.tight_layout()
                
                # Save the map
                plt.savefig('country_map.png', 
                        dpi=300, 
                        bbox_inches='tight',
                        facecolor='black',
                        edgecolor='none')
                
                plt.close()
                print(f"Map for {country_name} saved successfully!")
                return True
            else:
                print(f"Country '{country_name}' not found in the database")
                return False
                
        except Exception as e:
            print(f"Error generating map: {e}")
            return False


    def construct(self):
        # Commented out GTTS service
        # try:
        #     self.set_speech_service(GTTSService())
        #     print("Using Google Text-to-Speech service")
        # except Exception as e:
        #     print(f"Error setting up GTTS: {e}")
        
        try:
            self.set_speech_service(AzureService(voice="en-US-SteffanNeural", style="newscast"))
            print("Using Azure Text-to-Speech service")
        except Exception as e2:
            print(f"Error setting up Azure TTS: {e2}")
            print("WARNING: No speech service available!")
        
        if self.all_content.get('background_music'):
            try:
                self.add_background_music(self.all_content['background_music'])
                print(f"Added background music: {self.all_content['background_music']}")
            except Exception as e:
                print(f"Error adding background music: {e}")
        
        for scene in self.all_content['scenes']:
            scene_type = scene['type']
            print(f"Processing scene of type: {scene_type}")
            
            try:
                if scene_type == 'title':
                    self.create_title_scene(scene)
                elif scene_type == 'overview':
                    self.create_overview_scene(scene)
                elif scene_type == 'code':
                    self.create_code_scene(scene)
                elif scene_type == 'sequence':
                    self.create_sequence_diagram(scene)
                elif scene_type == 'image_text':
                    self.create_image_text_scene(scene)
                elif scene_type == 'multi_image_text':
                    self.create_multi_image_text_scene(scene)
                elif scene_type == 'triangle':
                    self.create_triangle_scene(scene)
                elif scene_type == 'timeline':
                    self.create_timeline_scene(scene)
                elif scene_type == 'data_processing_flow':
                    self.create_data_processing_flow(scene)
                elif scene_type == 'bullet_points':
                    self.create_bullet_points_scene(scene)
                elif scene_type == 'plan':
                    self.create_plan_scene(scene)
                elif scene_type == 'multi_section_bullets':
                    self.create_multi_section_bullets_scene(scene)
                elif scene_type == 'simple_bullets':
                    self.create_simple_bullets_scene(scene)
                elif scene_type == 'quick_lecture_slide':
                    self.create_quick_lecture_slide(scene)
                elif scene_type == 'dual_image_comparison':
                    self.create_dual_image_comparison(scene)
                elif scene_type == 'cycle_diagram':
                    self.create_economic_cycle(scene)
                elif scene_type == 'pain_triangle':
                    self.create_fraud_triangle(scene)
                elif scene_type == 'central_diagram':
                    self.create_central_box_diagram(scene)
                elif scene_type == 'flow_diagram':
                    self.create_gdp_measurement(scene)
                elif scene_type == 'visual_concept_map':
                    self.create_visual_concept_map(scene)
                elif scene_type == 'circular_flow_diagram':
                    self.create_circular_flow_diagram(scene) 
                elif scene_type == 'chemistry':
                    self.create_chemistry_scene(scene)  
                elif scene_type == 'country_map':
                    self.create_country_map_scene(scene) 


                else:
                    print(f"Warning: Unknown scene type: {scene_type}")
            except Exception as e:
                print(f"Error processing {scene_type} scene: {e}")
            
            if scene != self.all_content['scenes'][-1]:
                try:
                    with self.voiceover(scene.get('transition_text', 'Moving on.')):
                        self.clear()
                        self.wait(0.5)
                except Exception as e:
                    print(f"Error with transition: {e}")
                
                self.clear()
                self.wait(0.5)
        
        try:
            self.goodbye()
        except Exception as e:
            print(f"Error with goodbye scene: {e}")

def generate_video_from_json(json_content):
    """Generate video from JSON with dynamic scene naming"""
    output_name = json_content.get('output_name', 'GeneratedVideo')
    print(f"Generating video with output_name: {output_name}")

    config.output_file = ""
    config.disable_caching = True
    config.flush_cache = True
    config.write_to_movie = True
    config.format = 'mp4'
    config.frame_rate = 30
    config.quality = "low_quality"
    config.tex_template = "custom_template.tex"
    
    config.partial_movie_dir = os.path.join(config.video_dir, "partial_movie_files", output_name)
    
    print(f"Current config output_file: {config.output_file}")
    print(f"Using scene name: {output_name}")
    
    DynamicScene = type(
        output_name, 
        (DirectVideoGenerator,),
        {'__module__': __name__}
    )
    
    print(f"DynamicScene class name: {DynamicScene.__name__}")
    
    scene = DynamicScene(json_content)
    #scene.add_background("./examples/resources/blackboard.jpg") 
    scene.render()

    temp_files = [
        f"{output_name}.log",
        f"media/tex_files/{output_name}",
        f"media/texts/{output_name}"
    ]
    for f in temp_files:
        if os.path.exists(f):
            try:
                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.remove(f)
            except Exception as e:
                print(f"Warning: Failed to clean up {f}: {str(e)}")

# Simplified JSON - no colors, no positions, everything predetermined
example_json = example_json = {
    "output_name": "Economic_Cycle_Demo",
    "scenes": [  # <-- wrap your economic cycle inside this list
        {
            "type": "cycle_diagram",
            "title": "Economic Cycle Overview",
            "voiceover": "This diagram shows the basic economic cycle between households, businesses, and the government.",
            "duration": 6,
            "boxes": [
                {"text": "Households\n(Consumers)", "position": [-4, 0, 0]},
                {"text": "Businesses\n(Producers)", "position": [0, 3, 0]},
                {"text": "Government\n(Taxes & Spending)", "position": [4, 0, 0]},
                {"text": "Financial Sector\n(Banks & Loans)", "position": [0, -3, 0]}
            ],
            "connections": [
                {"start_index": 0, "start_side": "top", "end_index": 1, "end_side": "left"},
                {"start_index": 1, "start_side": "right", "end_index": 2, "end_side": "top"},
                {"start_index": 2, "start_side": "bottom", "end_index": 3, "end_side": "right"},
                {"start_index": 3, "start_side": "left", "end_index": 0, "end_side": "bottom"}
            ]
        }
    ]
}

# Clean only the "overview" and "timeline" scene types
cleaned_json = clean_json(example_json, scene_types_to_clean=['timeline', 'sequence'])
print(json.dumps(cleaned_json, indent=2))

if __name__ == "__main__":
    # Use directly with JSON
    generate_video_from_json(example_json)
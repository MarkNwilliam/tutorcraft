import json
import tempfile
import os
from manim_voiceover import VoiceoverScene
from code_video import CodeScene, AutoScaled, SequenceDiagram, TextBox, Connection
from manim_voiceover.services.gtts import GTTSService
from code_video.widgets import DEFAULT_FONT
from manim.mobject.types.image_mobject import ImageMobject  # Import ImageMobject
from voiceover_sequence_diagram_scene import VoiceoverSequenceDiagramScene
from manim import * 
from manim_voiceover.services.azure import AzureService
import requests
from PIL import Image
import io
from manim.opengl import *


def get_wikipedia_images(article_title, num_images=2, save_dir="./downloaded_images"):
    """
    Fetches images from a Wikipedia article or related articles using the search API.

    Parameters:
    - article_title (str): The title or keyword to search for on Wikipedia.
    - num_images (int): The number of images to fetch.
    - save_dir (str): The directory where images will be saved.

    Returns:
    - list: A list of file paths to the downloaded images.
    """
    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Define a custom User-Agent header
    headers = {
        "User-Agent": "DocVideoMaker/1.0 (https://example.com; contact@example.com)"
    }

    # Step 1: Check if the article exists
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": article_title,
        "prop": "images",
        "imlimit": 20  
    }
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    print("Image data:", data)  # Debug API response
    
    pages = data.get("query", {}).get("pages", {})
    page_id = list(pages.keys())[0] if pages else None

    # Step 2: If the article is missing, use the search API
    if not page_id or "missing" in pages[page_id]:
        print(f"No article found for topic: {article_title}. Searching for related articles...")
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": article_title,
            "srlimit": 1  # Get the top result
        }
        search_response = requests.get(search_url, params=search_params, headers=headers)
        search_data = search_response.json()
        print("Search response:", search_data)  # Debug search response
        
        if "query" in search_data and "search" in search_data["query"]:
            # Use the title of the top search result
            article_title = search_data["query"]["search"][0]["title"]
            print(f"Using related article: {article_title}")
        else:
            print(f"No related articles found for topic: {article_title}")
            return []

    # Step 3: Fetch images from the (possibly updated) article title
    params["titles"] = article_title
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    print("Updated image data:", data)  # Debug updated API response
    
    pages = data.get("query", {}).get("pages", {})
    page_id = list(pages.keys())[0] if pages else None
    if not page_id or "images" not in pages[page_id]:
        print(f"No images found for the article: {article_title}")
        return []
    
    image_titles = [
        img["title"] for img in pages[page_id]["images"]
        if not img["title"].lower().endswith(".svg") and "logo" not in img["title"].lower() and "icon" not in img["title"].lower()
    ]
    print("Filtered image titles:", image_titles)  # Debug filtered titles
    
    image_titles = image_titles[:num_images]
    image_paths = []
    
    for title in image_titles:
        img_params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "imageinfo",
            "iiprop": "url"
        }
        
        img_response = requests.get(url, params=img_params, headers=headers)
        img_data = img_response.json()
        print("Image URL data:", img_data)  # Debug URL response
        
        img_pages = img_data.get("query", {}).get("pages", {})
        img_id = list(img_pages.keys())[0] if img_pages else None
        if img_id and "imageinfo" in img_pages[img_id]:
            img_url = img_pages[img_id]["imageinfo"][0]["url"]
            print("Downloading image from:", img_url)  # Debug image URL
            
            try:
                img_response = requests.get(img_url, headers=headers)
                img_response.raise_for_status()  # Ensure the request was successful
                
                # Validate content type
                if "image" not in img_response.headers.get("Content-Type", ""):
                    print(f"Invalid content type for URL: {img_url}")
                    continue
                
                # Save the image to the specified directory
                file_name = os.path.basename(img_url)
                save_path = os.path.join(save_dir, file_name)
                with open(save_path, "wb") as img_file:
                    img_file.write(img_response.content)
                
                # Validate the image using PIL
                try:
                    with Image.open(save_path) as img:
                        img.verify()  # Verify the image is valid
                    image_paths.append(save_path)
                except Exception as e:
                    print(f"Invalid image file: {save_path}, error: {e}")
                    os.unlink(save_path)  # Remove invalid file
                
            except Exception as e:
                print(f"Error downloading image: {e}")
    
    print("Downloaded image paths:", image_paths)  # Debug downloaded paths
    return image_paths

class ComprehensiveVideoGenerator(CodeScene, VoiceoverSequenceDiagramScene):
    def __init__(self, content=None):
        super().__init__()
        if content is None:
            content = self.load_default_content()
        self.all_content = content

        self.add_background("./examples/resources/blackboard.jpg")
        

    def load_default_content(self):
        # Load default content from a JSON file or define it here
        with open('video_config.json', 'r') as f:
            return json.load(f)
        
    def create_title_scene(self, title_data):
        """
        Creates a title scene with optional background and subtitle.
        
        Parameters:
        title_data (dict): A dictionary containing the title scene data.
            - 'background' (str): Path to the background image (optional).
            - 'main_text' (str): The main title text.
            - 'font' (str): Font for the title text (default: 'Helvetica').
            - 'subtitle' (str): The subtitle text (optional).
            - 'voiceover' (str): The voiceover text for the title.
            - 'duration' (int): Duration to display the title scene (default: 3 seconds).
        """
        
        # Add background if specified
        if 'background' in title_data:
            self.add_background(title_data['background'])
        else:
            self.add_background("./examples/resources/blackboard.jpg")
        
        # Add voiceover for the title
        with self.voiceover(title_data['voiceover']):
            # Create and display the main title
            title = Text(title_data['main_text'], font=title_data.get('font', 'Helvetica'))
            self.play(Create(title))
            
            # Create and display the subtitle if specified
            if 'subtitle' in title_data:
                subtitle = Text(title_data['subtitle'], font=title_data.get('font', 'Helvetica'))
                subtitle.scale(0.6)
                subtitle.next_to(title, direction=DOWN, buff=LARGE_BUFF)
                self.play(FadeIn(subtitle))
            
            # Wait for the specified duration before clearing the scene
            self.wait(title_data.get('duration', 0.5))
        
        # Clear the scene
        self.clear()

    def create_overview_scene(self, overview_data):
        """
        Creates an overview scene with optional subtitle.
        
        Parameters:
        overview_data (dict): A dictionary containing the overview scene data.
            - 'text' (str): The main overview text.
            - 'font' (str): Font for the overview text (default: 'Helvetica').
            - 'voiceover' (str): The voiceover text for the overview.
            - 'duration' (int): Duration to display the overview scene (default: 3 seconds).
            - 'subtitle' (str): The subtitle text (optional).
            - 'subtitle_duration' (int): Duration to display the subtitle (default: 2 seconds).
            - 'creation_time' (int): Time to create the overview text (default: 10 seconds).
        """
        self.add_background("./examples/resources/blackboard.jpg")
      
        # Add voiceover for the overview
        with self.voiceover(overview_data['voiceover']):
            # Create and display the subtitle first if specified
            if 'subtitle' in overview_data:
                # Use MarkupText for better styling with Pango
                subtitle = Title(overview_data['subtitle'])
                subtitle.scale(0.8)
                subtitle.to_edge(UP)  # Position the subtitle at the top
                self.play(FadeIn(subtitle, run_time=1.5))  # Smooth fade-in animation for the subtitle
                self.wait(overview_data.get('subtitle_duration', 0.5))  # Wait for the specified duration
        
            
            # Create and display the main overview text
            text = AutoScaled(MarkupText(
                overview_data['text']
            ))
            self.play(FadeIn(text, run_time=2))  # Fade in the title smoothly
            self.wait(overview_data.get('duration', 0.5))  # Pause for the specified duration
        
        # Clear the scene
        self.clear()

    def create_code_scene(self, code_data):
        self.add_background("./examples/resources/blackboard.jpg")
       
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(code_data['code'])
            temp_path = temp_file.name

        try:
            tex = self.create_code(temp_path)
            
            with self.voiceover(f"Let's look at {code_data['title']}"):
                self.play(Create(tex))
            self.wait(1)

            with self.voiceover(code_data['intro']['text']):
                self.highlight_none(tex)
                self.wait(1)

            code_lines = code_data['code'].split('\n')
            sections = []
            start_line = None

            for i, line in enumerate(code_lines):
                if line.strip().startswith('#'):
                    if start_line is not None:
                        sections.append((start_line, i))
                    start_line = i + 1  # Manim lines are 1-indexed
                elif line.strip() == '' and start_line is not None:
                    sections.append((start_line, i))
                    start_line = None

            if start_line is not None:
                sections.append((start_line, len(code_lines)))

            for section, section_data in zip(sections, code_data['sections']):
                start_line, end_line = section
                with self.voiceover(section_data['voiceover']):
                    self.highlight_lines(
                        tex, 
                        start_line, 
                        end_line, 
                        section_data['title']
                    )
                    self.wait(0.5)

            with self.voiceover(code_data['conclusion']['text']):
                self.highlight_none(tex)
                self.wait(0.5)

        finally:
            os.unlink(temp_path)

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
        # Add all actors first
        actors = {}
        actor_names = sequence_data["actors"]
        actor_objects = diagram.add_objects(*actor_names)
        
        # Map actor names to their objects
        for name, obj in zip(actor_names, actor_objects):
            actors[name] = obj

        # Process each interaction from the JSON
        for interaction in sequence_data["interactions"]:
            source = actors[interaction["from"]]
            
            if interaction["type"] == "note":
                source.note(
                    message=interaction["message"],
                    voiceover=interaction["voiceover"]
                )
            else:  # type == "message"
                target = actors[interaction["to"]]
                source.to(
                    target,
                    message=interaction["message"],
                    voiceover=interaction["voiceover"]
                )

        # Add title
        title = Text(sequence_data["title"], font=DEFAULT_FONT)
        title.scale(0.8)
        title.to_edge(UP)

        self.add(title)
        diagram.next_to(title, DOWN)
        self.play(Create(diagram))

        self.create_diagram_with_voiceover(diagram)
        self.wait(0.4)
        self.clear()

    def goodbye(scene: CodeScene):
        # Keeping original conclusion exactly as is
        logo_path = "./yeefm logo.png"
        logo = OpenGLImageMobject(logo_path).scale(0.5)
        
        text = Text("Download YeeFM and Subscribe", font_size=40)
        logo.next_to(text, UP, buff=0.5)
        group = Group(logo, text).move_to(ORIGIN)

        with scene.voiceover(text="Download YeeFM and Subscribe") as tracker:
            scene.play(FadeIn(logo), FadeIn(text), run_time=tracker.duration)
            
        scene.wait(0.5)
        scene.play(*[FadeOut(mob) for mob in scene.mobjects])


    def add_background(self, path):
        try:
            background = OpenGLImageMobject(path)
            self.add(background)
        except OSError as e:
            print(f"Error loading background image: {e}")
    
    def create_image_text_scene(self, scene_data):
        """
        Creates a scene with a title, explanatory text, and images fetched from Wikipedia.

        Parameters:
        scene_data (dict): A dictionary containing the scene data.
            - 'title' (str): Title for the scene.
            - 'text' (str): Explanatory text to display.
            - 'wikipedia_topic' (str): Wikipedia topic to fetch images for.
            - 'num_images' (int): Number of images to fetch (default: 2).
            - 'voiceover' (str): The voiceover text for the scene.
            - 'duration' (int): Duration to display the scene (default: 5 seconds).
        """
        self.add_background("./examples/resources/blackboard.jpg")
        
        # Add voiceover for the scene
        with self.voiceover(scene_data['voiceover']):
            # Create and display the title
            title = Title(scene_data['title'])
            title.to_edge(UP)
            self.play(FadeIn(title, run_time=1))
            
            # Create and display the explanatory text
            text = AutoScaled(MarkupText(scene_data['text']))
            text.next_to(title, DOWN, buff=0.5)
            self.play(FadeIn(text, run_time=1))
            
            # Fetch images from Wikipedia
            num_images = scene_data.get('num_images', 2)
            image_paths = get_wikipedia_images(scene_data['wikipedia_topic'], num_images)
            
            # If no images found, create placeholders
            images = []
            if not image_paths:
                for i in range(num_images):
                    placeholder = Rectangle(width=4, height=3, color=RED)
                    placeholder_text = Text(f"No image {i+1} found", font_size=20).move_to(placeholder.get_center())
                    images.append(Group(placeholder, placeholder_text))
            else:
                for path in image_paths:
                    try:
                        img = OpenGLImageMobject(path)
                        img.width = 3  # Default width for images
                        images.append(img)
                    except Exception as e:
                        print(f"Error loading image: {e}")
                        placeholder = Rectangle(width=3, height=2.25, color=RED)
                        placeholder_text = Text("Image load failed", font_size=18).move_to(placeholder.get_center())
                        images.append(Group(placeholder, placeholder_text))
            
            # Arrange images horizontally
            image_group = Group(*images).arrange(RIGHT, buff=0.5)
            image_group.next_to(text, DOWN, buff=0.5)
            
            # Animate the images
            for img in images:
                self.play(FadeIn(img, run_time=0.5))
            
            # Wait for the specified duration
            self.wait(scene_data.get('duration', 5))
        
        # Clear the scene
        self.clear()


    def create_multi_image_text_scene(self, image_text_data):
        """
        Creates a scene with multiple images and explanatory text.
        Supports fallback keywords for fetching images from Wikipedia.
        """
        print(f"Creating scene: {image_text_data.get('title', 'Untitled')}")
        print(f"Image paths: {image_text_data.get('image_paths', [])}")
        self.add_background("./examples/resources/blackboard.jpg")
        
        # Add voiceover for the scene
        with self.voiceover(image_text_data['voiceover']):
            # Create title if specified
            if 'title' in image_text_data:
                title = Title(image_text_data['title'])
                title.to_edge(UP)
                self.play(FadeIn(title, run_time=1))
            
            # Get images from Wikipedia or use provided image paths
            images = []
            if 'wikipedia_topics' in image_text_data:
                num_images = image_text_data.get('num_images', 2)
                keywords = image_text_data['wikipedia_topics']
                print(f"Searching for images using keywords: {keywords}")
                
                image_paths = []
                for keyword in keywords:
                    print(f"Trying keyword: {keyword}")
                    image_paths = get_wikipedia_images(keyword, num_images)
                    if image_paths:
                        print(f"Images found for keyword: {keyword}")
                        break
                    else:
                        print(f"No images found for keyword: {keyword}")
                
                # If no images found, create placeholders
                if not image_paths:
                    print(f"No images found for any of the keywords: {keywords}")
                    for i in range(num_images):
                        print(f"Creating placeholder for image {i+1}")
                        placeholder = Rectangle(width=4, height=3, color=RED)
                        placeholder_text = Text(f"No image {i+1} found", font_size=20).move_to(placeholder.get_center())
                        images.append(Group(placeholder, placeholder_text))
                else:
                    for path in image_paths:
                        print(f"\n--- Attempting to load image: {path} ---")
                        print(f"Image path exists: {os.path.exists(path)}")
                        if os.path.exists(path):
                            print(f"Image path permissions: {oct(os.stat(path).st_mode)[-3:]}")
                            print(f"Image file size: {os.path.getsize(path)} bytes")
                        
                        try:
                            print("Loading image with ImageMobject...")
                            img = OpenGLImageMobject(path)
                            print(f"Image loaded successfully - dimensions: {img.width} x {img.height}")
                            
                            if 'image_width' in image_text_data:
                                print(f"Setting custom width: {image_text_data['image_width']}")
                                img.width = image_text_data['image_width']
                            else:
                                print("Setting default width: 3")
                                img.width = 3  # Default width for multiple images
                            
                            print("Adding image to collection")
                            images.append(img)
                            
                        except Exception as e:
                            print(f"Error loading image: {str(e)}")
                            print(f"Error type: {type(e).__name__}")
                            print("Creating placeholder for failed image")
                            placeholder = Rectangle(width=3, height=2.25, color=RED)
                            placeholder_text = Text("Image load failed", font_size=18)
                            placeholder_text.move_to(placeholder.get_center())
                            images.append(Group(placeholder, placeholder_text))
            
            elif 'image_paths' in image_text_data:
                for path in image_text_data['image_paths']:
                    try:
                        img = OpenGLImageMobject(path)
                        if 'image_width' in image_text_data:
                            img.width = image_text_data['image_width']
                        else:
                            img.width = 3  # Default width for multiple images
                        images.append(img)
                    except Exception as e:
                        print(f"Error loading image: {e}")
                        placeholder = Rectangle(width=3, height=2.25, color=RED)
                        placeholder_text = Text("Image load failed", font_size=18).move_to(placeholder.get_center())
                        images.append(Group(placeholder, placeholder_text))
            
            # Create text
            text = AutoScaled(MarkupText(image_text_data['text']))
            
            # Arrange images based on layout
            layout = image_text_data.get('layout', 'horizontal')
            image_group = None
            
            if layout == 'horizontal':
                image_group = Group(*images).arrange(RIGHT, buff=0.5)
            else:  # vertical
                image_group = Group(*images).arrange(DOWN, buff=0.5)
            
            # Position text and images
            if 'title' in image_text_data:
                # With title
                text.next_to(title, DOWN, buff=0.5)
                image_group.next_to(text, DOWN, buff=0.5)
            else:
                # Without title
                text.to_edge(UP, buff=1)
                image_group.next_to(text, DOWN, buff=0.5)
            
            # Center everything
            full_group = Group(text, image_group)
            full_group.move_to(ORIGIN)
            
            # Animate
            self.play(FadeIn(text), run_time=1)
            for img in images:
                self.play(FadeIn(img), run_time=0.5)
            
            # Wait for the specified duration
            self.wait(image_text_data.get('duration', 5))

    
    def create_triangle_scene(self, triangle_data):
        """
        Creates a triangle scene with connected components.
        
        Parameters:
        triangle_data (dict): A dictionary containing the triangle scene data.
            - 'title' (str): Title for the scene (optional).
            - 'top_text' (str): Text for the top component.
            - 'left_text' (str): Text for the left/bottom-left component.
            - 'right_text' (str): Text for the right/bottom-right component.
            - 'top_to_left' (str): Text for connection from top to left (optional).
            - 'top_to_right' (str): Text for connection from top to right (optional).
            - 'left_to_right' (str): Text for connection from left to right (optional).
            - 'right_to_left' (str): Text for connection from right to left (optional).
            - 'left_to_top' (str): Text for connection from left to top (optional).
            - 'right_to_top' (str): Text for connection from right to top (optional).
            - 'voiceover' (str): The voiceover text for the scene.
            - 'duration' (int): Duration to display the scene (default: 5 seconds).
        """
        self.add_background("./examples/resources/blackboard.jpg")
        
        with self.voiceover(triangle_data['voiceover']):
            # Create title if specified
            if 'title' in triangle_data:
                title = Title(triangle_data['title'])
                title.to_edge(UP)
                self.play(FadeIn(title, run_time=1))
                
            # Create the three components
            top = TextBox(triangle_data['top_text'], shadow=False)
            left = TextBox(triangle_data['left_text'], shadow=False)
            right = TextBox(triangle_data['right_text'], shadow=False)
            
            # Position components
            if 'title' in triangle_data:
                top.next_to(title, DOWN, buff=1)
            else:
                top.move_to(UP)
                
            left.next_to(top, DOWN + LEFT, buff=2)
            right.next_to(top, DOWN + RIGHT, buff=2)
            
            # Create connections based on provided data
            connections = []
            
            # Add connections that are specified in the data
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
            
            # Group all elements and apply AutoScaled
            elements = VGroup(top, left, right, *connections,metaclass=ConvertToOpenGL )
            auto_scaled_elements = AutoScaled(elements)
            
            # Animate elements in sequence
            self.play(FadeIn(top))
            
            # Create connections and components in sequence
            if connections:
                for i, conn in enumerate(connections):
                    self.play(Create(conn))
                    # After each top-to-component connection, show the component
                    if i == 0 and 'top_to_left' in triangle_data:
                        self.play(FadeIn(left))
                    elif i == 1 and 'top_to_right' in triangle_data:
                        self.play(FadeIn(right))
                    # Show the remaining components if not already shown
                    if i == len(connections) - 1:
                        remaining = []
                        if 'top_to_left' not in triangle_data and left not in self.mobjects:
                            remaining.append(left)
                        if 'top_to_right' not in triangle_data and right not in self.mobjects:
                            remaining.append(right)
                        if remaining:
                            self.play(*[FadeIn(mob) for mob in remaining])
            else:
                # If no connections, just show the components
                self.play(FadeIn(left), FadeIn(right))
            
            # Wait for specified duration
            self.wait(triangle_data.get('duration', 5))
        
        # Clear the scene
        self.clear()

    def create_data_processing_flow(self, flow_data):
        """
        Creates a data processing flow animation based on the provided configuration.

        Parameters:
        flow_data (dict): A dictionary containing the flow configuration.
            - 'blocks' (list): List of blocks with 'type', 'text', 'color', and 'voiceover'.
            - 'narration' (dict): Narration for the conclusion.
        """
        # Load color mapping
        color_map = {
            "green": GREEN,
            "red": RED,
            "blue": BLUE,
            "purple": PURPLE
        }

        self.add_background("./examples/resources/blackboard.jpg")

        # Prepare block groups
        blocks = []
        for block_config in flow_data['blocks']:
            # Create block
            block = Rectangle(width=2, height=1, color=color_map[block_config['color']], fill_opacity=0.3)
            
            # Create text with a consistent color (white) and ensure it fits within the block
            block_text = Text(block_config['text'], font_size=20, color=WHITE)
            margin = 0.2  # Margin from the walls of the box
            while block_text.width > block.width - margin or block_text.height > block.height - margin:
                block_text.scale(0.9)  # Scale down the text until it fits
            
            # Add a semi-transparent background rectangle behind the text
            text_background = Rectangle(
                width=block_text.width + 0.2,
                height=block_text.height + 0.2,
                color=BLACK,
                fill_opacity=0.5,
                stroke_opacity=0
            )
            text_background.move_to(block_text.get_center())
            
            # Group the text and its background
            text_group = VGroup(text_background, block_text)
            text_group.move_to(block.get_center())
            
            # Create group
            block_group = VGroup(block, text_group)
            blocks.append((block_group, block_config))

        # Positioning blocks
        blocks[0][0].shift(LEFT*3 + UP*1.5)  # Input 1
        blocks[1][0].shift(LEFT*3 + DOWN*1.5)  # Input 2
        blocks[2][0].shift(ORIGIN)  # Processor
        blocks[3][0].shift(RIGHT*3)  # Output

        # Create arrows
        arrows = [
            Line(blocks[0][0].get_right(), blocks[2][0].get_left(), color=GREEN, tip_length=0.1).add_tip(),
            Line(blocks[1][0].get_right(), blocks[2][0].get_left(), color=RED, tip_length=0.1).add_tip(),
            Line(blocks[2][0].get_right(), blocks[3][0].get_left(), color=PURPLE, tip_length=0.1).add_tip()
        ]

        # Animation sequence
        for block, block_config in blocks:
            with self.voiceover(text=block_config['voiceover']):
                if block_config['type'] in ['input1', 'input2']:
                    self.play(FadeIn(block))
                elif block_config['type'] == 'processor':
                    # Create connections for processor
                    self.play(
                        Create(arrows[0]),
                        Create(arrows[1]),
                        FadeIn(block)
                    )
                elif block_config['type'] == 'output':
                    # Final output with last arrow
                    self.play(
                        Create(arrows[2]),
                        FadeIn(block)
                    )

        # Conclusion
        with self.voiceover(text=flow_data['narration']['conclusion']):
            self.wait(1)

        # Cleanup
        self.play(
            *[FadeOut(block) for block, _ in blocks],
            *[FadeOut(arrow) for arrow in arrows]
        )


    def create_timeline_scene(self, timeline_data):
        """
        Creates a timeline animation scene with events, images, and narration.
        
        Parameters:
        timeline_data (dict): A dictionary containing the timeline scene data.
            - 'title' (str): Title for the timeline (optional).
            - 'events' (list): List of events, each with:
                - 'year' (str/int): Year or time marker for the event.
                - 'text' (str): Short description of the event.
                - 'narration' (str): Voiceover text for the event.
                - 'image_description' (str): Search term for wikimedia image (optional).
            - 'conclusion' (dict): Conclusion data with:
                - 'narration' (str): Narration text for the conclusion.
            - 'background_image' (str): Path to background image (optional).
        """
        # Use specified background or default
        background_image_path = timeline_data.get('background_image', 
                                                "./examples/resources/blackboard.jpg")
        background = OpenGLImageMobject(background_image_path)
        background.scale_to_fit_width(config.frame_width * 3)
        background.scale_to_fit_height(config.frame_height * 3)
        background.move_to(ORIGIN)
        self.add(background)
        
        # Reuse headers from TimelineAnimation for API requests
        self.headers = {
            'User-Agent': 'TimelineAnimation/1.0 (https://example.com; contact@example.com)'
        }
        
        # Set up timeline
        events = [(event['year'], event['text'], event['narration'], event.get('image_description', '')) 
                for event in timeline_data['events']]
        
        num_events = len(events)
        timeline = Line(LEFT * 7, RIGHT * 7, color=WHITE)
        timeline_group = Group(timeline)
        
        # Create elements containers
        dots = Group()
        year_labels = Group()
        event_texts = Group()
        images = Group()
        
        # Pre-calculate positions
        positions = [timeline.point_from_proportion(i/(num_events-1)) for i in range(num_events)]
        
        # Add title if specified
        if 'title' in timeline_data:
            title = Title(timeline_data['title'])
            title.to_edge(UP, buff=0.5)
            self.play(FadeIn(title))
        
        for i, (year, text, _, image_desc) in enumerate(events):
            # Create timeline elements
            dot = Dot(color=BLUE).move_to(positions[i])
            year_label = Text(str(year), font_size=20).next_to(dot, UP, buff=0.15)
            
            # Format text with line breaks
            words = text.split()
            lines = [" ".join(words[i:i+3]) for i in range(0, len(words), 3)]
            event_text = Text("\n".join(lines), font_size=16, line_spacing=0.8)
            event_text.next_to(dot, DOWN, buff=0.25 + (0.1 * len(lines)))
            
            # Image handling with standardized sizing
            image_mob = self.create_missing_placeholder()
            if image_desc:
                image_path = self.get_wikimedia_image(image_desc)
                if image_path and os.path.exists(image_path):
                    try:
                        img = OpenGLImageMobject(image_path)
                        img = self.scale_image(img)
                        img.next_to(year_label, UP, buff=0.25)
                        # Add background rectangle
                        bg = BackgroundRectangle(img, fill_opacity=0.6, buff=0.1)
                        image_mob = Group(bg, img)
                    except Exception as e:
                        print(f"Error loading image: {e}")
                        image_mob = self.create_error_placeholder()
            
            images.add(image_mob)
            dots.add(dot)
            year_labels.add(year_label)
            event_texts.add(event_text)
        
        # Add all elements to timeline group
        timeline_group.add(dots, year_labels, event_texts, images)
        timeline_group.center()
        
        # Animation sequence
        self.play(Create(timeline))
        self.wait(0.5)
        
        # Set up camera for MovingCameraScene functionality
        self.camera.frame.scale(1.2)
        
        for i in range(num_events):
            with self.voiceover(text=events[i][2]) as tracker:
                # Animate elements with adjusted timing
                self.play(
                    FadeIn(dots[i]),
                    FadeIn(year_labels[i]),
                    FadeIn(event_texts[i]),
                    FadeIn(images[i]),
                    self.camera.frame.animate.move_to(dots[i]).scale(0.5),
                    run_time=tracker.duration * 0.4
                )
                # Hold position for clearer view
                self.wait(tracker.duration * 0.2)
                # Smooth return to timeline view
                self.play(
                    self.camera.frame.animate.move_to(ORIGIN).scale(1/0.5),
                    run_time=tracker.duration * 0.4
                )
        
        # Conclusion if provided
        if 'conclusion' in timeline_data and 'narration' in timeline_data['conclusion']:
            conclusion_text = Text(timeline_data['conclusion']['narration'], font_size=24)
            with self.voiceover(text=timeline_data['conclusion']['narration']):
                self.play(FadeOut(timeline_group))
                self.play(Write(conclusion_text))
                self.wait(1)
                self.play(FadeOut(conclusion_text))
        
        # Clear the scene
        self.clear()
    
    def create_error_placeholder(self):
        error_mob = Rectangle(width=1.5, height=1, color=RED)
        error_text = Text("Image Error", font_size=14).move_to(error_mob.get_center())
        return Group(error_mob, error_text)

    def create_missing_placeholder(self):
        missing_mob = Rectangle(width=1.5, height=1, color=BLUE_E)
        missing_text = Text("No Image", font_size=14).move_to(missing_mob.get_center())
        return Group(missing_mob, missing_text)

    def scale_image(self, img_mob, max_width=2.5, max_height=1.8):
        """Scale image proportionally to fit within max dimensions"""
        width = img_mob.width
        height = img_mob.height
        
        # Calculate scale factors
        width_scale = max_width / width
        height_scale = max_height / height
        
        # Use the smaller scale factor to maintain aspect ratio
        scale_factor = min(width_scale, height_scale)
        return img_mob.scale(scale_factor * 0.9)  # 10% margin
    
        # Helper methods needed for the timeline scene
    def get_wikimedia_image(self, search_term, save_dir="./downloaded_images"):
        """
        Fetch image from Wikimedia with proper User-Agent, debugging, validation, and saving to a directory.

        Parameters:
        - search_term (str): The term to search for on Wikimedia.
        - save_dir (str): The directory where images will be saved.

        Returns:
        - str: The file path of the saved image, or None if no valid image is found.
        """
        print(f"Searching Wikimedia for: {search_term}")
        
        # Ensure the save directory exists
        os.makedirs(save_dir, exist_ok=True)

        try:
            # Search for articles
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
            data = response.json()
            print(f"Search response: {data}")  # Debugging

            if "query" in data and data["query"]["search"]:
                article_title = data["query"]["search"][0]["title"]
                print(f"Found article: {article_title}")
                
                # Get images from the article
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
                img_data = img_response.json()
                print(f"Image data: {img_data}")  # Debugging
                
                pages = img_data["query"]["pages"]
                page_id = list(pages.keys())[0]
                
                if "images" in pages[page_id]:
                    image_titles = [
                        img["title"] for img in pages[page_id]["images"]
                        if not img["title"].lower().endswith(".svg") 
                        and "logo" not in img["title"].lower()
                        and "icon" not in img["title"].lower()
                    ]
                    print(f"Filtered image titles: {image_titles}")  # Debugging
                    
                    if image_titles:
                        # Get the URL of the first image
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
                        img_info_data = img_info_response.json()
                        print(f"Image info data: {img_info_data}")  # Debugging
                        
                        img_info_pages = img_info_data["query"]["pages"]
                        img_info_id = list(img_info_pages.keys())[0]
                        
                        if "imageinfo" in img_info_pages[img_info_id]:
                            img_url = img_info_pages[img_info_id]["imageinfo"][0]["url"]
                            print(f"Found image URL: {img_url}")
                            
                            try:
                                # Download the image
                                img_response = requests.get(img_url, headers=self.headers)
                                img_response.raise_for_status()  # Ensure the request was successful
                                
                                # Validate content type
                                if "image" not in img_response.headers.get("Content-Type", ""):
                                    print(f"Invalid content type for URL: {img_url}")
                                    return None
                                
                                # Save the image to the specified directory
                                file_name = os.path.basename(img_url)
                                save_path = os.path.join(save_dir, file_name)
                                with open(save_path, "wb") as img_file:
                                    img_file.write(img_response.content)
                                
                                # Validate the image using PIL
                                try:
                                    with Image.open(save_path) as img:
                                        img.verify()  # Verify the image is valid
                                    print(f"Image saved and validated: {save_path}")
                                    return save_path
                                except Exception as e:
                                    print(f"Invalid image file: {save_path}, error: {e}")
                                    os.unlink(save_path)  # Remove invalid file
                                    return None
                            
                            except Exception as img_err:
                                print(f"Error downloading or processing image: {img_err}")
                                return None
            
            print(f"No image found for: {search_term}")
            return None
        
        except Exception as e:
            print(f"Error in get_wikimedia_image: {str(e)}")
            return None

    # Modify the construct method to include the new scene type
    def construct(self):
        self.set_speech_service(GTTSService())
        #self.set_speech_service(AzureService(voice="en-AU-NatashaNeural",style="newscast-casual",))

        # Add background music if specified
        background_music_path = self.all_content.get('background_music')
        if background_music_path:
            self.add_background_music(background_music_path)

        # Process each scene in sequence
        for scene in self.all_content['scenes']:
            scene_type = scene['type']
            
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
            
        # Add final goodbye scene
        self.goodbye()

def generate_video(json_path):
    with open(json_path, 'r') as f:
        content = json.load(f)
  
    scene = ComprehensiveVideoGenerator(content)
    scene.add_background("./examples/resources/blackboard.jpg") 
    scene.render()

if __name__ == "__main__":
    # Example usage with the JSON file
    generate_video('video_config.json')



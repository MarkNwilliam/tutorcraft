import json
import tempfile
import os
from manim import Create, Scene, ORIGIN, Text, FadeIn, FadeOut, DOWN, UP, LEFT, RIGHT, LARGE_BUFF, MED_LARGE_BUFF, linear
from manim_voiceover import VoiceoverScene
from code_video import CodeScene, AutoScaled, SequenceDiagram, TextBox, Connection
from manim_voiceover.services.gtts import GTTSService
from code_video.widgets import DEFAULT_FONT
from manim.mobject.types.image_mobject import ImageMobject  # Import ImageMobject
from voiceover_sequence_diagram_scene import VoiceoverSequenceDiagramScene
from manim import * 
from manim_voiceover.services.azure import AzureService
from manim.opengl import *

class ComprehensiveVideoGenerator(CodeScene, VoiceoverSequenceDiagramScene):
    def __init__(self, content=None):
        super().__init__()
        if content is None:
            content = self.load_default_content()
        self.all_content = content

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
            self.wait(title_data.get('duration', 3))
        
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
        
        # Add voiceover for the overview
        with self.voiceover(overview_data['voiceover']):
            # Create and display the main overview text
            title = Text(
                overview_data['text'],
                font=overview_data.get('font', 'Helvetica'),
                line_spacing=0.5,
            ).scale(0.7)
            self.play(Create(title, run_time=overview_data.get('creation_time', 10), rate_func=linear))
            self.wait(overview_data.get('duration', 3))
            
            # Create and display the subtitle if specified
            if 'subtitle' in overview_data:
                subtitle = Text(overview_data['subtitle'], font=overview_data.get('font', 'Helvetica'))
                subtitle.scale(0.7)
                subtitle.next_to(title, direction=DOWN, buff=MED_LARGE_BUFF, aligned_edge=LEFT)
                self.play(Create(subtitle))
                self.wait(overview_data.get('subtitle_duration', 2))
        
        # Clear the scene
        self.clear()

    def create_code_scene(self, code_data):
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
                    self.wait(2)

            with self.voiceover(code_data['conclusion']['text']):
                self.highlight_none(tex)
                self.wait(2)

        finally:
            os.unlink(temp_path)

    def create_sequence_diagram(self, sequence_data):
        print("here is the sequence data", sequence_data)   
        background_path = sequence_data.get('background')
        if background_path:
            self.add_background(background_path)

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
        self.wait(3)
        self.clear()

    def goodbye(scene: CodeScene):
        # Keeping original conclusion exactly as is
        logo_path = "/Users/mac/code-video-generator/yeefm logo.png"
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

    def construct(self):
        #self.set_speech_service(GTTSService())
        self.set_speech_service(AzureService(voice="en-AU-NatashaNeural",style="newscast-casual",))

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
            
            # Add transition between scenes if not the last scene
            if scene != self.all_content['scenes'][-1]:
                with self.voiceover(scene.get('transition_text', 'Moving on.')):
                    self.clear()
                    self.wait(0.5)

        # Add final goodbye scene
        self.goodbye()

def generate_video(json_path):
    with open(json_path, 'r') as f:
        content = json.load(f)
    
    scene = ComprehensiveVideoGenerator(content)
    scene.render()

if __name__ == "__main__":
    # Example usage with the JSON file
    generate_video('video_config.json')
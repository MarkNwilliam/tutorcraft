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
from flowchartwithanime import JsonToFlowchartVertical
from manim.opengl import *

class ComprehensiveVideoGenerator(CodeScene, VoiceoverSequenceDiagramScene):
    def __init__(self, content=None):
        super().__init__()
        if content is None:
            content = self.load_default_content()
        self.all_content = content

    def load_default_content(self):
        # Load default content from a JSON file or define it here
        with open('pyramidwithtimeline.json', 'r') as f:
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
    
    def create_pyramid_scene(self, pyramid_data):
        """
        Creates a pyramid scene based on the provided data.
        
        Parameters:
        pyramid_data (dict): A dictionary containing the pyramid scene data.
            - 'title' (str): The title of the pyramid scene.
            - 'voiceover' (str): The voiceover text for the pyramid scene.
            - 'boxes' (list): List of dictionaries containing box messages.
            - 'connections' (list): List of dictionaries containing connection data.
        """
        # Create the components based on the provided box messages
        top = TextBox(pyramid_data['boxes'][0]['message'], shadow=False)
        worker1 = TextBox(pyramid_data['boxes'][1]['message'], shadow=False)
        worker2 = TextBox(pyramid_data['boxes'][2]['message'], shadow=False)

        # Position with top in middle and workers on sides below
        top.move_to(UP)  # This puts it in the middle and slightly up
        worker1.next_to(top, DOWN + LEFT, buff=2)
        worker2.next_to(top, DOWN + RIGHT, buff=2)

        # Create connections from top to workers based on the provided connection data
        conn1 = Connection(top, worker1, pyramid_data['connections'][0]['text'])
        conn2 = Connection(top, worker2, pyramid_data['connections'][1]['text'], padding=-0.7)
        conn3 = Connection(worker1, worker2, pyramid_data['connections'][2]['text'])
        conn4 = Connection(worker2, worker1, pyramid_data['connections'][3]['text'])
        conn5 = Connection(worker1, top, pyramid_data['connections'][4]['text'])
        conn6 = Connection(worker2, top, pyramid_data['connections'][5]['text'], padding=-0.6)

        # Group all elements to be auto-scaled
        elements = VGroup(top, worker1, worker2, conn1, conn2, conn3, conn4, conn5, conn6)

        # Apply AutoScaled to all elements
        auto_scaled_elements = AutoScaled(elements)

        # Add title if provided
        if 'title' in pyramid_data:
            title = Text(pyramid_data['title'], font=DEFAULT_FONT)
            title.scale(0.8)
            title.to_edge(UP)
            self.add(title)

        # Add voiceover for the pyramid scene
        with self.voiceover(pyramid_data['voiceover']):
            # Animate in sequence
            self.play(FadeIn(top))
            self.play(Create(conn1))
            self.play(FadeIn(worker1))
            self.play(Create(conn2))
            self.play(FadeIn(worker2))
            self.play(Create(conn3))
            self.play(Create(conn4))    
            self.play(Create(conn5))    
            self.play(Create(conn6))

            # Hold the final frame
            self.wait(2)
            self.clear()
    
    def create_flowchart_scene(self, flowchart_data):
        flowchart = JsonToFlowchartVertical()
        flowchart.setup()

        title = flowchart_data.get("title", "Flowchart Title")

        # Create and display the title
        title_text = Text(flowchart.wrap_text(title, max_chars_per_line=30), font_size=50).move_to(ORIGIN)
        with self.voiceover(text=f"Learn with an illustration: {title}.") as tracker:
            self.play(Write(title_text), run_time=tracker.duration)
        self.clear()

        # Add blocks
        for block in flowchart_data['blocks']:
            flowchart.to(
                name=block['name'],
                text=block['text'],
                voiceover_text=block.get('voiceover_text', None)
            )

        # Add connections
        for connection in flowchart_data['connections']:
            flowchart.connect(
                from_block=connection['from'],
                to_block=connection['to'],
                connection_type=connection['type'],
                message=connection.get('message', ''),
                direction=connection.get('direction', 'right')
            )

        # Calculate positions and create connections
        flowchart._calculate_positions()

        # Group all elements
        all_elements = VGroup(*[block["group"] for block in flowchart.blocks.values()])

        # Scale and center
        padding = 1.0
        design_height = all_elements.get_height() + 2 * padding
        design_width = all_elements.get_width() + 2 * padding

        scale_height = self.camera.frame.height / design_height
        scale_width = self.camera.frame.width / design_width
        scale_ratio = min(scale_height, scale_width)

        all_elements.scale(scale_ratio)
        all_elements.move_to(ORIGIN)

        # Show initial full view
        self.play(
            self.camera.frame.animate.scale(1.0).move_to(ORIGIN)
        )

        # Animate blocks with camera movement and voice-over
        for block_name, block_data in flowchart.blocks.items():
            block = block_data["group"]
            voiceover_text = block_data["voiceover_text"]

            # Zoom in to block
            self.play(
                self.camera.frame.animate.scale(0.5).move_to(block),
                run_time=0.8
            )

            # Add voice-over for the block's text
            if voiceover_text:
                with self.voiceover(text=voiceover_text) as tracker:
                    self.play(Create(block), run_time=tracker.duration)
            else:
                self.play(Create(block))

            # Create connections for this block
            connections = flowchart._create_connections(block_name)
            for connection in connections:
                self.play(Create(connection), run_time=0.3)

            # Zoom out to show context
            self.play(
                self.camera.frame.animate.scale(2.0).move_to(ORIGIN),
                run_time=0.8
            )

            self.wait(0.2)

        # Final zoom out to show complete diagram
        self.play(
            self.camera.frame.animate.scale(1.2).move_to(ORIGIN),
            run_time=1
        )

        self.wait(1)
        self.clear()



    def create_timeline_scene(self, timeline_data):
        """
        Creates a timeline scene based on the provided data.
        
        Parameters:
        timeline_data (dict): A dictionary containing the timeline scene data.
            - 'title' (dict): A dictionary containing the title data.
                - 'main' (str): The main title text.
                - 'subtitle' (str): The subtitle text.
                - 'narration' (str): The voiceover text for the title.
            - 'events' (list): A list of dictionaries containing event data.
                - 'year' (int): The year of the event.
                - 'text' (str): The event description.
                - 'narration' (str): The voiceover text for the event.
        """
        # Set up the camera frame
        camera_frame = self.camera.frame

        print("here is the timeline data", timeline_data)   

        events = [(event['year'], event['text'], event['narration']) 
                 for event in timeline_data['events']]
        
        # Calculate base sizes based on number of events
        num_events = len(events)
        base_font_size = max(72 / (num_events / 4), 16)
        event_font_size = max(base_font_size * 0.25, 12)
        year_font_size = max(base_font_size * 0.33, 14)
        dot_radius = max(0.1 * (10 / num_events), 0.05)
        
        # Timeline width calculation
        timeline_width = max(num_events * 1.5, 8)
        
        # Intro page with voiceover
        intro_title = Text(timeline_data['title']['main'], font_size=base_font_size, color=BLUE)
        intro_subtitle = Text(timeline_data['title']['subtitle'], font_size=base_font_size * 0.5)
        intro_subtitle.next_to(intro_title, DOWN, buff=0.5)
        intro_group = VGroup(intro_title, intro_subtitle)
        
        # Show intro with voiceover
        with self.voiceover(text=timeline_data['title']['narration']) as tracker:
            self.play(
                AddTextLetterByLetter(intro_title),
                AddTextLetterByLetter(intro_subtitle),
                run_time=3
            )
        self.wait(0.5)
        self.play(FadeOut(intro_group))

        # Create timeline
        timeline = Line(
            start=LEFT * (timeline_width/2),
            end=RIGHT * (timeline_width/2),
            color=WHITE
        )
        
        # Create visual elements
        dots = VGroup(metaclass=ConvertToOpenGL)
        year_labels = VGroup(metaclass=ConvertToOpenGL)
        event_texts = VGroup(metaclass=ConvertToOpenGL)
        
        for i, (year, text, _) in enumerate(events):
            dot = Dot(radius=dot_radius, color=BLUE)
            dot_x = timeline.point_from_proportion(i / (len(events) - 1))[0]
            dot.move_to([dot_x, 0, 0])
            dots.add(dot)
            
            year_label = Text(str(year), font_size=year_font_size)
            year_label.next_to(dot, UP, buff=0.2)
            year_labels.add(year_label)
            
            words = text.split()
            lines = [" ".join(words[i:i+2]) for i in range(0, len(words), 2)]
            
            event_text = Text("\n".join(lines), font_size=event_font_size)
            text_buffer = 0.3 + (len(lines) * 0.1)
            event_text.next_to(dot, DOWN, buff=text_buffer)
            event_texts.add(event_text)
        
        timeline_group = VGroup(timeline, dots, year_labels, event_texts)
        
        # Scale timeline
        width_scale = (config.frame_width - 1) / timeline_group.width
        height_scale = (config.frame_height - 1) / timeline_group.height
        scale_factor = min(width_scale, height_scale) * 0.9
        timeline_group.scale(scale_factor)
        
        self.play(Create(timeline))
        
        # Calculate zoom levels
        zoom_in_scale = max(0.7 - (num_events * 0.02), 0.3)
        zoom_out_scale = min(1.5 + (num_events * 0.05), 2.5)
        
        # Animate events with voiceover - Modified timing
        for i, (_, _, narration) in enumerate(events):
            # Create elements first without zoom
            self.play(
                Create(dots[i]),
                Write(year_labels[i]),
                Write(event_texts[i]),
                run_time=0.5
            )
            
            # Start voiceover and zoom in simultaneously
            with self.voiceover(text=narration) as tracker:
                # Zoom in at the start of narration
                self.play(
                    camera_frame.animate.scale(zoom_in_scale).move_to(dots[i]),
                    run_time=1
                )
                # Wait for the remaining duration of the narration
                self.wait(tracker.duration - 1)
                
                if i < len(events) - 1:
                    # Zoom out at the end of narration
                    self.play(
                        camera_frame.animate.scale(zoom_out_scale).move_to(ORIGIN),
                        run_time=1
                    )
        
        self.play(
            camera_frame.animate.scale(zoom_out_scale).move_to(ORIGIN),
            run_time=2
        )
        
        self.play(FadeOut(timeline_group))
        
        self.wait(0.5)
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
            elif scene_type == 'pyramid':
                self.create_pyramid_scene(scene)
            elif scene_type == 'timeline':
                self.create_timeline_scene(scene)
            elif scene_type == 'flowchart':
                self.create_flowchart_scene(scene)
            
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
    generate_video('pyramidwithtimeline.json')
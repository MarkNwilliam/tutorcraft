from manim import *
from collections import defaultdict
import json
from manim_voiceover.services.azure import AzureService
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService
from manim.opengl import *

class JsonToFlowchartVertical(VoiceoverScene, MovingCameraScene):
    def __init__(self):
        super().__init__()
        self.blocks = {}
        self.connections = []
        self.graph = defaultdict(list)
        self.vertical_spacing = 2.5
        self.horizontal_spacing = 3
        self.levels = {}
        self.scale_factor = 0.6

    def setup(self):
        # Save the initial state of the camera frame
        self.camera.frame.save_state()  # Save the initial state for later restoration
        self.camera.frame.scale(1.2).move_to(ORIGIN)  # Adjust the initial frame

        # Set up Azure TTS service
        #self.set_speech_service(AzureService(voice="en-AU-NatashaNeural", style="newscast-casual"))
        self.set_speech_service(GTTSService())

    def wrap_text(self, text, max_chars_per_line):
        """Wrap text into multiple lines with a maximum number of characters per line."""
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars_per_line:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return "\n".join(lines)

    def to(self, name, text, voiceover_text=None, base_width=1.2, base_height=1.2, base_font_size=20, width_scaling_factor=0.08, font_scaling_factor=0.05, max_chars_per_line=30, height_scaling_factor=0.08):
        """Create and store a named block with text inside."""
        # Calculate the width based on the text length
        text_length = len(text)
        width = base_width + text_length * width_scaling_factor
        height = width / 2

        # Calculate the font size based on the text length
        font_size = max(base_font_size - text_length * font_scaling_factor, 8)  # Ensure a minimum font size

        # Wrap the text into multiple lines
        wrapped_text = self.wrap_text(text, max_chars_per_line)

        # Create the rectangle with the calculated width
        block = Rectangle(width=width, height=height).set_stroke(width=1)
        text_obj = Text(wrapped_text, font_size=font_size).move_to(block.get_center())
        group = VGroup(block, text_obj)
        self.blocks[name] = {"group": group, "voiceover_text": voiceover_text}  # Store voiceover text with the block
        return self

    def connect(self, from_block, to_block, connection_type="straight", message="", direction="right"):
        """Create a connection between blocks and store in graph."""
        self.graph[from_block].append((to_block, connection_type, message, direction))
        return self

    def _calculate_positions(self):
        """Calculate positions for all blocks based on connections."""
        # Find root nodes (nodes with no incoming edges)
        incoming_edges = set()
        for from_block in self.graph:
            for to_block, _, _, _ in self.graph[from_block]:
                incoming_edges.add(to_block)
        
        root_nodes = set(self.blocks.keys()) - incoming_edges
        if not root_nodes:
            root_nodes = {list(self.blocks.keys())[0]}  # Take first block if no clear root

        # Initialize vertical position
        y_position = 3  # Start from top (y=3)
        
        # Position blocks vertically, one after the other
        for block_name in self.blocks:
            # Calculate the x position (set to 0 since we're only focusing on vertical arrangement)
            x_position = 0
            
            # Set the block's position
            self.blocks[block_name]["group"].move_to([x_position, y_position, 0])
            
            # Move the vertical position down for the next block
            y_position -= self.vertical_spacing

                

    def _create_connections(self, from_block):
        """Create connections for a specific block."""
        connections = []
        for to_block, conn_type, message, direction in self.graph[from_block]:
            if conn_type == "straight":
                connection = self._create_straight_arrow(
                    self.blocks[from_block]["group"].get_bottom(),
                    self.blocks[to_block]["group"].get_top()
                )
            elif conn_type == "self":
                connection = self._create_self_arrow(
                    self.blocks[from_block]["group"],
                    message=message
                )
            elif conn_type == "jump":
                connection = self._create_jump_arrow(
                    self.blocks[from_block]["group"],
                    self.blocks[to_block]["group"],
                    message=message,
                    direction=direction
                )
            connections.append(connection)
        return connections

    def _create_straight_arrow(self, start, end, tip_length=0.2):
        """Create a straight arrow connecting two points."""
        return Line(start=start, end=end, tip_length=tip_length).set_stroke(width=1).add_tip()

    def _create_self_arrow(self, block, message="Loop", spacing=0.4, distance=0.8):
        """Create a self-referencing arrow for a block."""
        center_x = block.get_right()[0]
        center_y = block.get_right()[1]

        line = Polygon(
            [center_x, center_y + spacing, 0],
            [center_x + distance, center_y + spacing, 0],
            [center_x + distance, center_y - spacing, 0],
            [center_x + distance / 2, center_y - spacing, 0],
            [center_x + distance, center_y - spacing, 0],
            [center_x + distance, center_y + spacing, 0],
            [center_x, center_y + spacing, 0],
            color=WHITE,
        ).set_stroke(width=1)

        arrow = Arrow(
            start=[center_x + distance, center_y - spacing, 0],
            end=[center_x, center_y - spacing, 0],
            buff=0,
            stroke_width=2,
        )

        label = Text(message, font_size=50, slant=ITALIC)
        label.scale(0.5)
        label.next_to(line, RIGHT)

        return VGroup(line, arrow, label)

    def _create_jump_arrow(self, block1, block2, message="Loop", spacing=0.4, distance=0.8, direction="right"):
        """Create a jumping arrow between two blocks."""
        if direction == "right":
            block1_x = block1.get_right()[0]
            block1_y = block1.get_right()[1]
            block2_x = block2.get_right()[0]
            block2_y = block2.get_right()[1]

            vertices = [
                [block1_x, block1_y, 0],
                [block1_x + distance, block1_y, 0],
                [block1_x + distance, block2_y, 0],
                [block2_x, block2_y, 0],
            ]

            label_position = RIGHT
        else:
            block1_x = block1.get_left()[0]
            block1_y = block1.get_left()[1]
            block2_x = block2.get_left()[0]
            block2_y = block2.get_left()[1]

            vertices = [
                [block1_x, block1_y, 0],
                [block1_x - distance, block1_y, 0],
                [block1_x - distance, block2_y, 0],
                [block2_x, block2_y, 0],
            ]

            label_position = LEFT

        bentline = VMobject()
        bentline.set_points_as_corners([*vertices])
        bentline.set_color(WHITE)
        bentline.set_stroke(width=1)

        arrow = Arrow(
            start=vertices[2],
            end=vertices[-1],
            buff=0,
            color=WHITE
        )

        label = Text(message, font_size=50, slant=ITALIC)
        label.scale(0.5)
        label.next_to(bentline, label_position)

        return VGroup(bentline, arrow, label, )

    def load_json(self, json_data):
        """Load blocks and connections from JSON data."""
        data = json.loads(json_data)
        for block in data["blocks"]:
            self.to(block["name"], block["text"], block.get("voiceover_text", block["text"]))  # Use voiceover_text if provided, else use block text
        for connection in data["connections"]:
            self.connect(
                connection["from"],
                connection["to"],
                connection["type"],
                connection.get("message", ""),
                connection.get("direction", "right")
            )

    def construct(self):
        # Corrected JSON data
        json_data = '''
{
    "title": "How Companies Hire Employees: The Step-by-Step Hiring Process",
    "blocks": [
        {
            "name": "job_opening",
            "text": "Job Opening Identified",
            "voiceover_text": "The hiring process starts when a company identifies a need for a new employee. According to LinkedIn, 70% of jobs are never publicly posted but filled through networking."
        },
        {
            "name": "job_posting",
            "text": "Job Posting & Sourcing",
            "voiceover_text": "The HR team creates a job description and posts it on platforms like LinkedIn, Indeed, and company career pages. Research shows that 60% of job seekers apply within the first week of a job posting."
        },
        {
            "name": "resume_screening",
            "text": "Resume Screening",
            "voiceover_text": "HR uses AI tools or manual review to filter applicants. On average, recruiters spend only 7.4 seconds reviewing a resume."
        },
        {
            "name": "initial_interview",
            "text": "Initial Screening Interview",
            "voiceover_text": "HR conducts a short interview to assess basic qualifications and cultural fit. 85% of recruiters say cultural fit is crucial when making a hiring decision."
        },
        {
            "name": "technical_test",
            "text": "Technical/Skill Assessment",
            "voiceover_text": "Candidates may take skill-based tests, coding challenges, or case studies. 76% of hiring managers say skill-based hiring reduces bias and improves candidate quality."
        },
        {
            "name": "final_interview",
            "text": "Final Interview with Hiring Manager",
            "voiceover_text": "Candidates meet the hiring manager and team. The final interview typically includes behavioral questions and scenario-based assessments."
        },
        {
            "name": "job_offer",
            "text": "Job Offer & Negotiation",
            "voiceover_text": "If the candidate is successful, HR extends an offer. 52% of candidates negotiate salary before accepting an offer."
        },
        {
            "name": "background_check",
            "text": "Background Check & References",
            "voiceover_text": "Companies verify employment history, references, and conduct background checks. 1 in 3 applicants provides misleading information on their resume."
        },
        {
            "name": "onboarding",
            "text": "Employee Onboarding",
            "voiceover_text": "New hires complete paperwork, get training, and integrate into the team. Companies with strong onboarding programs improve employee retention by 82%."
        },
        {
            "name": "probation_period",
            "text": "Probation & Performance Review",
            "voiceover_text": "Most employees have a probation period of 3-6 months, during which their performance is evaluated before full employment confirmation."
        }
    ],
    "connections": [
        {"from": "job_opening", "to": "job_posting", "type": "straight"},
        {"from": "job_posting", "to": "resume_screening", "type": "straight"},
        {"from": "resume_screening", "to": "initial_interview", "type": "straight"},
        {"from": "initial_interview", "to": "technical_test", "type": "straight"},
        {"from": "technical_test", "to": "final_interview", "type": "straight"},
        {"from": "final_interview", "to": "job_offer", "type": "straight"},
        {"from": "job_offer", "to": "background_check", "type": "straight"},
        {"from": "background_check", "to": "onboarding", "type": "straight"},
        {"from": "onboarding", "to": "probation_period", "type": "straight"},
        
        {"from": "resume_screening", "to": "job_posting", "type": "jump", "message": "No suitable candidates, repost job", "direction": "left"},
        {"from": "initial_interview", "to": "resume_screening", "type": "jump", "message": "Candidate rejected, select another", "direction": "left"},
        {"from": "technical_test", "to": "initial_interview", "type": "jump", "message": "Retake test or reconsider candidate", "direction": "left"},
        {"from": "final_interview", "to": "technical_test", "type": "jump", "message": "Candidate needs further assessment", "direction": "left"},
        {"from": "job_offer", "to": "final_interview", "type": "jump", "message": "Candidate declines, select next best", "direction": "left"},
        {"from": "background_check", "to": "job_offer", "type": "jump", "message": "Failed verification, reconsider offer", "direction": "right"},
        {"from": "probation_period", "to": "onboarding", "type": "jump", "message": "Performance issues, retrain or reassign", "direction": "right"}
    ]
}


        '''

        # Load JSON data
        data = json.loads(json_data)
        title = data.get("title", "Flowchart Title")  # Get the title from JSON, default to "Flowchart Title"

        # Create and display the title
        title_text = Text(self.wrap_text(title, max_chars_per_line=30), font_size=50).move_to(ORIGIN)
        with self.voiceover(text=f"learn with an illustration {title}.") as tracker:
            self.play(Write(title_text), run_time=tracker.duration)
        #self.wait(1)

        self.clear()

        # Load JSON data
        self.load_json(json_data)
        self._calculate_positions()

        # Group all elements
        all_elements = Group(*[block["group"] for block in self.blocks.values()], *self.connections)

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
            self.camera.frame.animate.scale(1.0).move_to(ORIGIN)  # Changed from 1.2 to 1.0
        )
        # self.wait(0.1)

        # Animate blocks with camera movement and voice-over
        for block_name, block_data in self.blocks.items():
            block = block_data["group"]
            voiceover_text = block_data["voiceover_text"]

            # Zoom in to block
            self.play(
                self.camera.frame.animate.scale(0.5).move_to(block),  # Changed from 0.3 to 0.5
                run_time=0.8
            )
            
            # Add voice-over for the block's text
            with self.voiceover(text=voiceover_text) as tracker:
                # Create block
                self.play(Create(block), run_time=tracker.duration)
            
            # Create connections for this block
            connections = self._create_connections(block_name)
            for connection in connections:
                self.play(Create(connection), run_time=0.3)
            
            # Zoom out to show context
            self.play(
                self.camera.frame.animate.scale(2.0).move_to(ORIGIN),  # Changed from 3.5 to 2.0
                run_time=0.8
            )
            
            self.wait(0.2)

        # Final zoom out to show complete diagram
        self.play(
            self.camera.frame.animate.scale(1.2).move_to(ORIGIN),  # Changed from 1.0 to 1.2
            run_time=1
        )
        
        self.wait(1)

        self.clear()

        logo_path = "/Users/mac/texttoeducationalvideos/yeefm logo.png"
        logo = OpenGLImageMobject(logo_path).scale(0.5)
        
        # Create the text
        text = Text("Download YeeFM and Subscribe", font_size=40)
        
        # Arrange the logo and text
        logo.next_to(text, UP, buff=0.5)
        
        # Group them together using Group instead of VGroup
        group = Group(logo, text).move_to(ORIGIN)

        with self.voiceover(text="Download YeeFM and Subscribe") as tracker:
            self.play(FadeIn(logo), FadeIn(text), run_time=tracker.duration)
            
        self.wait(2)
        self.play(*[FadeOut(mob) for mob in self.mobjects])
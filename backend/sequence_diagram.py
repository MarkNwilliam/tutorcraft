from importlib.metadata import PackageNotFoundError
from importlib.metadata import version
from os.path import dirname
from manim import *
from manim.animation.creation import Create
from voiceover_sequence_diagram_scene import VoiceoverSequenceDiagramScene
from code_video import AutoScaled, CodeScene, Connection, SequenceDiagram, TextBox
from code_video.widgets import DEFAULT_FONT
import json
from manim.opengl import *

def load_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)

def title_scene(scene: CodeScene, config):
    # Add background
    if config.get("background_image"):
        scene.add_background(config["background_image"])
    
    # Create title text
    title = AutoScaled(Text(config["title"]["text"], font="Helvetica"))
    
    # Create version text
    subtitle_text = (
        Text(config["title"]["subtitle"], font="Helvetica")
        .scale(0.6)
        .next_to(title, direction=DOWN, buff=LARGE_BUFF)
    )

    # Animate title with voiceover
    with scene.voiceover(config["title"]["voiceover"]) as tracker:
        scene.play(Create(title, run_time=2))
        scene.play(FadeIn(subtitle_text, run_time=2))

    #scene.wait(1)
    scene.clear()

def overview(scene: CodeScene, config):
    if "overview" not in config:
        return
        
    text = AutoScaled(Text(
        config["overview"]["text"],
        font="Helvetica",
        line_spacing=0.5,
    ).scale(0.7))

    with scene.voiceover(config["overview"]["voiceover"]) as tracker:
        scene.play(
            Create(text, run_time=tracker.duration, rate_func=linear)
        )

    scene.wait(0.4)
    scene.clear()

def demo_sequence(scene: CodeScene, config):
    diagram = AutoScaled(SequenceDiagram())

    # Add all actors first
    actors = {}
    actor_names = config["sequence_diagram"]["actors"]
    actor_objects = diagram.add_objects(*actor_names)
    
    # Map actor names to their objects
    for name, obj in zip(actor_names, actor_objects):
        actors[name] = obj

    # Process each interaction from the JSON
    for interaction in config["sequence_diagram"]["interactions"]:
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
    title = Text(config["sequence_diagram"]["title"], font=DEFAULT_FONT)
    title.scale(0.8)
    title.to_edge(UP)

    scene.add(title)
    diagram.next_to(title, DOWN)
    scene.play(Create(diagram))

    scene.create_diagram_with_voiceover(diagram)
    scene.wait(3)
    scene.clear()

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

class Main(CodeScene, VoiceoverSequenceDiagramScene):
    def construct(self):
        config = load_config('sequence_diagram.json')
        
        if config.get("background_music"):
            self.add_background_music(config["background_music"])
            
        title_scene(self, config)
        overview(self, config)
        if config.get("background_image"):
            self.add_background(config["background_image"])
        demo_sequence(self, config)
        goodbye(self)

if __name__ == "__main__":
    Main().construct()
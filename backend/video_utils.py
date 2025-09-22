import os
import shutil
import tempfile
from manim import *
from manim import config
from manim.mobject.types.image_mobject import ImageMobject
from PIL import Image
import numpy as np
from manim.opengl import *


class VideoUtils:
    """Utility methods for video generation"""
    
    def add_background(self, path):
        """Add a background image to the scene"""
        try:
            background = OpenGLImageMobject(path)
            self.add(background)
        except OSError as e:
            print(f"Error loading background image: {e}")

    def wrap_text(self, text, max_chars_per_line):
        """Return wrapped text as a string with newlines"""
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

    def format_code(self, code_text):
        """
        Format code by properly breaking it into lines and handling escape sequences
        """
        if isinstance(code_text, str):
            code_text = code_text.replace('\\n', '\n')
        
        lines = code_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.rstrip()
            if not line:
                formatted_lines.append('')
                continue
                
            if line.strip().startswith('#'):
                formatted_lines.append(line)
                continue
            
            if any(cmd in line.lower() for cmd in ['pip', 'wget', 'unzip', 'tar', 'selenium-driver']):
                formatted_lines.append(line)
                continue
                
            formatted_lines.append(line)
                    
        final_lines = []
        for i, line in enumerate(formatted_lines):
            if (line.strip().startswith('#') and 
                i > 0 and 
                not formatted_lines[i-1].strip().startswith('#') and 
                formatted_lines[i-1].strip()):
                final_lines.append('')
                
            final_lines.append(line)
            
            if any(cmd in line.lower() for cmd in ['pip install', 'wget', 'unzip', 'tar']):
                final_lines.append('')
                    
        return '\n'.join(final_lines)

    def generate_video_from_json(self, json_content):
        """Generate video from JSON with dynamic scene naming"""
        output_name = json_content.get('output_name', 'GeneratedVideo')
        print(f"Generating video with output name: {output_name}")

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
        scene.add_background("./examples/resources/blackboard.jpg") 
        scene.render()

        self.cleanup_temp_files(output_name)

    def cleanup_temp_files(self, output_name):
        """Clean up temporary files after rendering"""
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

    def handle_transition(self, scene):
        """Handle scene transitions"""
        try:
            with self.voiceover(scene.get('transition_text', 'Moving on.')):
                self.clear()
                self.wait(0.5)
        except Exception as e:
            print(f"Error with transition: {e}")
        
        self.clear()
        self.wait(0.5)
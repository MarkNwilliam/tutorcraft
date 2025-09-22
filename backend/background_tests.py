from manim import *

class BackgroundColorTest(Scene):
    def construct(self):
        # Set the background color to match your image
        config.background_color = "#f7f5f3"
        
        # Create a simple "Hello World" text
        hello_text = Text("Hello World!", font_size=48, color=BLACK)
        
        # Add some colored elements to see contrast
        circle = Circle(radius=1, color=BLUE, fill_opacity=0.5)
        circle.shift(UP * 2)
        
        rectangle = Rectangle(width=3, height=1, color=RED, fill_opacity=0.3)
        rectangle.shift(DOWN * 2)
        
        # Simple animations
        self.play(Write(hello_text))
        self.wait(1)
        self.play(FadeIn(circle))
        self.wait(1)
        self.play(FadeIn(rectangle))
        self.wait(2)

# To run this, save as test_background.py and run:
# manim test_background.py BackgroundColorTest
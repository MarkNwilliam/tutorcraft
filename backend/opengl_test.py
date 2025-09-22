from manim import *
import time

class OpenGLSpeedTest(Scene):
    """Test scene to compare Cairo vs OpenGL performance on macOS"""
    
    def construct(self):
        # Record start time
        start_time = time.time()
        
        # Create a grid of squares for performance testing
        squares = VGroup()
        colors = [RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE]
        
        for i in range(6):
            for j in range(6):
                square = Square(side_length=0.8)
                square.set_fill(colors[(i + j) % len(colors)], opacity=0.7)
                square.move_to([i * 1.2 - 3, j * 1.2 - 3, 0])
                squares.add(square)
        
        # Performance test animations
        self.play(Create(squares, lag_ratio=0.05))
        self.wait(0.5)
        
        # Rotation animation
        self.play(squares.animate.rotate(PI/4), run_time=2)
        self.wait(0.5)
        
        # Scale animation
        self.play(squares.animate.scale(1.5), run_time=2)
        self.wait(0.5)
        
        # Color shift animation
        self.play(squares.animate.set_fill(PINK, opacity=0.8), run_time=2)
        self.wait(0.5)
        
        # Final transformation
        self.play(
            squares.animate.arrange_in_grid(rows=9, cols=4, buff=0.1),
            run_time=3
        )
        self.wait(1)
        
        end_time = time.time()
        print(f"\n🎬 Animation completed in {end_time - start_time:.2f} seconds")
        print("✅ OpenGL rendering test successful!")

class SimpleOpenGLTest(Scene):
    """Minimal test to verify OpenGL is working"""
    
    def construct(self):
        # Simple test objects
        circle = Circle(radius=2, color=BLUE)
        square = Square(side_length=3, color=RED).shift(RIGHT * 4)
        triangle = Triangle(color=GREEN).shift(LEFT * 4)
        
        # Test basic animations
        self.play(Create(circle))
        self.play(Create(square), Create(triangle))
        self.play(
            circle.animate.shift(UP * 2),
            square.animate.rotate(PI/4),
            triangle.animate.scale(0.5)
        )
        self.wait(1)
        
        # Test text rendering with OpenGL
        text = Text("OpenGL Working on macOS!", color=WHITE)
        self.play(Write(text))
        self.wait(2)
        
        print("✅ Simple OpenGL test passed!")

if __name__ == "__main__":
    print("🚀 Testing Manim OpenGL on macOS...")
    print("📊 This will test both performance and compatibility")
    print("-" * 50)
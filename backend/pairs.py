from manim import DOWN, FadeIn, LEFT, RIGHT, Scene, UP, VGroup
from manim.animation.creation import Create
from code_video import Connection, TextBox
from code_video import AutoScaled

class ContrastingPairsScene(Scene):
    def construct(self):
        # Level 1 - Education
        high1 = TextBox("HIGH", shadow=False)
        low1 = TextBox("LOW", shadow=False)

        # Level 2 - Innovation
        high2 = TextBox("HIGH", shadow=False)
        low2 = TextBox("LOW", shadow=False)

        # Level 3 - You can customize this label
        high3 = TextBox("HIGH", shadow=False)
        low3 = TextBox("LOW", shadow=False)

        # Position first level
        high1.to_edge(LEFT, buff=2).shift(UP * 2)
        low1.to_edge(RIGHT, buff=2).shift(UP * 2)

        # Position second level
        high2.next_to(high1, DOWN, buff=1.5)
        low2.next_to(low1, DOWN, buff=1.5)

        # Position third level
        high3.next_to(high2, DOWN, buff=1.5)
        low3.next_to(low2, DOWN, buff=1.5)

        # Create connections with descriptive labels
        conn1 = Connection(high1, low1, "Education")
        conn2 = Connection(high2, low2, "Innovation")
        conn3 = Connection(high3, low3, "Technology")

        # Group all elements
        elements = VGroup(
            high1, low1, high2, low2, high3, low3,
            conn1, conn2, conn3
        )

        # Apply AutoScaled
        #auto_scaled_elements = AutoScaled(elements)

        # Animate level by level
        # Level 1
        self.play(FadeIn(high1))
        self.play(FadeIn(low1))
        self.play(Create(conn1))
        
        # Level 2
        self.play(FadeIn(high2))
        self.play(FadeIn(low2))
        self.play(Create(conn2))
        
        # Level 3
        self.play(FadeIn(high3))
        self.play(FadeIn(low3))
        self.play(Create(conn3))

        # Hold the final frame
        self.wait(5)
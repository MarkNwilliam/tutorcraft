from manim import DOWN, FadeIn, LEFT, RIGHT, Scene, UP, VGroup
from manim.animation.creation import Create
from code_video import Connection, TextBox
from code_video import AutoScaled

class TriangleScene(Scene):
    def construct(self):
        # Create the three components
        top = TextBox("Main Controller\n(Master)", shadow=False)
        worker1 = TextBox("Worker 1\n(Processing)", shadow=False)
        worker2 = TextBox("Worker 2\n(Storage)", shadow=False)

        # Position with top in middle and workers on sides below
        top.move_to(UP)  # This puts it in the middle and slightly up
        worker1.next_to(top, DOWN + LEFT, buff=2)
        worker2.next_to(top, DOWN + RIGHT, buff=2)

        # Create connections from top to workers
        conn1 = Connection(top, worker1, "Tasks")
        conn2 = Connection(top, worker2, "Data", padding=-0.7)
        conn3 = Connection(worker1, worker2, "Data 2")
        conn4 = Connection(worker2, worker1, "Datsa 3")
        conn5 = Connection(worker1, top, "Data 4")
        conn6 = Connection(worker2, top, "Data 5", padding=-0.6)

        # Group all elements to be auto-scaled
        elements = VGroup(top, worker1, worker2, conn1)

        # Apply AutoScaled to all elements
        auto_scaled_elements = AutoScaled(elements)

        # Animate in sequence
        self.play(FadeIn(top))
        
        # Create connections and workers
        self.play(Create(conn1))
        self.play(FadeIn(worker1))
        
        self.play(Create(conn2))
        self.play(FadeIn(worker2))

        self.play(Create(conn3))
        self.play(Create(conn4))    
        self.play(Create(conn5))    
        self.play(Create(conn6))

        # Hold the final frame
        self.wait(5)
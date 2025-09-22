from manim import *

class SleepRule(Scene):
    def construct(self):
        # Set background and title
        self.camera.background_color = BLACK
        title = Text("The Sleep Rule", font_size=48).to_edge(UP)
        underline = Line(title.get_left(), title.get_right()).next_to(title, DOWN)
        self.play(Write(title), Create(underline))
        self.wait(1)

        # Create the heading for the list
        list_heading = Text("What Happens During Sleep", font_size=36).to_edge(LEFT).shift(UP*1.5)
        self.play(Write(list_heading))
        self.wait(0.5)

        # List of benefits
        benefits_list = [
            "Boosts fat-burning hormones (growth hormone)",
            "Lowers cortisol (stress hormone)",
            "Regulates hunger hormones (ghrelin & leptin)",
            "Preserves muscle mass",
            "Increases insulin sensitivity"
        ]

        # Create and animate each bullet point
        bullets = VGroup(*[Text(text).scale(0.8).to_edge(LEFT) for text in benefits_list])
        bullets.arrange(down, buff=0.7, aligned_edge=LEFT).next_to(list_heading, DOWN, aligned_edge=LEFT)

        for bullet in bullets:
            self.play(Write(bullet))
            self.wait(0.5)

        self.wait(2)
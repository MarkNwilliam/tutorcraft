from manim import Create
from manim_voiceover import VoiceoverScene
from code_video import CodeScene
from manim_voiceover.services.gtts import GTTSService
from os.path import dirname

class HighlightScene(CodeScene, VoiceoverScene):
    def construct(self):
        # Set up the voice service
        self.set_speech_service(GTTSService())

        # Create and display the code
        tex = self.create_code("/Users/mac/code-video-generator/jail.py")
        self.play(Create(tex))
        self.wait(1)

        # Introduction
        with self.voiceover("""Let's explore Fail2Ban, your server's security guard. This configuration file 
        defines how it protects your system from malicious attacks."""):
            self.highlight_line(tex, 1, "Fail2Ban Configuration Overview")
            self.wait(1)

        # Default Section
        with self.voiceover("""The DEFAULT section is like the general rulebook. Everything we set here applies 
        to all security checkpoints unless specifically overridden."""):
            self.highlight_line(tex, 3, "Default Settings Section")
            self.wait(1)

        # Ignore IPs
        with self.voiceover("""Think of ignoreip as your VIP list. These IP addresses are always trusted - 
        like giving permanent access cards to your system administrators."""):
            self.highlight_line(tex, 5, "Trusted IP Addresses")
            self.wait(1)

        # Ban Time Settings
        with self.voiceover("""Bantime is like a timeout - here it's set to 10 minutes. If someone misbehaves, 
        they're put in this timeout. For critical systems, consider longer bans."""):
            self.highlight_line(tex, 6, "Ban Duration")
            self.wait(1)

        # Find Time Window
        with self.voiceover("""Findtime is your security camera's memory - it only remembers suspicious activity 
        within this 10-minute window. Make this equal to or slightly longer than your bantime."""):
            self.highlight_line(tex, 7, "Detection Window")
            self.wait(1)

        # Max Retry
        with self.voiceover("""Maxretry is your tolerance level - like a bouncer who gives five chances before 
        showing someone the door. For sensitive services, three attempts is often enough."""):
            self.highlight_line(tex, 8, "Maximum Attempts")
            self.wait(1)

        # SSH Section
        with self.voiceover("""The SSH section shows how to get strict with important services. Notice the 
        one-hour ban and only three retries - because SSH is a favorite target for attackers."""):
            self.highlight_lines(tex, 16, 19, "SSH-Specific Rules")
            self.wait(1)

        # Final overview
        with self.voiceover("""Remember: Your security is only as strong as your configuration. Regular monitoring 
        and adjusting these values is key to maintaining effective protection."""):
            self.highlight_none(tex)
            self.wait(2)

if __name__ == "__main__":
    scene = HighlightScene()
    scene.render()
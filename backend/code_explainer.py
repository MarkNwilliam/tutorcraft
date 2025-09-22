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
        tex = self.create_code("/Users/mac/code-video-generator/install.txt")
        self.play(Create(tex))
        self.wait(1)

        # Introduction
        with self.voiceover("""Welcome to our Fail2Ban installation guide. We'll walk through each step 
        of installing and setting up this essential security tool on your Linux server."""):
            self.highlight_none(tex)
            self.wait(1)

        # Update Package List
        with self.voiceover("""First, we update our system's package list. Think of this like checking 
        a store's inventory before shopping - we want to make sure we get the latest version of Fail2Ban. 
        The sudo command gives us administrative privileges for this operation."""):
            self.highlight_lines(tex, 1, 2, "Update Package List")
            self.wait(2)

        # Install Fail2Ban
        with self.voiceover("""Now we install Fail2Ban using apt, the package manager. The -y flag 
        automatically answers 'yes' to installation prompts, making this suitable for automated scripts. 
        This is like having the installer do all the heavy lifting for us."""):
            self.highlight_lines(tex, 4, 5, "Install Fail2Ban")
            self.wait(2)

        # Enable on Boot
        with self.voiceover("""Next, we enable Fail2Ban to start automatically when your system boots up. 
        Think of this as setting your security guard's work schedule - they'll automatically show up 
        whenever the building opens."""):
            self.highlight_lines(tex, 7, 8, "Enable Auto-start")
            self.wait(2)

        # Start Service
        with self.voiceover("""We then start the Fail2Ban service immediately. While the previous step 
        ensures it runs on future reboots, this command puts our security guard on duty right now."""):
            self.highlight_lines(tex, 10, 11, "Start Service")
            self.wait(2)

        # Check Status
        with self.voiceover("""Finally, we verify that Fail2Ban is running correctly. This status check 
        is like asking for a security report - it tells us if our guard is actively monitoring the system. 
        Look for the 'active (running)' status in green to confirm everything is working."""):
            self.highlight_lines(tex, 13, 14, "Check Status")
            self.wait(2)

        # Conclusion
        with self.voiceover("""And that's it! Your system now has an active security guard watching 
        for suspicious activity. Remember to check the service status periodically and configure 
        Fail2Ban's rules to match your security needs."""):
            self.highlight_none(tex)
            self.wait(2)

if __name__ == "__main__":
    scene = HighlightScene()
    scene.render()
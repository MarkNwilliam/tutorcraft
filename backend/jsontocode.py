import json
import tempfile
import os
from manim import Create
from manim_voiceover import VoiceoverScene
from code_video import CodeScene
from manim_voiceover.services.gtts import GTTSService

class EnhancedCodeScene(CodeScene, VoiceoverScene):
    def __init__(self, json_data):
        super().__init__()
        self.content = json_data

    def construct(self):
        self.set_speech_service(GTTSService())

        # Create temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(self.content['code'])
            temp_path = temp_file.name

        try:
            # Create and display the code
            tex = self.create_code(temp_path)
            self.play(Create(tex))
            self.wait(1)

            # Introduction
            with self.voiceover(self.content['intro']['text']):
                self.highlight_none(tex)
                self.wait(1)

            # Process each section
            for section in self.content['sections']:
                with self.voiceover(section['voiceover']):
                    try:
                        self.highlight_lines(
                            tex, 
                            section['highlight_start'], 
                            section['highlight_end'], 
                            section['title']
                        )
                        self.wait(section['duration'])
                    except Exception as e:
                        print(f"Error highlighting section {section['title']}: {str(e)}")
                        self.highlight_none(tex)
                        self.wait(section['duration'])

            # Conclusion
            with self.voiceover(self.content['conclusion']['text']):
                self.highlight_none(tex)
                self.wait(2)

        finally:
            os.unlink(temp_path)

# Example JSON structure with exact line numbers
example_content = {
    "code": """# Update package list
sudo apt update
sudo apt upgrade -y

# Install Fail2Ban
sudo apt install fail2ban -y

# Enable on boot
sudo systemctl enable fail2ban

# Start service
sudo systemctl start fail2ban

# Check status
sudo systemctl status fail2ban""",
    
    "intro": {
        "text": "Welcome to our Fail2Ban installation guide. We'll walk through each step of installing and setting up this essential security tool on your Linux server."
    },
    
    "sections": [
        {
            "title": "Update Package List",
            "highlight_start": 2,  # sudo apt update
            "highlight_end": 3,    # sudo apt upgrade -y
            "voiceover": "First, we update our system's package list. Think of this like checking a store's inventory before shopping - we want to make sure we get the latest version of Fail2Ban.",
            "duration": 2
        },
        {
            "title": "Install Fail2Ban",
            "highlight_start": 6,  # sudo apt install fail2ban -y
            "highlight_end": 6,
            "voiceover": "Now we install Fail2Ban using apt, the package manager. The -y flag automatically answers 'yes' to installation prompts.",
            "duration": 2
        },
        {
            "title": "Enable Auto-start",
            "highlight_start": 9,  # sudo systemctl enable fail2ban
            "highlight_end": 9,
            "voiceover": "Next, we enable Fail2Ban to start automatically when your system boots up.",
            "duration": 2
        },
        {
            "title": "Start Service",
            "highlight_start": 12,  # sudo systemctl start fail2ban
            "highlight_end": 12,
            "voiceover": "We then start the Fail2Ban service immediately. This puts our security guard on duty right now.",
            "duration": 2
        },
        {
            "title": "Check Status",
            "highlight_start": 15,  # sudo systemctl status fail2ban
            "highlight_end": 15,
            "voiceover": "Finally, we verify that Fail2Ban is running correctly. This status check confirms everything is working properly.",
            "duration": 2
        }
    ],
    
    "conclusion": {
        "text": "And that's it! Your system now has an active security guard watching for suspicious activity. Remember to check the service status periodically."
    }
}

def generate_video(json_path):
    """Generate a video from a JSON configuration file."""
    with open(json_path, 'r') as f:
        content = json.load(f)
    
    scene = EnhancedCodeScene(content)
    scene.render()

if __name__ == "__main__":
    # Save example content to a temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_json:
        json.dump(example_content, temp_json)
        json_path = temp_json.name

    try:
        generate_video(json_path)
    finally:
        os.unlink(json_path)
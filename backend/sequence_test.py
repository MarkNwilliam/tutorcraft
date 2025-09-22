from os.path import dirname
from manim import DOWN, Text, UP
from manim.animation.creation import Create
from code_video import AutoScaled, CodeScene
from code_video.sequence import SequenceDiagramScene, SequenceDiagram
from code_video.widgets import DEFAULT_FONT
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class VoiceoverSequenceDiagramScene(SequenceDiagramScene, VoiceoverScene):
    """Combines SequenceDiagramScene with VoiceoverScene capabilities"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_speech_service(GTTSService())

class OnlineShoppingSequence(VoiceoverSequenceDiagramScene):
    def construct(self):
        # Set up the background (optional)
        example_dir = dirname(__file__)
        #self.add_background(f"{example_dir}/resources/blackboard.jpg")

        # Create the diagram
        diagram = AutoScaled(SequenceDiagram())
        
        # Add the actors
        customer, website, payment, warehouse = diagram.add_objects(
            "Customer", 
            "Website", 
            "Payment System",
            "Warehouse"
        )

        # Add interactions with voiceover narratives
        customer.to(
            website, 
            message="Browse products",
            voiceover="The customer starts browsing products on the e-commerce website"
        )

        customer.to(
            website,
            message="Add to cart",
            voiceover="They find an item they like and add it to their shopping cart"
        )

        website.note(
            message="Update cart total",
            voiceover="The website calculates the total price including taxes and shipping"
        )

        customer.to(
            website,
            message="Checkout",
            voiceover="The customer proceeds to checkout with their selected items"
        )

        website.to(
            payment,
            message="Process payment",
            voiceover="The website securely sends payment information to the payment processing system"
        )

        payment.to(
            payment,
            message="Validate card\nand process",
            voiceover="The payment system validates the credit card and processes the transaction"
        )

        payment.to(
            website,
            message="Payment confirmed",
            voiceover="The payment is confirmed and the website is notified"
        )

        website.to(
            warehouse,
            message="Create order",
            voiceover="A new order is created and sent to the warehouse for fulfillment"
        )

        warehouse.note(
            message="Check inventory",
            voiceover="The warehouse system checks the inventory levels and allocates the items"
        )

        warehouse.to(
            website,
            message="Order confirmed",
            voiceover="The warehouse confirms the order and prepares it for shipping"
        )

        website.to(
            customer,
            message="Order confirmation",
            voiceover="Finally, the customer receives their order confirmation with tracking details"
        )

        # Add title
        title = Text("Online Shopping Process", font=DEFAULT_FONT)
        title.scale(0.8)
        title.to_edge(UP)
        
        # Create initial animation
        self.add(title)
        diagram.next_to(title, DOWN)
        self.play(Create(diagram))

        # Create animations with voiceover
        self.create_diagram_with_voiceover(diagram)

        # Hold the final frame
        self.wait(3)


if __name__ == "__main__":
    scene = OnlineShoppingSequence()
    scene.render()
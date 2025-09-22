# test_wikimedia_fetcher.py
from wikipedia_image_fetcher import WikipediaImageFetcher

def test_wikimedia_image_fetcher():
    # Initialize the correct fetcher class
    fetcher = WikipediaImageFetcher()
    
    # Test with different search terms
    test_terms = [
        "CP violation",
        "Quantum field theory", 
        "Standard Model"
    ]
    
    for term in test_terms:
        print(f"\nTesting with term: '{term}'")
        image_paths = fetcher.get_wikipedia_images(term)  # This returns a LIST
        print("Result:")
        
        if image_paths:
            print(f"Successfully downloaded {len(image_paths)} image(s): {image_paths}")
            
            # Verify each image in the list
            for i, image_path in enumerate(image_paths):
                try:
                    with open(image_path, 'rb') as f:
                        print(f"Image {i+1} exists at: {image_path}")
                        print(f"File size: {len(f.read())} bytes")
                except IOError as e:
                    print(f"Warning: Downloaded file {image_path} cannot be opened: {e}")
        else:
            print("No images were downloaded")

if __name__ == "__main__":
    test_wikimedia_image_fetcher()
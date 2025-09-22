from wikipedia_image_fetcher import WikipediaImageFetcher

def test_wikipedia_image_fetcher():
    # Initialize the fetcher
    fetcher = WikipediaImageFetcher()
    
    # Test with a known Wikipedia article that has images
    test_article = "Quantum chromodynamics"
    num_images = 2
    
    print(f"\nTesting WikipediaImageFetcher with article: '{test_article}'")
    image_paths = fetcher.get_wikipedia_images(test_article, num_images)
    
    print("\nResults:")
    if image_paths:
        print(f"Successfully downloaded {len(image_paths)} images:")
        for path in image_paths:
            print(f"- {path}")
    else:
        print("No images were downloaded")

if __name__ == "__main__":
    test_wikipedia_image_fetcher()
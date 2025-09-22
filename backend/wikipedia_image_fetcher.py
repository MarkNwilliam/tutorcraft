import os
import requests
from PIL import Image
import cairosvg
import concurrent.futures
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('image_fetcher.log')
    ]
)

class WikipediaImageFetcher:
    def __init__(self, headers=None):
        self.headers = headers or {
            'User-Agent': 'DocVideoMaker/1.0 (https://example.com; contact@example.com)'
        }
        self.logger = logging.getLogger(__name__)

    def _get_openverse_images(self, query, num_images=2):
        """Private method to get images from Openverse as fallback"""
        self.logger.info(f"Attempting Openverse fallback for query: {query}")
        url = "https://api.openverse.engineering/v1/images/"
        params = {
            "q": query,
            "license_type": "commercial,modification",
            "page_size": num_images
        }
        
        try:
            response = requests.get(url, params=params, headers={"Accept": "application/json"})
            response.raise_for_status()
            data = response.json()
            
            image_urls = []
            for result in data.get("results", [])[:num_images]:
                if result.get("url"):
                    image_urls.append(result["url"])
            
            self.logger.info(f"Found {len(image_urls)} images from Openverse")
            return image_urls
        except Exception as e:
            self.logger.error(f"Openverse API error: {e}")
            return []

    def _download_image(self, url, save_dir):
        """Helper method to download and verify an image"""
        self.logger.info(f"Downloading image from URL: {url}")
        try:
            file_name = os.path.basename(url)
            save_path = os.path.join(save_dir, file_name)
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            with open(save_path, "wb") as img_file:
                img_file.write(response.content)

            # Handle SVG conversion
            if file_name.lower().endswith(".svg"):
                self.logger.info("Converting SVG to PNG")
                png_path = save_path.rsplit('.', 1)[0] + '.png'
                cairosvg.svg2png(url=save_path, write_to=png_path)
                os.unlink(save_path)
                save_path = png_path

            # Verify the image
            with Image.open(save_path) as img:
                img.verify()
            
            self.logger.info(f"Successfully downloaded image to: {save_path}")
            return save_path
        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            if os.path.exists(save_path):
                os.unlink(save_path)
            return None

    def get_wikipedia_images(self, article_title, num_images=2, save_dir="./downloaded_images"):
        """Original method with Openverse fallback added"""
        self.logger.info(f"Starting image fetch for: {article_title}")
        os.makedirs(save_dir, exist_ok=True)

        # First try Wikipedia (your original code)
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": article_title,
            "prop": "images",
            "imlimit": 50
        }

        self.logger.info("Making initial Wikipedia API request")
        response = requests.get(url, params=params, headers=self.headers)
        data = response.json()
        self.logger.debug(f"Initial Wikipedia response: {data}")

        pages = data.get("query", {}).get("pages", {})
        page_id = list(pages.keys())[0] if pages else None

        if not page_id or "missing" in pages[page_id]:
            self.logger.warning(f"No article found for topic: {article_title}")
            self.logger.info("Searching for related articles...")
            
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": article_title,
                "srlimit": 1
            }
            
            search_response = requests.get(search_url, params=search_params, headers=self.headers)
            search_data = search_response.json()
            self.logger.debug(f"Wikipedia search response: {search_data}")

            if "query" in search_data and "search" in search_data["query"]:
                article_title = search_data["query"]["search"][0]["title"]
                self.logger.info(f"Using related article title: {article_title}")
            else:
                self.logger.warning(f"No related articles found, switching to Openverse fallback")
                openverse_urls = self._get_openverse_images(article_title, num_images)
                image_paths = []
                for url in openverse_urls:
                    path = self._download_image(url, save_dir)
                    if path:
                        image_paths.append(path)
                self.logger.info(f"Returning {len(image_paths)} images from Openverse fallback")
                return image_paths

        params["titles"] = article_title
        response = requests.get(url, params=params, headers=self.headers)
        data = response.json()
        self.logger.debug(f"Updated Wikipedia response: {data}")

        pages = data.get("query", {}).get("pages", {})
        page_id = list(pages.keys())[0] if pages else None
        if not page_id or "images" not in pages[page_id]:
            self.logger.warning(f"No images found in article: {article_title}")
            self.logger.info("Switching to Openverse fallback")
            openverse_urls = self._get_openverse_images(article_title, num_images)
            image_paths = []
            for url in openverse_urls:
                path = self._download_image(url, save_dir)
                if path:
                    image_paths.append(path)
            self.logger.info(f"Returning {len(image_paths)} images from Openverse fallback")
            return image_paths

        # Include SVGs in the filtered image titles
        image_titles = [
            img["title"] for img in pages[page_id]["images"]
            if "logo" not in img["title"].lower() and "icon" not in img["title"].lower()
        ]
        self.logger.info(f"Found {len(image_titles)} candidate images after filtering")

        image_titles = image_titles[:num_images]
        image_paths = []

        def download_single_image(title):
            self.logger.info(f"Processing image title: {title}")
            img_params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "imageinfo",
                "iiprop": "url"
            }

            img_response = requests.get(url, params=img_params, headers=self.headers)
            img_data = img_response.json()
            self.logger.debug(f"Image URL response: {img_data}")

            img_pages = img_data.get("query", {}).get("pages", {})
            img_id = list(img_pages.keys())[0] if img_pages else None
            if img_id and "imageinfo" in img_pages[img_id]:
                img_url = img_pages[img_id]["imageinfo"][0]["url"]
                self.logger.info(f"Found image URL: {img_url}")
                return self._download_image(img_url, save_dir)
            return None

        # Use ThreadPoolExecutor for parallel downloads
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(image_titles))) as executor:
            future_to_title = {executor.submit(download_single_image, title): title for title in image_titles}
            
            for future in concurrent.futures.as_completed(future_to_title):
                result = future.result()
                if result:
                    image_paths.append(result)
                    self.logger.info(f"Successfully processed image: {result}")

        # If we didn't get enough images from Wikipedia, try Openverse
        if len(image_paths) < num_images:
            needed = num_images - len(image_paths)
            self.logger.info(f"Only got {len(image_paths)} images from Wikipedia, need {needed} more")
            self.logger.info("Attempting Openverse fallback for remaining images")
            openverse_urls = self._get_openverse_images(article_title, needed)
            for url in openverse_urls:
                path = self._download_image(url, save_dir)
                if path:
                    image_paths.append(path)
                    self.logger.info(f"Added fallback image: {path}")

        self.logger.info(f"Final image count: {len(image_paths)}")
        return image_paths[:num_images]
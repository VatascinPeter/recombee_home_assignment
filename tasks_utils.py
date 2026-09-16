import requests


NS = {"g": "http://base.google.com/ns/1.0"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB


def parse_items(root, feed_id):
    """Find all items, return their attributes and all image urls"""
    items = []
    urls = set()

    for item in root.iterfind("channel/item"):
        urls.update(c.text.strip() for c in item if "image_link" in c.tag and c.text and c.text.strip())
        g_id = item.findtext("g:id", namespaces=NS)
        if not g_id:
            print("Skipping item without g:id")
            continue
        title = item.findtext("title")
        description = item.findtext("description")
        native_price = item.findtext("g:price", "", namespaces=NS)
        price, _, currency = native_price.strip().partition(" ") if native_price else (None, None, None)
        price, currency = price or None, currency or None
        items.append((feed_id, g_id, title, description, price, currency))
    return items, urls


def get_image_data(img_url):
    """Download an image and return it as a byte string and image type (or None if failed)"""
    try:
        with requests.get(img_url, stream=True, timeout=10) as response:
            # bad response
            if response.status_code != 200:
                print(f"Error getting image data ({img_url}): {response.status_code}")
                return None

            content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
            # is not image
            if not content_type.startswith("image/"):
                print(f"Error getting image data ({img_url}): Not an image")
                return None

            declared = response.headers.get("Content-Length", "")
            # image too large
            if declared.isdigit() and int(declared) > MAX_IMAGE_BYTES:
                print(f"Error getting image data ({img_url}): Too large ({declared} bytes)")
                return None

            data = bytearray()
            # iteratively download image - stop if too large
            for chunk in response.iter_content(chunk_size=64 * 1024):
                data.extend(chunk)
                if len(data) > MAX_IMAGE_BYTES:
                    print(f"Error getting image data ({img_url}): Too large")
                    return None
            return bytes(data), content_type
    except requests.exceptions.RequestException as e:
        print(f"Error getting image data ({img_url}): {e}")
        return None

import xml.etree.ElementTree as ET

from tasks_utils import parse_items

FEED = """
<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">
<channel>
    <title>Test feed</title>
    <item>
        <g:id>A1</g:id>
        <title>Shirt</title>
        <description>Nice shirt</description>
        <g:image_link> https://example.com/a.jpg </g:image_link>
        <g:additional_image_link>https://example.com/b.jpg</g:additional_image_link>
        <g:price> 299.00 NOK </g:price>
    </item>
    <item>
        <g:id>A2</g:id>
        <title>Shirt - Large</title>
        <g:image_link>https://example.com/a.jpg</g:image_link>
    </item>
    <item>
        <title>Item without id</title>
        <g:image_link>https://example.com/skipped.jpg</g:image_link>
    </item>
</channel>
</rss>
"""


def test_parse_items():
    items, urls = parse_items(ET.fromstring(FEED), feed_id=7)

    assert items == [
        (7, "A1", "Shirt", "Nice shirt", "299.00", "NOK"),
        (7, "A2", "Shirt - Large", None, None, None),   # missing description/price -> None
    ]                                                     # item without g:id skipped
    # stripped, deduplicated, kept images from skipped items
    assert urls == {"https://example.com/a.jpg", "https://example.com/b.jpg", "https://example.com/skipped.jpg"}


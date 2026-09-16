import os
import traceback
from contextlib import suppress
import xml.etree.ElementTree as ET
import dramatiq
from dramatiq.middleware import TimeLimitExceeded
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from psycopg2.extras import execute_batch
from tasks_utils import parse_items, get_image_data
from db import get_cursor


dramatiq.set_broker(RabbitmqBroker(url=os.environ["RABBITMQ_URL"]))


@dramatiq.actor(max_retries=0)
def parse_xml(xml_file, feed_id):
    """parse feed xml file and save each item data and image in database"""
    try:
        file_data = ET.parse(xml_file)
        items, urls = parse_items(file_data.getroot(), feed_id)
        # download all images before saving them in the database
        images = []
        for url in urls:
            image_data = get_image_data(url)
            if image_data:
                images.append((feed_id, image_data[0], image_data[1], url))

        # upload data to the database in a batch
        with get_cursor() as cur:
            execute_batch(cur, "INSERT INTO items (feed_id, g_id, title, description, price, currency) VALUES (%s, %s, %s, %s, %s, %s) "
                               "ON CONFLICT (feed_id, g_id) DO NOTHING;",
                             items)
            execute_batch(cur,
                          "INSERT INTO images (feed_id, image_data, image_format, url) VALUES (%s, %s, %s, %s);",
                          images)
            # set status to done
            cur.execute("UPDATE feeds SET status = %s WHERE id = %s;", ("done", feed_id))
    except (Exception, TimeLimitExceeded):
        print("Failed to parse feed data")
        traceback.print_exc()
        with get_cursor() as cur:
            cur.execute("UPDATE feeds SET status = %s WHERE id = %s;", ("failed", feed_id))
    finally:
        # delete the shared xml file after processing
        with suppress(FileNotFoundError):
            os.remove(xml_file)

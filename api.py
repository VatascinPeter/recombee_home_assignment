import os
from contextlib import suppress
from flask import Flask, request, Response
from tasks import parse_xml
from db import get_cursor

app = Flask(__name__)
UPLOAD_FOLDER = '/app/uploads'

@app.route("/feeds", methods=["POST"])
def post_feeds():
    """post a new feed, process xml file asynchronously"""
    # retrieve xml file and save in a shared volume
    file = request.files.get("file")
    if not file or not file.filename:
        return {"error": "No file provided"}, 400

    # insert a new feed into the database
    with get_cursor() as cur:
        cur.execute("INSERT INTO feeds DEFAULT VALUES RETURNING id;")
        feed_id = cur.fetchone()[0]

    # save the xml file to be accessible by the worker
    file_path = os.path.join(UPLOAD_FOLDER, f"{feed_id}.xml")
    try:
        file.save(file_path)

        # process file asynchronously
        parse_xml.send(file_path, feed_id)
    except Exception:
        app.logger.exception("Feed %s could not be queued", feed_id)
        with suppress(FileNotFoundError):
            os.remove(file_path)
        with get_cursor() as cur:
            cur.execute("DELETE FROM feeds WHERE id = %s;", (feed_id,))
        return {"error": "Feed could not be queued for processing"}, 503

    # return id
    return {"id": str(feed_id)}, 202


@app.route("/feeds/<int:feed_id>", methods=["GET"])
def get_feed(feed_id):
    """return status of a specific feed"""
    with get_cursor() as cur:
        cur.execute("SELECT status FROM feeds WHERE id = %s;", (feed_id,))
        status = cur.fetchone()
    if status is None:
        return {"error": "Feed not found"}, 404
    return {"status": status[0]}, 200


@app.route("/feeds/<int:feed_id>/items", methods=["GET"])
def get_feeds_items(feed_id):
    """return array of item_ids of a specific feed"""
    with get_cursor() as cur:
        cur.execute("SELECT id FROM feeds WHERE id = %s;", (feed_id,))
        if not cur.fetchone():
            return {"error": "Feed not found"}, 404
        cur.execute("SELECT g_id FROM items WHERE feed_id = %s;", (feed_id,))
        item_ids = [row[0] for row in cur.fetchall()]
    return item_ids, 200


@app.route("/feeds/<int:feed_id>/items/<item_id>", methods=["GET"])
def get_feeds_item(feed_id, item_id):
    """return attributes of a specific item"""
    with get_cursor() as cur:
        cur.execute("SELECT g_id, title, description, price, currency FROM items WHERE g_id = %s AND feed_id = %s;",
                    (item_id, feed_id))
        item_data = cur.fetchone()

    if not item_data:
        return {"error": "Item not found"}, 404
    return {"id": item_data[0],
            "title": item_data[1],
            "description": item_data[2],
            "price": float(item_data[3]) if item_data[3] is not None else None,
            "currency": item_data[4]}, 200


@app.route("/feeds/<int:feed_id>/images", methods=["GET"])
def get_feeds_images(feed_id):
    """return all image_ids from a feed"""
    with get_cursor() as cur:
        cur.execute("SELECT id FROM feeds WHERE id = %s;", (feed_id,))
        if not cur.fetchone():
            return {"error": "Feed not found"}, 404
        cur.execute("SELECT id FROM images WHERE feed_id = %s;", (feed_id,))
        img_ids = [row[0] for row in cur.fetchall()]
    return img_ids, 200


@app.route("/feeds/<int:feed_id>/images/<int:img_id>", methods=["GET"])
def get_feeds_image(feed_id, img_id):
    """return the image data of an image"""
    with get_cursor() as cur:
        cur.execute("SELECT image_data, image_format FROM images WHERE id = %s AND feed_id = %s;", (img_id, feed_id))
        row = cur.fetchone()

    if row is None:
        return {"error": "Image not found"}, 404
    return Response(bytes(row[0]), content_type=row[1])

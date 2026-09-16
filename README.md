# Item feed service

## How to run

To build and start the programme, run the command in this folder with Docker Desktop running:

```shell
docker compose up --build
```

Wait until all dependencies are installed, and the database and messaging queue are set up. The API is ready when the log shows _Listening at: http://0.0.0.0:8000_.

To reset, removing containers and all volumes, run this command:

```shell
docker compose down -v
```

__Example commands__ (for Windows)

Posting a feed (replace angle brackets <> with real data):

```shell
curl.exe -F "file=@<xml_filepath>" http://localhost:8000/feeds
```

For example:

```shell
curl.exe -F "file=@Data/feed_example.xml" http://localhost:8000/feeds
```

Checking the status of processing a feed (other REST API endpoints likewise):

```shell
curl.exe http://localhost:8000/feeds/<feed_id>
```

Saving an image:

```shell
curl.exe http://localhost:8000/feeds/<feed_id>/images/<image_id> --output <output_filepath>
```

Specifically, this command saves image with id=3 from feed with id=1 to a file 'img.jpg':

```shell
curl.exe http://localhost:8000/feeds/1/images/3 --output img.jpg
```
Checking status of a non-existent feed yields 404 'Feed not found':
```shell
curl.exe http://localhost:8000/feeds/99
```

Not passing a file yields 400 'No file provided':

```shell
curl.exe -X POST http://localhost:8000/feeds
```

Passing a non-parsable file still creates a feed, but it will be marked 'failed' by the background worker:

```shell
curl.exe -F "file=@api.py" http://localhost:8000/feeds
curl.exe http://localhost:8000/feeds/<id from previous command>
```

## REST API Endpoints

| Endpoint | Returns |
|-----------------------------------|-----------------------------------------------------|
| POST /feeds | {"id": "1"}, 202 |
| GET /feeds/\<id> | {"status": "processing" \| "done" \| "failed"} |
| GET /feeds/\<id>/items | array of item IDs (g:id values) |
| GET /feeds/\<id>/items/\<item_id> | {"id", "title", "description", "price", "currency"} |
| GET /feeds/\<id>/images | array of image IDs assigned by the service |
| GET /feeds/\<id>/images/\<image_id> | the image bytes, with its original content type |

Note: \<item_id> is the g:id value of an item, feed id and g:id uniquely define an item

## Project Structure

__POST /feeds__ stores a feed row with status processing, saves the XML to a volume shared with the worker, and puts a
message on RabbitMQ. It returns immediately. The worker parses the file, downloads each distinct image, and writes all
items, images and the done status in a single transaction, so a feed's data either appears complete or not at all. On
any error the feed is marked _failed_.

### Docker parts

__docker-compose.yml__ - runs four containers, API handling, Background worker, RabbitMQ Messaging Queue, PostgreSQL Database

__Dockerfile__ - instructions to correctly set up Python environment for the API handling and Background worker

__requirements.txt__ - required Python libraries and their versions

### Python

__api.py__ - REST API endpoint handling implemented using _Flask_, GET endpoints directly access the database

__tasks.py__ - _Dramatiq_ actor for xml file parsing and data storing in database

__db.py__ - using _psycopg2_ library, handles a database connection pool and provides cursors for _api.py_ and _tasks.py_

__tasks_utils.py__ - extracting data from xml tree and downloading images from urls

### Database

__database.sql__ - PostgreSQL definition of used database. Three tables - _feeds_ storing the status of each feed, _items_ storing data for each stored item and an id of its feed, _images_ storing all saved images and their feed

### Testing

__tests/test_tasks_utils.py__ - testing, whether the xml tree parsing function correctly saves all items with g:id defined and finds all image urls

Run locally (pytest required):
```shell
python -m pytest tests/test_tasks_utils.py
```
Run in Docker (pytest in requirements.txt):
```shell
docker compose build api
docker compose run --rm --no-deps api python -m pytest
```

__Data__ - folder containing xml files for testing

__Data/feed_example.xml__ - provided example feed (modified by adding _\</rss>_ in the end to be parsable, non-functioning image urls)

__Data/feed_example_2.xml__ - AI generated example file with 10 items and 18 functioning image urls


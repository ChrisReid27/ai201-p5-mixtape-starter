## Mixtape Codebase Map

### The main app files

- `app.py` is the application factory and database setup. It creates the Flask
  app, applies configuration, initializes SQLAlchemy, registers the route
  blueprints, and creates the database tables.
- `models.py` defines the persisted entities and their relationships:
  `User`, `Song`, `Tag`, `ListeningEvent`, `Rating`, `Playlist`, and
  `Notification`. It also defines the friendship, song-tag, and playlist-song
  association tables. Each model provides a `to_dict()` method for API output.
- `seed_data.py` is a data-population script. It creates example users,
  friendships, songs, tags, playlists, listening events, ratings-related data,
  and notifications.
- `instance/mixtape.db` is the SQLite database used by the default
  configuration.

### The routes

- `routes/songs.py` defines endpoints for song search, song details, ratings,
  and listening events. It connects those endpoints to `search_service`,
  `notification_service`, and `streak_service`.
- `routes/playlists.py` defines endpoints for playlist creation, playlist
  metadata, playlist-song retrieval, and adding songs to playlists. It connects
  playlist operations to `playlist_service` and playlist additions to
  `notification_service`.
- `routes/users.py` defines endpoints for user details, streaks,
  notifications, and notification read status. It connects those endpoints to
  `streak_service` and `notification_service`.
- `routes/feed.py` defines endpoints for the friends-listening-now feed and the
  general activity feed. It connects both endpoints to `feed_service`.
- `routes/__init__.py` marks the routes directory as a Python package.

### The services

- `services/feed_service.py` assembles social feed data from users, friendships,
  songs, and listening events. `get_friends_listening_now` produces each
  friend's most recent listening activity within the recent-activity window.
  `get_activity_feed` produces a limited list of recent activity from friends.
- `services/notification_service.py` coordinates notifications, playlist
  additions, and ratings. `create_notification` creates a notification;
  `add_to_playlist` associates a song with a playlist and creates the related
  notification; `rate_song` creates or updates a rating; `get_notifications`
  retrieves notifications; and `mark_as_read` updates notification status.
- `services/playlist_service.py` coordinates playlist creation and retrieval.
  `create_playlist` creates a playlist; `get_playlist_songs` returns its songs
  in playlist order; `get_playlist` returns playlist metadata; and
  `get_user_playlists` returns a user's playlists.
- `services/search_service.py` provides song lookup operations.
  `search_songs` searches song titles and artists and serializes the results
  with their tags. `get_song` retrieves one song and serializes it.
- `services/streak_service.py` coordinates listening events and streak data.
  `record_listening_event` creates an event and updates the listener's streak;
  `update_listening_streak` applies the calendar-day streak rules; and
  `get_streak` returns a user's current streak.
- `services/__init__.py` marks the services directory as a Python package.

### Tests + project documentation

- `tests/test_streaks.py` exercises the streak service with different listening
  dates and user histories.
- `tests/test_search.py` exercises song searching with songs having different
  tag relationships and with unmatched queries.
- `tests/test_playlists.py` exercises playlist creation data and ordered song
  retrieval, including empty playlists.
- `README.md` documents the project purpose, setup, application structure, and
  feature entry points.
- `requirements.txt` lists the Flask, SQLAlchemy, dotenv, and pytest
  dependencies.

### Data flow (rating a song)

1. A client sends `POST /songs/<song_id>/rate` with `user_id` and `score` in
   the JSON request body.
2. `routes/songs.py:rate` reads the request values and calls
   `notification_service.rate_song(user_id, song_id, score)`.
3. `rate_song` uses the database session to load the referenced `Song` and
   `User`.
4. The service looks for a `Rating` associated with that user and song.
5. An existing rating is updated; otherwise, the service creates a new
   `Rating` model instance.
6. The service commits the rating through the shared SQLAlchemy session and
   returns the rating model.
7. The route calls `rating.to_dict()` and returns the serialized rating as a
   JSON response.

### Patterns I noticed

- The application uses an application factory, allowing different
  configurations and database connections to be supplied when creating an app.
- Flask blueprints divide the HTTP API by feature area: songs, playlists,
  users, and feeds.
- Routes focus on HTTP input and output, while services coordinate domain
  operations and persistence.
- SQLAlchemy models represent database entities and relationships, while
  association tables represent many-to-many connections.
- Model `to_dict()` methods provide a consistent boundary between database
  objects and JSON API responses.
- Services are organized by domain responsibility: search, playlists,
  notifications, feeds, and listening streaks.
- Service results commonly use model instances for write operations and
  dictionaries or lists of dictionaries for read operations.
- Pytest fixtures create configured applications and isolated databases so each
  test module can exercise its related service area independently.


## Root Cause Analysis Issue 1

| # | Title | Affected service |
|---|-------|-----------------|
| 1 | My listening streak keeps resetting | `streak_service.py` |

I listen to something on Mixtape every single day — I haven't missed a day in weeks. On Saturday night my streak was at 12. Sunday morning I played a song like always, checked my profile, and my streak said 1. This is the second time it's happened, and both times it was a Sunday. Listening again on Monday bumped it to 2, so it's counting again — it just threw away my whole streak.

Steps I took:

Listened to a song every calendar day, including Saturday.
Listened again Sunday morning and checked my streak (GET /users/<my_id>/streak).
Expected: streak goes from 12 to 13 — I listened on consecutive days. Actual: streak shows 1, as if I'd skipped a day.

### How I reproduced it:
In `tests/test_streaks.py`, the final test within the suite is the Sunday-specific test designed for this issue. I ran it from the from the terminal using `pytest tests/test_streaks.py -k sunday -v`. The test creates a fresh user, calls `update_listening_streak` with Saturday, June 15, 2024, and then calls it again with Sunday, June 16, 2024. The first call sets the streak to 1 and the second should increase it to 2. Instead, the test fails with `assert 1 == 2`, reproducing the issue 1 issue.

## Root Cause Analysis Issue 2

| # | Title | Affected service |
|---|-------|-----------------|
| 2 | Friends Listening Now shows people from yesterday | `feed_service.py` |

"Friends Listening Now" is supposed to show me what my friends are playing right now — or at least what they've played today. This morning around 9am it showed darius "listening now" to a song he told me he played at 11pm last night, before he went to bed. He hadn't opened the app all morning. Stuff from yesterday evening keeps hanging around in the feed until the same time the next day.

Steps I took:

Opened my feed in the morning (GET /feed/<my_id>/listening-now).
Cross-checked with darius: his last listen was the previous night.
Expected: only friends who have listened today appear. Actual: friends whose last listen was yesterday evening still show up the next morning.


### How I reproduced it:
In the test suite, I made a temporary test called `test_feed_reproduction.py` and ran it with `pytest tests/test_feed_reproduction.py -v`. The test created a viewer, a friend, a friendship between them on the system, and a valid song. It then created one `ListeningEvent` for the friend with its timestamp set to the previous evening, approximately 10 hours before the feed request. No newer listening event was created for that friend. This test called `get_friends_listening_now(viewer.id)` and expected an empty feed because the friend had not listened during the current calendar day. Instead, the feed included the friend's event from before because it was still within the service's rolling 24-hour window, failing the temp test, and issue 2 was recreated.

## Root Cause Analysis Issue 3

| # | Title | Affected service |
|---|-------|-----------------|
| 3 | The same song keeps showing up twice in search | `search_service.py` |

When I search, some songs come back two or even three times — identical entries, same song. I searched "Anthem" and Crown Heights Anthem by Borough Kings showed up three times in the results. Other songs only show up once. Nothing about the duplicates looks different; it's just the same result repeated.

Steps I took:

Searched for a song (GET /songs/search?q=Anthem).
Counted the results.
Expected: each matching song appears exactly once. Actual: some songs appear once, others two or three times, for a single-song match.

### How I reproduced it:
The app state requires that the database has a valid user, a valid song whose title or artist matches the search query, and at mimnimum two tags asscociated with the song. The testing data in this example is Crown Heights Anthem for the song, the artist is Borough Kings, and the tags are rap, hip-hop, and boom bap. In tests folder, in `test_search.py`, there's a test called `test_search_no_duplicates_multi_tag_song` and I ran it with `pytest tests/test_search.py -k multi_tag -v`. The test simulates the song Crown Heights Anthem getting assigned its tags. Then matching results displays the song three times, therefore failing the test and mimicking issue 3.
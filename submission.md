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

### How I reproduced it:


## Root Cause Analysis Issue 2

| # | Title | Affected service |
|---|-------|-----------------|
| 2 | Friends Listening Now shows people from yesterday | `feed_service.py` |

### How I reproduced it:


## Root Cause Analysis Issue 3

| # | Title | Affected service |
|---|-------|-----------------|
| 3 | The same song keeps showing up twice in search | `search_service.py` |

### How I reproduced it:


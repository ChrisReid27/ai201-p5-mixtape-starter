from datetime import datetime, timedelta, timezone

from app import create_app, db
from models import User, Song, ListeningEvent, friendships
from services.feed_service import get_friends_listening_now


def test_yesterday_event_appears_in_listening_now_feed():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with app.app_context():
        db.create_all()

        viewer = User(username="viewer", email="viewer@example.com")
        friend = User(username="friend", email="friend@example.com")
        db.session.add_all([viewer, friend])
        db.session.flush()

        db.session.execute(
            friendships.insert().values(
                user_id=viewer.id,
                friend_id=friend.id,
            )
        )

        song = Song(
            title="Late Night Song",
            artist="Test Artist",
            shared_by=friend.id,
        )
        db.session.add(song)
        db.session.flush()

        event = ListeningEvent(
            user_id=friend.id,
            song_id=song.id,
            listened_at=datetime.now(timezone.utc) - timedelta(hours=10),
        )
        db.session.add(event)
        db.session.commit()

        feed = get_friends_listening_now(viewer.id)

        assert len(feed) == 0
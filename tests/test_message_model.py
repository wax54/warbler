"""Message model tests."""

# run these tests like:
# python -m unittest test_message_model.py

import os
from unittest import TestCase

from db_setup import connect_db, db
from users.models import User, Follow
from messages.models import Message

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test model for User."""

    def setUp(self):
        """Create test client, add sample data."""
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follow.query.delete()
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        db.session.add(u)
        db.session.commit()

        self.u_id = u.id
        self.client = app.test_client()

    def test_message_model(self):
        """Does basic model work?"""
        m = Message(
            text="Test Message",
            user_id=self.u_id
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(m.text, "Test Message")
        self.assertEqual(m.user_id, self.u_id)
        self.assertIsNotNone(m.timestamp)
        self.assertIsNotNone(m.id)

        u = User.query.get(self.u_id)
        self.assertEqual(m.user, u)

    def test_message_repr(self):
        m = Message(
            text="Test Message",
            user_id=self.u_id
        )
        db.session.add(m)
        db.session.commit()

        id = m.id
        self.assertEqual(
            m.__repr__(), f"<Message #{id}: u_id={self.u_id}>")

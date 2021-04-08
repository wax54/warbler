"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import Message, User, connect_db, db

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import CURR_USER_KEY, app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        testuser = User.signup(username="testuser",
                               email="test@test.com",
                               password="testuser",
                               image_url=None)
        db.session.commit()
        self.testu_id = testuser.id

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testu_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_unathorized_add_message(self):
        """Can unauthorized users create a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                #  make sure no user is logged in
                if sess.get(CURR_USER_KEY):
                    del sess[CURR_USER_KEY]

            resp = c.post(f"/messages/new")

            # still redirects, but...
            self.assertEqual(resp.status_code, 302)
            resp = c.get(resp.location)
            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized.', html)

    def test_add_message_without_text(self):
        """What happens if a user submits a blank message?"""

        # Get Client
        with self.client as c:
            # Use Session to spoof user being logged in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testu_id

            # Now, that session setting is saved, Test

            resp = c.post("/messages/new", data={"text": ""})

            # Make sure you get the form page back
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('>Add my message!</button>', html)

    def test_show_message(self):
        """Can user view a message?"""

        # get test client
        with self.client as c:
            # Use Session to spoof user being logged in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testu_id
            # make a message
            m = Message(text="Test Message",
                        user_id=self.testu_id)
            db.session.add(m)
            db.session.commit()

            resp = c.get(f"/messages/{m.id}")

            # Make sure you get the form page back
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn(f'>{m.text}</p>', html)

    def test_delete_message(self):
        """Can a user delete their message"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testu_id

            m = Message(text="Test Message",
                        user_id=self.testu_id)
            db.session.add(m)
            db.session.commit()
            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post(f"/messages/{m.id}/delete")

            # redirects
            self.assertEqual(resp.status_code, 302)

            test_m = Message.query.get(m.id)
            self.assertIsNone(test_m)

    def test_unathorized_delete_message(self):
        """Can a user delete another users message"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:

            # SOME OTHER USER TEST
            another_user = User.signup(username="testuser2",
                                       email="test2@test.com",
                                       password="PASSWORD",
                                       image_url=None)
            db.session.add(another_user)
            db.session.commit()

            with c.session_transaction() as sess:
                # a different user is logged in
                sess[CURR_USER_KEY] = another_user.id
            # message belongs to original test user
            m = Message(text="Test Message",
                        user_id=self.testu_id)
            db.session.add(m)
            db.session.commit()

            resp = c.post(f"/messages/{m.id}/delete")

            # still redirects, but...
            self.assertEqual(resp.status_code, 302)
            # the message still exists
            test_m = Message.query.get(m.id)
            self.assertIsNotNone(test_m)

            # NO USER TEST
            with c.session_transaction() as sess:
                # no user is logged in
                del sess[CURR_USER_KEY]
            resp = c.post(f"/messages/{m.id}/delete")

            # still redirects, but...
            self.assertEqual(resp.status_code, 302)
            # the message still exists
            test_m = Message.query.get(m.id)
            self.assertIsNotNone(test_m)

"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py

from app import CURR_USER_KEY, app
import os
from unittest import TestCase

from db_setup import connect_db, db
from users.models import User
from messages.models import Message

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class LikeFeatureTestCase(TestCase):
    """Test views for routes having to do with the like feature."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.u1_info = {"username": "testuser",
                        "email": "test@test.com",
                        "password": "testuser",
                        "image_url": ""}

        testuser = User.signup(**self.u1_info)
        db.session.commit()

        self.u1_info["id"] = testuser.id

        self.message_info = {"text": "TestMessage",
                             "user_id": testuser.id}
        m = Message(**message_info)
        db.session.add(m)
        db.session.commit()
        self.message_info["id"] = m.id

        def test_like_message_route_works(self):
            with self.client as c:
                user = User.query.get(self.u1_info["id"])
                #signed in as user 1
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = user.id

                #user has no like messages
                self.assertEqual(len(user.likes), 0)
                #like the post
                resp = c.post(f'users/add_like/{self.message_info["id"]}')

                self.assertEqual(resp.status_code, 302)
                #SUDDENLY user has a like message! and its that message!
                self.assertEqual(user.likes[0].id, self.message_info["id"])

                #call the same url again to unlike
                resp = c.post(f'users/add_like/{self.message_info["id"]}')

                #user has no like messages again!
                self.assertEqual(len(user.likes), 0)


class UserViewTestCase(TestCase):
    """Test views for Users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        testuser = User.signup(username="testuser",
                               email="test@test.com",
                               password="testuser",
                               image_url=None)
        testuser2 = User.signup(username="testuser2",
                                email="test2@test.com",
                                password="testuser2",
                                image_url=None)
        db.session.commit()
        self.u1_id = testuser.id
        self.u2_id = testuser2.id

    def test_user_follow_route_works(self):
        """Does following a user work?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            #signed in as user 1
            resp = c.post(f'/users/follow/{self.u2_id}')
            u2 = User.query.get(self.u2_id)
            self.assertEqual(u2.followers[0].id, self.u1_id)

    def test_you_you_cant_follow_yourself(self):
        """if you post to your own follow link, does it work?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            #signed in as user 1
            resp = c.post(f'/users/follow/{self.u1_id}')
            self.assertEqual(resp.status_code, 302)
            resp = c.get(resp.location)
            html = resp.get_data(as_text=True)
            self.assertIn("You Can&#39;t follow yourself Bud.", html)
            u1 = User.query.get(self.u1_id)
            self.assertEqual(len(u1.following), 0)

    def test_user_follow_route_redirects_unauthorized_users(self):
        with self.client as c:
            with c.session_transaction() as sess:
                #log out user if logged in
                if sess.get(CURR_USER_KEY):
                    del sess[CURR_USER_KEY]
            #Not Signed in
            resp = c.post(f'/users/follow/{self.u2_id}')
            self.assertEqual(resp.status_code, 302)

    def test_user_stop_follow_route_works(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            #signed in as user 1
            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)
            #follow user 2
            u1.following.append(u2)
            db.session.commit()

            #u2 = User.query.get(self.u2_id)

            #check to make sure they are being followed
            self.assertEqual(u2.followers[0].id, self.u1_id)

            #send the request to stop following user 2 (logged in as user 1)
            resp = c.post(f'/users/stop-following/{self.u2_id}')

            self.assertEqual(len(u2.followers), 0)

    def test_user_stop_follow_route_redirects_unauthorized_users(self):
        with self.client as c:
            with c.session_transaction() as sess:
                #log out user if logged in
                if sess.get(CURR_USER_KEY):
                    del sess[CURR_USER_KEY]
            #Not Signed in
            resp = c.post(f'/users/stop-following/{self.u2_id}')
            self.assertEqual(resp.status_code, 302)

    def test_view_user_followers(self):
        """Can a user view another users followers?"""

        with self.client as c:
            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)
            u1_username = u1.username
            u2_username = u2.username
            u1.following.append(u2)
            u1.followers.append(u2)
            db.session.commit()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            #Logged in as user 1 view your own following page
            resp = c.get(f"/users/{self.u1_id}/followers")

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn(u2_username, html)

            #Logged in as user 1 view user 2's following page
            resp = c.get(f"/users/{self.u2_id}/followers")

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn(u1_username, html)

    def test_view_user_followers_redirects_unauthorized_users(self):
        """Can an unauthorized visitor view a users followers?"""

        with self.client as c:
            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)
            u1_username = u1.username
            u2_username = u2.username
            u1.following.append(u2)
            u1.followers.append(u2)
            db.session.commit()

            with c.session_transaction() as sess:
                #log out user if logged in
                if sess.get(CURR_USER_KEY):
                    del sess[CURR_USER_KEY]
            #not logged in
            resp = c.get(f"/users/{self.u1_id}/followers")

            self.assertEqual(resp.status_code, 302)

    def test_view_user_followings(self):
        """Can a user view another users followings?"""

        with self.client as c:
            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)
            u1_username = u1.username
            u2_username = u2.username
            u1.following.append(u2)
            u1.followers.append(u2)
            db.session.commit()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            #Logged in as user 1 view your own following page
            resp = c.get(f"/users/{self.u1_id}/following")

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn(u2_username, html)

            #Logged in as user 1 view user 2's following page
            resp = c.get(f"/users/{self.u2_id}/following")

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn(u1_username, html)

    def test_view_user_following_redirects_unauthorized_users(self):
        """Can an unauthorized visitor view a users followings?"""

        with self.client as c:
            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)
            u1_username = u1.username
            u2_username = u2.username
            u1.following.append(u2)
            u1.followers.append(u2)
            db.session.commit()

            with c.session_transaction() as sess:
                #log out user if logged in
                if sess.get(CURR_USER_KEY):
                    del sess[CURR_USER_KEY]
            #not logged in
            resp = c.get(f"/users/{self.u1_id}/following")

            self.assertEqual(resp.status_code, 302)


class UserAuthenticationViewsTestCase(TestCase):
    """Test views for routes having to do with User authentication ."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.u1_info = {"username": "testuser",
                        "email": "test@test.com",
                        "password": "testuser",
                        "image_url": ""}

        self.u2_info = {"username": "testuser2",
                        "email": "test2@test.com",
                        "password": "testuser2",
                        "image_url": ""}
        testuser = User.signup(**self.u1_info)
        db.session.commit()

        self.u1_info["id"] = testuser.id

    def test_user_register(self):
        with self.client as c:
            resp = c.get(f'/signup')
            self.assertEqual(resp.status_code, 200)

            resp = c.post(f'/signup', data=self.u2_info)
            self.assertEqual(resp.status_code, 302)
            u = User.query.filter_by(username="testuser2").first()
            self.assertIsNotNone(u)

    def test_user_login(self):
        with self.client as c:
            resp = c.get(f'/login')
            self.assertEqual(resp.status_code, 200)

            resp = c.post(f'/login', data=self.u1_info)
            self.assertEqual(resp.status_code, 302)
            with c.session_transaction() as sess:
                self.assertEqual(sess[CURR_USER_KEY], self.u1_info["id"])

    def test_user_logout(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_info["id"]

            #signed in as user 1
            resp = c.get(f'/logout')
            self.assertEqual(resp.status_code, 302)

            with c.session_transaction() as sess:
                self.assertIsNone(sess.get(CURR_USER_KEY))

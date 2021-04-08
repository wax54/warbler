"""User model tests."""

# run these tests like:
# python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

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


class UserModelTestCase(TestCase):
    """Test model for User."""

    def setUp(self):
        """Create test client, add sample data."""
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follow.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="www.someimage.com/1204194",
            header_image_url="www.someimage.com/131931",
            bio="Test Bio",
            location="Washington"
        )
        db.session.add(u)
        db.session.commit()

        self.assertEqual(u.email, "test@test.com")
        self.assertEqual(u.username, "testuser")
        self.assertEqual(u.bio, "Test Bio")
        self.assertEqual(u.password, "HASHED_PASSWORD")
        self.assertEqual(u.image_url, "www.someimage.com/1204194")
        self.assertEqual(u.header_image_url, "www.someimage.com/131931")
        self.assertEqual(u.location, "Washington")

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.following), 0)
        self.assertEqual(len(u.likes), 0)



    def test_user_repr(self):
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        db.session.add(u)
        db.session.commit()

        id = u.id
        self.assertEqual(
            u.__repr__(), f"<User #{id}: testuser, test@test.com>")

    def test_is_following(self):
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        u2 = User(
            email="test2@test2.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )
        #Not Following yet, simply existing
        self.assertFalse(u.is_following(u2))
        #Started Following
        u.following.append(u2)
        self.assertTrue(u.is_following(u2))

        #stopped following
        u.following.remove(u2)
        self.assertFalse(u.is_following(u2))

    def test_is_followed_by(self):
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        u2 = User(
            email="test2@test2.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )
        #Not Follower yet, simply existing
        self.assertFalse(u.is_followed_by(u2))
        #Started Following
        u.followers.append(u2)
        self.assertTrue(u.is_followed_by(u2))

        #stopped following
        u.followers.remove(u2)
        self.assertFalse(u.is_followed_by(u2))

    def test_update_from_serial(self):
        u = User(email="test@test.com",
                 username="testuser",
                 password="HASHED_PASSWORD",
                 image_url="www.someimage.com/1204194",
                 header_image_url="www.someimage.com/131931"
                 )

        serial_of_user = {
            "email": "test2@test.com",
            "username": "testuser2",
            "image_url": "",
            "header_image_url": "",
            "bio": "Test Bio",
            "location": "Washington"
        }

        u.update_from_serial(serial_of_user)
        db.session.add(u)
        db.session.commit()

        self.assertEqual(u.email, "test2@test.com")
        self.assertEqual(u.username, "testuser2")
        #if empty string is passed in, image_url defaults to default
        #if nothing is passed in, nothing happens
        #if something is passed in, it is updated
        self.assertEqual(u.image_url, User.image_url.default.arg)
        #same thing for the header image
        self.assertEqual(u.header_image_url, User.header_image_url.default.arg)
        self.assertEqual(u.bio, "Test Bio")
        self.assertEqual(u.location, "Washington")

    def test_duplicate_user_signup_failure(self):
        u_info = {
            "email": "test@test.com",
            "username": "testuser",
            "password": "PASSWORD",
            "image_url": "https://www.SomeUrl.com/images0138"
        }

        u = User.signup(**u_info)
        db.session.commit()
        another_u = User.signup(**u_info)
        #raises if email or username is not unique
        self.assertRaises(IntegrityError, db.session.commit)

    def test_no_username_signup_failure(self):
        u_info = {
            "email": "test@test.com",
            "username": "",
            "password": "PASSWORD",
            "image_url": "https://www.SomeUrl.com/images0138"
        }
        #testing signup without a username
        u = User.signup(**u_info)
        db.session.commit()

    def test_user_signup(self):
        u_info = {
            "email": "test@test.com",
            "username": "testuser",
            "password": "PASSWORD",
            "image_url": "https://www.SomeUrl.com/images0138"
        }
        u_without_image_url_info = {
            "email": "test2@test2.com",
            "username": "testuser2",
            "password": "PASSWORD",
            "image_url": None
        }

        u = User.signup(**u_info)
        db.session.commit()
        #A new user is created
        self.assertIsNotNone(u.id)
        self.assertEqual(u.username, u_info['username'])
        #Password is hashed
        self.assertNotEqual(u.password, u_info['password'])
        self.assertEqual(u.image_url, u_info['image_url'])

        #test user with None for an image_url input
        another_u = User.signup(**u_without_image_url_info)
        db.session.commit()
        self.assertEqual(another_u.username,
                         u_without_image_url_info['username'])
        self.assertEqual(another_u.image_url, User.image_url.default.arg)

    def test_user_authenticate(self):
        u_info = {
            "email": "test@test.com",
            "username": "testuser",
            "password": "PASSWORD",
            "image_url": "https://www.SomeUrl.com/images0138"
        }
        u_without_image_url_info = {
            "email": "test2@test2.com",
            "username": "testuser2",
            "password": "PASSWORD",
            "image_url": None
        }

        u = User.signup(**u_info)
        db.session.commit()

        # we a user back because we put in the correct credentials
        authenticated_u = User.authenticate(
            username=u_info['username'], password=u_info['password'])
        self.assertEqual(u, authenticated_u)

        # we get False back because we put in a username that doesn't exist
        authenticated_u = User.authenticate(
            username="someusername", password=u_info['password'])
        self.assertFalse(authenticated_u)

        # we get False back because we put in the wrong password
        authenticated_u = User.authenticate(
            username=u_info['username'], password="someotherpassword")
        self.assertFalse(authenticated_u)

        # we get False back because we put in the hashed password (which is then rehashed and does not match)
        authenticated_u = User.authenticate(
            username=u_info['username'], password=u.password)
        self.assertFalse(authenticated_u)

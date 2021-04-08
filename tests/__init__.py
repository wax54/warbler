#Batch test file
# Run FLASK_ENV=production python -m unittest tests from the root app to run all the tests in this directory

from tests.test_message_model import *
from tests.test_message_views import *
from tests.test_user_views import *
from tests.test_user_model import *

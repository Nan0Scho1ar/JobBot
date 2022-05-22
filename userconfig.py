import os

from Shared.helpers import Const


class UserConfig(Const):
    EMAIL = os.environ['EMAIL']
    PASSWORD = os.environ['PASSWORD']
    INDEED_API_KEY = os.environ['INDEED_API_KEY']

    class Path(Const):
        JSON_TAG_BLURBS = r'blurbs.json'
        DEFAULT_RESUME = os.environ['DEFAULT_RESUME']

    class Settings(Const):
        # Booleans
        USE_ALT_END_TAG = True
        USE_LONG_TEXT = False
        IS_DRY_RUN = False
        WILL_RELOAD_TAGS_AND_BLURBS = False

        MINIMUM_NUMBER_MATCHING_KEYWORDS = 1

    class Default(Const):
        EXPERIENCE = 2
        CITY = 'Vancouver'

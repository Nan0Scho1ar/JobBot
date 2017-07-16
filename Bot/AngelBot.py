from Bot.Robot import Robot, RobotConstants

# Selenium Imports
from selenium import webdriver, common
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from run import UserConfig
import json
import peewee
from models import Job

from helpers import Const
import re
from typing import Optional
import time


class AngelBot(Robot):
    def __init__(self, user_config: UserConfig, dry_run=False, reload_tags_blurbs=True):
        super().__init__(
            user_config=user_config,
            driver=RobotConstants.Driver.CHROME
        )

    def login(self):
        self.driver.get(AngelConstants.URL.LOGIN)
        element_email = self.driver.find_element(By.ID, AngelConstants.Id.LOGIN_EMAIL)
        element_email.send_keys(self.user_config.EMAIL)
        self.driver.find_element(By.ID, AngelConstants.Id.LOGIN_PASSWORD).send_keys(self.user_config.PASSWORD)
        element_email.submit()

    def gather(self, query_parameters):
        def extract_job_key(url: str) -> Optional[str]:
            last_part_of_url = url.rsplit('/', 1)[-1]
            match = re.match(AngelConstants.Regex.JOB_KEY_FROM_URL, last_part_of_url)
            if match:
                return match.group(1)
            return None

        assert self._is_authenticated()

        string_parameters = AngelBot._encode_parameters(query_parameters)
        self.driver.get(AngelConstants.URL.JOBS + string_parameters)

        # Check if any jobs have loaded
        WebDriverWait(self.driver, AngelConstants.PauseTime.JOBS_LOADED).until(
            EC.presence_of_element_located((By.XPATH, AngelConstants.XPath.JOB_LISTING_LINK))
        )
        self._scroll_infinitely()
        elements_list = self.driver.find_elements(By.XPATH, AngelConstants.XPath.JOB_LISTING_LINK)
        for element in elements_list:
            job_link = element.get_attribute('href')
            job_title = element.get_attribute('innerText')
            job_key = extract_job_key(job_link)
            if job_key is None:
                pass
            else:
                try:
                    Job.create(
                        key=job_key,
                        website=AngelConstants.WEBSITE_NAME,
                        link=job_link,
                        title=job_title
                    )
                except peewee.IntegrityError as e:
                    print(e)

    def apply(self):
        jobs = Job\
            .select()\
            .where(
            (Job.applied == False) &
            (Job.good_fit == True) &
            (Job.website == AngelConstants.WEBSITE_NAME) &
            (Job.attempted == False)
        )

        for count, job in enumerate(jobs):
            if count > RobotConstants.MAX_COUNT_APPLICATION_ATTEMPTS:
                print(RobotConstants.String.MAX_ATTEMPTS_REACHED)
                break

            self._apply_single_job(job)

    def _apply_single_job(self, job: Job):
        self.driver.get(job.link)
        self.attempt_application(job)
        self._get_job_information(job)

        user_note = self.application_builder.generate_message(
            company=job.company,
            description=job.description
        )
        if user_note is not None:
            try:
                apply_now_element = self.driver.find_element(By.CSS_SELECTOR, AngelConstants.CSSSelector.APPLY_NOW)
                apply_now_element.click()

                job.message = user_note
                self.driver.find_element(By.XPATH, AngelConstants.XPath.USER_NOTE).send_keys(user_note)

                if not self.user_config.Settings.DRY_RUN:
                    self.driver.find_element(By.XPATH, AngelConstants.XPath.APPLY).click()

                self.successful_application(job, dry_run=self.user_config.Settings.DRY_RUN)

            except common.exceptions.NoSuchElementException as e:
                job.error = str(e)
        else:
            job.error = RobotConstants.String.NOT_ENOUGH_KEYWORD_MATCHES
            self.failed_application(job)

        job.save()

    def _get_job_information(self, job: Job):
        element_job_description = self.driver.find_element(By.XPATH, AngelConstants.XPath.JOB_DESCRIPTION)
        element_job_company = self.driver.find_element(By.XPATH, AngelConstants.XPath.JOB_COMPANY)
        job.description = element_job_description.text
        job.company = element_job_company.get_attribute('text').strip()

    def _is_authenticated(self) -> bool:
        try:
            self.driver.find_element(By.XPATH, AngelConstants.XPath.LOGGED_IN)
            return True
        except common.exceptions.NoSuchElementException as e:
            return False

    @staticmethod
    def _encode_parameters(dict_parameters: dict) -> str:
        """
        Function to encode the query parameters how Angel.co likes them
        :param dict_parameters:
        :return:
        """
        dict_copy = dict_parameters.copy()
        string_parameters = json.dumps(dict_copy)
        return string_parameters.\
            replace(',','%2C').\
            replace(':','%3A').\
            replace('[','%5B').\
            replace(']','%5D')

    def _scroll_infinitely(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(AngelConstants.PauseTime.SCROLL)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height


class AngelConstants(Const):
    WEBSITE_NAME = 'Angel'

    class URL(Const):
        BASE = r'https://angel.co/'
        LOGIN = r'https://angel.co/login'
        JOBS = r'https://angel.co/jobs#find/f!'

    class Id(Const):
        LOGIN_EMAIL = 'user_email'
        LOGIN_PASSWORD = 'user_password'

    class XPath(Const):
        LOGGED_IN = r"//div[string(@data-user_id)]"
        JOB_LISTING_LINK = r"//div[@class='listing-row']//div[@class='title']/a"
        # Get these when on indiviual company page
        JOB_DESCRIPTION = r"//div[contains(@class,'job-description')]"
        JOB_COMPANY = r"//a[@class='c-navbar-item'][@data-bounds_target='.hero']"
        # There's 4 of these on each page, select first element
        USER_NOTE = r"//textarea[contains(@class,'user-note-textarea')]"
        APPLY = r"//button[contains(@class,'js-apply-button')]"

    class CSSSelector(Const):
        APPLY_NOW = r"div.buttons.js-apply.applicant-flow-dropdown > a"

    class Regex(Const):
        JOB_KEY_FROM_URL = re.compile('(\d+)-')

    class PauseTime(Const):
        SCROLL = 1
        JOBS_LOADED = 7


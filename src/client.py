import logging
import time
import traceback
from datetime import datetime
from pathlib import Path

import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from src.config import Config
from src.exceptions import (
    CloudflareChallengeError,
    ImageUploadError,
    LoginFailedError,
    ModelSelectionError,
    ResponseTimeoutError,
)


class ChatGPTWebClient:
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.driver = self._init_driver()
        self.wait = WebDriverWait(self.driver, self.config.timeout)

    def _init_driver(self) -> webdriver.Chrome:
        chrome_options = Options()
        if self.config.headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1920,1080")

        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--lang=en-US")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument(f"user-agent={UserAgent.random}")

        driver = uc.Chrome(options=chrome_options)
        driver.set_page_load_timeout(self.config.timeout)
        return driver

    def access_homepage(self) -> None:
        self.driver.get("https://chat.openai.com/")
        self.logger.info("Accessing ChatGPT homepage...")

    def login(self) -> None:
        if self.config.email is None or self.config.password is None:
            self.logger.warning("Email or password not provided. Skipping login.")
            return

        for attempt in range(1, self.config.max_login_retries + 1):
            self.logger.info(
                "Login attempt %d/%d...", attempt, self.config.max_login_retries
            )
            try:
                self._perform_login_flow(self.config.email, self.config.password)
                self.logger.info("Successfully logged in on attempt %d.", attempt)
                return
            except Exception as e:
                self.logger.warning("Login attempt %d failed: %s", attempt, e)
                self._capture_state(f"login_failure_attempt_{attempt}")
                if attempt == self.config.max_login_retries:
                    self._handle_error(
                        "All login attempts failed.",
                        e,
                        raise_exception=True,
                        exception_class=LoginFailedError,
                    )
                else:
                    time.sleep(3)

    def select_model(self, model_name: str) -> None:
        self.logger.info("Selecting model: %s", model_name)
        model_menu_selectors = [
            (By.CSS_SELECTOR, "button.model-selector-button"),
            (By.XPATH, "//button[contains(@class,'model-menu')]"),
        ]
        self._click_first_available(model_menu_selectors, "model menu button")

        time.sleep(1)  # メニューが開くのを待つ

        model_option_selectors = [
            (
                By.XPATH,
                f"//div[contains(@class,'model-option') and contains(text(),'{model_name}')]",  # noqa: E501
            ),
            (By.XPATH, f"//button[contains(text(),'{model_name}')]"),
        ]
        try:
            self._click_first_available(
                model_option_selectors, f"model option '{model_name}'"
            )
            self.logger.info("Model '%s' selected.", model_name)
        except Exception as e:
            self._handle_error(
                f"Failed to select model {model_name}.",
                e,
                raise_exception=True,
                exception_class=ModelSelectionError,
            )

        time.sleep(2)  # モデルが適用されるのを待つ

    def send_message(self, message: str) -> None:
        self._wait_and_fill(
            (By.ID, "prompt-textarea"), message, clear_before=True, send_enter=True
        )
        self.logger.info("Sending message: %s", message)

    def send_image(self, image_path: str) -> None:
        self.logger.info("Sending image: %s", image_path)
        if not Path(image_path).is_file():
            self._handle_error(
                f"Image file not found: {image_path}",
                None,
                raise_exception=True,
                exception_class=ImageUploadError,
            )

        attach_button_selectors = [
            (By.CSS_SELECTOR, "button.attach-image"),
            (By.XPATH, "//button[contains(@class,'attach-image')]"),
        ]
        try:
            self._click_first_available(attach_button_selectors, "attach image button")
        except Exception:
            self.logger.info("No attach image button clicked.")

        time.sleep(1)

        file_input_selectors = [
            (By.CSS_SELECTOR, "input[type='file']"),
        ]
        file_input = self._find_first_present(
            file_input_selectors, "file input for image"
        )
        if not file_input:
            self._handle_error(
                "No file input found for image upload.",
                None,
                raise_exception=True,
                exception_class=ImageUploadError,
            )

        file_input.send_keys(str(Path(image_path).resolve()))
        self.logger.info("Image file path sent to file input.")

        time.sleep(3)  # プレビューなどが表示されるのを待機x

    def wait_for_response(self) -> str:
        self.logger.info(
            "Waiting for ChatGPT response to stabilize (max %d s)...",
            self.config.response_max_wait,
        )
        start = time.time()
        last_response_text = ""
        stable_start = None

        while True:
            if time.time() - start > self.config.response_max_wait:
                self._handle_error(
                    "Timed out waiting for response to stabilize.",
                    None,
                    raise_exception=True,
                    exception_class=ResponseTimeoutError,
                )

            response_blocks = self.driver.find_elements(
                By.CSS_SELECTOR, ".markdown.prose p"
            )
            current_text = "\n".join(
                [el.text for el in response_blocks if el.text.strip()]
            )

            if current_text and current_text != last_response_text:
                last_response_text = current_text
                stable_start = time.time()
                self.logger.debug("Response updated, checking again for stability...")
            else:
                # 一定時間変化しなければ終了
                if (
                    last_response_text
                    and stable_start
                    and (time.time() - stable_start)
                    >= self.config.response_stable_interval
                ):
                    self.logger.info("Response finish.")
                    break
                time.sleep(1)

        return last_response_text.strip()

    def close(self) -> None:
        self.logger.info("Closing the browser.")
        self.driver.quit()

    def _perform_login_flow(self, email: str, password: str) -> None:
        if self._is_cloudflare_challenge():
            self._handle_error(
                "Cloudflare challenge detected at homepage.",
                None,
                raise_exception=True,
                exception_class=CloudflareChallengeError,
            )

        login_button_selectors = [
            (By.XPATH, "//button[contains(text(),'Log in')]"),
            (By.CSS_SELECTOR, "button[data-test='login']"),
        ]
        self._click_first_available(login_button_selectors, "login button")

        self._wait_and_fill((By.CSS_SELECTOR, "input[type='email']"), email)
        self._wait_and_click((By.CSS_SELECTOR, "button[type='submit']"))

        self._wait_and_fill((By.CSS_SELECTOR, "input[type='password']"), password)
        self._wait_and_click((By.CSS_SELECTOR, "button[type='submit']"))

        self.wait.until(ec.presence_of_element_located((By.TAG_NAME, "textarea")))

    def _is_cloudflare_challenge(self) -> bool:
        page_source = self.driver.page_source.lower()
        if "cloudflare" in page_source and "checking your browser" in page_source:
            self.logger.warning("Cloudflare challenge detected in the DOM.")
            return True
        return False

    def _wait_and_fill(
        self,
        locator: tuple[str, str],
        value: str,
        clear_before: bool = True,
        send_enter: bool = False,
    ) -> None:
        try:
            element = self.wait.until(ec.presence_of_element_located(locator))
            if clear_before:
                element.clear()
            element.send_keys(value)
            if send_enter:
                element.send_keys(Keys.ENTER)
        except TimeoutException as e:
            self._handle_error(
                f"Element {locator} not found for filling.", e, raise_exception=True
            )

    def _wait_and_click(self, locator: tuple[str, str]) -> None:
        try:
            element = self.wait.until(ec.element_to_be_clickable(locator))
            element.click()
        except TimeoutException as e:
            self._handle_error(
                f"Element {locator} not clickable.", e, raise_exception=True
            )

    def _click_first_available(
        self, selectors: list[tuple[str, str]], description: str
    ) -> None:
        for by_, sel in selectors:
            try:
                element = self.wait.until(ec.element_to_be_clickable((by_, sel)))
                element.click()
                return
            except TimeoutException:
                pass
        self._handle_error(
            f"No valid selector found for {description}.", None, raise_exception=True
        )

    def _find_first_present(self, selectors: list[tuple[str, str]], description: str):
        for by_, sel in selectors:
            try:
                element = self.wait.until(ec.presence_of_element_located((by_, sel)))
                return element
            except TimeoutException:
                continue
        self.logger.warning("No valid element found for %s.", description)
        return None

    def _handle_error(
        self,
        msg: str,
        exception: Exception | None,
        raise_exception: bool = True,
        exception_class=Exception,
    ) -> None:
        self.logger.error(msg)
        if exception:
            self.logger.error("Exception: %s", exception)
            traceback.print_exc()

        self._capture_state("error")

        if raise_exception:
            if exception:
                raise exception_class(f"{msg} - Original Exception: {exception}")
            else:
                raise exception_class(msg)

    def _capture_state(self, prefix: str) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = self.config.log_dir / f"{prefix}_screenshot_{timestamp}.png"
        dom_path = self.config.log_dir / f"{prefix}_dom_{timestamp}.html"

        self.driver.save_screenshot(str(screenshot_path))
        with open(dom_path, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

        self.logger.info("Captured screenshot: %s", screenshot_path)
        self.logger.info("Captured DOM dump: %s", dom_path)

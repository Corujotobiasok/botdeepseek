from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class WebController:
    def __init__(self):
        self.driver = None
        self._init_driver()

    def _init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--mute-audio")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(15)
        except Exception as e:
            print(f"Error al iniciar navegador: {e}")

    def play_youtube(self, query):
        if not self.driver:
            return False
        try:
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            self.driver.get(search_url)
            wait = WebDriverWait(self.driver, 10)
            first_video = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "ytd-video-renderer:first-child"))
            )
            first_video.click()
            self._dismiss_popups()
            fullscreen_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-fullscreen-button"))
            )
            fullscreen_btn.click()
            return True
        except Exception as e:
            print(f"Error al reproducir YouTube: {e}")
            return False

    def search_web(self, query):
        if not self.driver:
            return False
        try:
            self.driver.get(f"https://www.google.com/search?q={query.replace(' ', '+')}")
            self._dismiss_popups()
            return True
        except:
            return False

    def _dismiss_popups(self):
        try:
            WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Aceptar') or contains(text(), 'Acepto')]"))
            ).click()
        except:
            pass

    def close(self):
        if self.driver:
            self.driver.quit()
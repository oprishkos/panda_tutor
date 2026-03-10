import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import pytest

@pytest.fixture
def driver():
    driver = webdriver.Edge()
    driver.get("http://10.160.72.116:5000/auth/register")
    yield driver
    driver.quit()

def test_valid_values(driver):
    driver.find_element("id", "email").send_keys("proverka@mail.ru")
    time.sleep(2)
    driver.find_element("id", "password").send_keys("192837465")
    time.sleep(2)
    driver.find_element("id", "password_confirm").send_keys("192837465")
    time.sleep(2)
    role_select_el = driver.find_element(By.ID, "role")
    role_select = Select(role_select_el)
    role_select.select_by_visible_text("Репетитор")
    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, ".btn.btn-primary").click()
    time.sleep(2)

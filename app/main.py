import logging
import os
import pandas as pd
import requests
import subprocess

from datetime import datetime
from playwright.sync_api import sync_playwright


LETTERBOXD_USERNAME = os.getenv("LETTERBOXD_USERNAME")
LETTERBOXD_PASSWORD = os.getenv("LETTERBOXD_PASSWORD")
TRAKT_USERNAME = os.getenv("TRAKT_USERNAME")
FILTER_CSV = os.getenv("FILTER_CSV", f"{datetime.now().year}-01-01")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            logging.error(f"Failed to send message to Telegram: {response.text}")
    except Exception as e:
        logging.error(f"Error sending message to Telegram: {str(e)}")


def generate_csv(trakt_username):
    command = ["npx", "trakt-to-letterboxd", "-u", trakt_username, "-f", "file.csv"]
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    if result.stderr:
        print("stderr:", result.stderr)
        print("Failed to generate CSV file")
        return None
    else:
        print("stdout:", result.stdout)
        print("Successfully generated CSV file")
        return 0


def filter_csv_by_watched_date(csv_file, filter_date):
    data = pd.read_csv(csv_file)

    data["WatchedDate"] = pd.to_datetime(data["WatchedDate"], format="%Y-%m-%d")
    filtered_data = data.loc[(data["WatchedDate"] >= filter_date)]

    filtered_data.to_csv(csv_file, index=False)


def upload_csv(csv_file):
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True, slow_mo=500)
            page = browser.new_page()
            page.goto("https://letterboxd.com/import")
            page.wait_for_load_state("domcontentloaded")

            # Enter username/password
            page.locator('//*[@id="field-username"]').fill(LETTERBOXD_USERNAME)
            page.locator('//*[@id="field-password"]').fill(LETTERBOXD_PASSWORD)

            # Press SIGN IN button
            signin_button = page.locator(
                '//*[@id="html"]/body/div[1]/div/form/div/div[3]/button'
            )
            signin_button.wait_for(state="visible", timeout=5000)
            logging.info(f"Found sign in button: {signin_button}")
            signin_button.click()
            page.wait_for_load_state("domcontentloaded")

            # Accept cookies
            logging.info("Click cookies concent button...")
            concent_button = page.locator(
                '.fc-cta-consent'
            )
            concent_button.wait_for(state="visible", timeout=5000)
            logging.info(f"Found consent button: {concent_button}")
            concent_button.click()
            page.wait_for_load_state("domcontentloaded")

            # Import file
            import_item = page.locator('//*[@id="upload-imdb-import"]')
            import_item.wait_for(state="hidden", timeout=5000)
            logging.info(f"Found import item: {import_item}")
            import_item.set_input_files(csv_file)

            # Wait for matching to complete
            matching_result = page.wait_for_selector(
                '#diary-importer-identifier:has-text("Matching complete")'
            )
            logging.info(matching_result.inner_text())

            # Click import link
            import_link = page.locator('//*[@id="content"]/div/div[1]/a[2]')
            import_link.wait_for(state="visible", timeout=5000)
            logging.info(f"Found import link: {import_link}")
            import_link.click()

            # Wait for import to complete
            page.wait_for_selector("#content > div > div.body-text.-centered.profile-link")

            # Print import result
            import_result = page.locator('//*[@id="diary-importer-identifier"]/p')
            import_result.wait_for(state="visible", timeout=5000)
            logging.info(import_result.inner_text())
    except Exception as e:
        print(f"Error: {e}")
        send_telegram_message("Failed to export to Letterboxd")


def main():
    generate_csv(TRAKT_USERNAME)
    if not generate_csv:
        return 1
    if FILTER_CSV:
        filter_csv_by_watched_date(
            os.path.join(os.path.dirname(__file__), "file.csv"), FILTER_CSV
        )
    upload_csv(os.path.join(os.path.dirname(__file__), "file.csv"))


main()

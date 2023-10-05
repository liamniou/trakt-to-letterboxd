import os
import pandas as pd
import subprocess

from playwright.sync_api import sync_playwright

LETTERBOXD_USERNAME = os.getenv("LETTERBOXD_USERNAME")
LETTERBOXD_PASSWORD = os.getenv("LETTERBOXD_PASSWORD")
TRAKT_USERNAME = os.getenv("TRAKT_USERNAME")
FILTER_CSV = os.getenv("FILTER_CSV", "2023-01-01")


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
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True, slow_mo=500)
        page = browser.new_page()
        page.goto("https://letterboxd.com/")

        # Accept cookies
        concent_button = page.locator(
            '//*[@id="html"]/body/div[7]/div[2]/div[1]/div[2]/div[2]/button[1]'
        )
        concent_button.wait_for(state="visible", timeout=5000)
        print(f"Found consent button: {concent_button}")
        concent_button.click()

        # Click SIGN IN link
        signin_link = page.locator('//*[@id="header"]/section/div/div/nav/ul/li[1]/a')
        signin_link.wait_for(state="visible", timeout=5000)
        print(f"Found sign in link: {signin_link}")
        signin_link.click()

        # Enter username/password
        page.locator('//*[@id="username"]').fill(LETTERBOXD_USERNAME)
        page.locator('//*[@id="password"]').fill(LETTERBOXD_PASSWORD)

        # Press SIGN IN button
        signin_button = page.locator(
            '//*[@id="signin"]/fieldset/div/div[4]/div[1]/input'
        )
        signin_button.wait_for(state="visible", timeout=5000)
        print(f"Found sign in button: {signin_button}")
        signin_button.click()

        page.wait_for_selector("#add-new-button")

        page.goto("https://letterboxd.com/import")

        # Import file
        import_item = page.locator('//*[@id="upload-imdb-import"]')
        import_item.wait_for(state="hidden", timeout=5000)
        print(f"Found import item: {import_item}")
        import_item.set_input_files(csv_file)

        # Wait for matching to complete
        matching_result = page.wait_for_selector(
            '#diary-importer-identifier:has-text("Matching complete")'
        )
        print(matching_result.inner_text())

        # Click import link
        import_link = page.locator('//*[@id="content"]/div/div[1]/a[2]')
        import_link.wait_for(state="visible", timeout=5000)
        print(f"Found import link: {import_link}")
        import_link.click()

        # Wait for import to complete
        page.wait_for_selector("#content > div > div.body-text.-centered.profile-link")

        # Print import result
        import_result = page.locator('//*[@id="diary-importer-identifier"]/p')
        import_result.wait_for(state="visible", timeout=5000)
        print(import_result.inner_text())


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

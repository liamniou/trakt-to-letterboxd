# Description
The tool uses [trakt-to-letterboxd](https://github.com/bbeesley/trakt-to-letterboxd) to generate CSV file with your watched movies that is later imported to your Letterboxd profile.

Letterboxd doesn't have public API, so the tool uses [Playwright](https://playwright.dev) to interact with the website.

# Usage
1. Create `.env` file and provide the values for the ENV variables:
- LETTERBOXD_USERNAME=...
- LETTERBOXD_PASSWORD=...
- TRAKT_USERNAME=...
2. Start the container:
> docker-compose up -d

# Environmental variables
| Variable            | Description                                                       | Default      |
| ------------------- | ----------------------------------------------------------------- | ------------ |
| LETTERBOXD_USERNAME | Your Letterboxd username or email                                 | -            |
| LETTERBOXD_PASSWORD | Letterboxd password                                               | -            |
| TRAKT_USERNAME      | Your Trakt username                                               | -            |
| FILTER_CSV          | String (in format "%Y-%m-%d") used to filter CSV by 'WatchedDate' | "2023-01-01" |

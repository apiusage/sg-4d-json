# SG 4D Scraper

This repository scrapes Singapore 4D results every 6 hours using GitHub Actions and saves the data as `4d.json`.

## Setup

1. Clone this repo.
2. Generate a GitHub Personal Access Token (PAT) with `repo` scope:
   - https://github.com/settings/tokens
3. Go to your repo's Settings → Secrets and variables → Actions, create a new secret:
   - Name: `PAT`
   - Value: your token
4. The GitHub Action `scrape.yml` will run every 6 hours to update `4d.json`.

## Usage

You can access the latest 4D results JSON file via GitHub Pages or raw URL:

```
https://your-username.github.io/your-repo-name/4d.json
```

Replace with your GitHub username and repo name.

## Run Locally

```
npm install
npm run scrape
```

## License

MIT

# How to Add Google Sheets Credentials

The pipeline can write directly to Google Sheets. This guide walks you through
setting up OAuth credentials.

## Step 1: Create a Google Cloud project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "Keyboard Shopping Agent")
3. Enable the **Google Sheets API**:
   - Go to APIs & Services > Library
   - Search for "Google Sheets API"
   - Click Enable

## Step 2: Create OAuth credentials

1. Go to APIs & Services > Credentials
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the consent screen:
   - User type: External (or Internal if using Workspace)
   - Add your email as a test user
4. Application type: Desktop app
5. Download the JSON file
6. Rename it to `credentials.json` and place it in the repo root

## Step 3: Install Google extras

```bash
pip install -e ".[google]"
```

## Step 4: Run with Google Sheets output

```bash
python -m scripts.run_pipeline --zip 11201 --out google_sheets
```

On first run, a browser window will open for OAuth consent. After authorizing,
a `token.json` file is created (git-ignored) for future runs.

## Step 5: Write to an existing sheet

```bash
python -m scripts.run_pipeline --zip 11201 --out google_sheets --sheet-id YOUR_SHEET_ID
```

The sheet ID is the long string in the Google Sheets URL:
`https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`

## Security notes

- `credentials.json` and `token.json` are git-ignored by default
- Never commit these files to the repository
- If you accidentally commit them, revoke the credentials immediately in
  Google Cloud Console

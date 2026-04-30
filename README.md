# votega.org-dev
Test/Dev Site for votega.org

## Refreshing Congress member data

This repo uses a GitHub Actions workflow to generate `assets/data/current-members.json` from the Congress.gov API.

To refresh the data manually:

1. Go to the repository on GitHub.
2. Open the `Actions` tab.
3. Select the workflow `Update Congress.gov current members data`.
4. Click `Run workflow`.

The workflow uses the `CONGRESS_API_KEY` secret, so make sure that secret is configured in the repository settings before running.

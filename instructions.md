# Agent Instructions for votega.org-TEST Project

## Scope
These instructions apply only to the votega.org-TEST project (a static GitHub Pages site using Congress.gov API data). They do not affect other projects or general coding tasks.

## Core Principles
- **API Key Security First**: Never expose API keys in client-side code. Always use server-side or build-time generation (e.g., GitHub Actions) to fetch data and serve static JSON. If live API calls are needed, implement a proxy or backend.
- **Static Site Best Practices**: For GitHub Pages sites, prefer prebuilt data over dynamic fetches to avoid CORS issues and key exposure. Use workflows to generate JSON files at build time.
- **Congress.gov API Handling**: Map fields correctly (e.g., `partyHistory[0].partyName` for party, `terms.item[0].chamber` for chamber). Always filter client-side for state/chamber since the API doesn't support direct chamber queries. Include user-friendly notes about API limitations (e.g., no contact info).
- **Error Handling**: Provide clear, actionable error messages for users (e.g., "Data file missing—run the workflow"). Log errors to console for debugging.
- **Environment Awareness**: Detect GitHub Pages paths (e.g., `/votega.org-TEST/`) and adjust redirects accordingly.
- **GitHub Actions**: Use secrets for sensitive data. Schedule workflows for daily updates. Include fetch-depth: 0 only if needed for git history.

## Coding Patterns
- **JavaScript**: Use async/await for fetches. Prefer `fetch()` over XMLHttpRequest. Structure scripts with constants at top (e.g., `DATA_URL`).
- **HTML**: Use semantic elements. Include fallback links (e.g., back to search page). Embed scripts inline for simplicity in static sites.
- **Python Scripts**: For data generation, use urllib for requests, handle pagination with loops, and output clean JSON with metadata (e.g., updatedAt, count).
- **Workflows**: Opt into latest Node.js versions to avoid deprecation warnings. Use ubuntu-latest runners.

## Project-Specific Conventions
- **File Structure**: Keep data in `assets/data/`, scripts in `assets/scripts/`, and workflows in `.github/workflows/`.
- **Data Format**: Congress member JSON should include `bioguideId`, `name`, `partyName`, `state`, `terms.item[]`, `depiction.imageUrl`.
- **User Experience**: Show loading states, handle empty data gracefully, and explain API limitations in UI.
- **Version Control**: Commit generated files (e.g., JSON) back to repo via workflows, but never commit secrets.

## Enforcement
- Always check for API key exposure before suggesting code changes.
- If proposing live API calls, suggest alternatives first.
- For new features, verify against Congress.gov API docs and test with sample data.
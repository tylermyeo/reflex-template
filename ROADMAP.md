# CMS Pages → Reflex Site Roadmap (Beginner‑Friendly)

This plan gets a basic version live using your Notion CSV export, a manual CSV→JSON step, and simple Reflex pages. We’ll use the Slug column for routes. You already have GitHub and Railway set up, so we’ll keep using them.

## Overview
- Data source: Notion database (exported as CSV → converted to JSON)
- File used by the app: `myapp/data/cms_pages.json`
- Routing: Use `Slug` (each row becomes a page at `/<slug>`)
- Goal of v1: Proof‑of‑concept — load JSON, generate simple pages, verify locally, then ensure it works on Railway
- Later: Improve page template design, then consider automation with n8n (not needed for v1)

## Phase 1 — Prepare Data (Manual)
1) Export CSV from Notion (table view → ••• → Export → CSV).
2) Convert CSV → JSON using any “CSV to JSON” converter.
3) Save the result as `myapp/data/cms_pages.json`.
4) Sanity checks (recommended):
   - Every published row has a unique `Slug` (e.g., `creative-cloud-all-apps-pricing-suomi`).
   - Rows you want live have `Status` = "Published" (and optionally `Is Indexable` = "Yes").
   - If the first header looks odd (BOM), open CSV in Google Sheets and re‑export.

Suggested field mapping we’ll use in the app:
- slug: `Slug`
- title: `Page Title`
- published: `Status` == "Published" (and optionally `Is Indexable` == "Yes")
- content: `Intro Paragraph` (optionally append `FAQ` later)
- price info: `Latest Price ($)`, `Latest Price Currency`, `Period`
- meta: `SEO Meta Title`, `SEO Meta Description`
- useful extras: `Last Page Update`, `Last Price Update`, `Page ID`, `Canonical Path`

## Phase 2 — Local Proof‑of‑Concept
Goal: Load `cms_pages.json` and render very basic pages for each published row using `Slug` as the route.
1) Add a simple page template that shows: Title, Intro Paragraph, and (optionally) price.
2) For each published row, register a page at `/<slug>`.
3) Add a quick index page that lists all published slugs as links (helps testing).
4) Run locally and test:
   - Start the app
   - Open the index page, click into a few generated routes
   - Confirm: content appears; unknown paths show your 404 page

Keep design minimal here — the goal is to prove the data→route→render path works.

## Phase 3 — Make It Reliable
- Filtering: Only generate routes for rows where `Status` == "Published" (and optionally `Is Indexable` == "Yes").
- Validation: Skip rows missing `Slug` or `Page Title`.
- Fallbacks: If `Intro Paragraph` is empty, show a friendly placeholder; hide price if missing.
- Errors: Don’t let a bad row crash the build — skip and log it.

## Phase 4 — Improve the Page Template
- Layout: Use your existing design system components for headings/body/sections.
- Content: Add optional `FAQ` under the main copy.
- SEO: If present, set page title/description from `SEO Meta Title`/`SEO Meta Description`.
- Navigation: Keep or improve the “All pages” list for discovery/testing.

## Phase 5 — Version Control (GitHub already set up)
- Keep `myapp/data/cms_pages.json` in the repo so Railway builds use the same data.
- Commit changes as you refine the template and JSON.

## Phase 6 — Deploy / Verify on Railway (already live)
- Push to GitHub; Railway will redeploy.
- After deploy, open the Railway URL and test:
  - Homepage loads
  - Index page lists all published slugs
  - A few slug pages render correctly
  - 404 works for nonsense routes
- If something differs from local, re‑check the JSON path (`myapp/data/cms_pages.json`) and filters.

## Phase 7 — Manual Content Update Loop (simple + reliable)
When content changes in Notion:
1) Export CSV → Convert to JSON → replace `myapp/data/cms_pages.json`.
2) Test locally.
3) Commit and push → Railway redeploys.

This gives you a dependable workflow without automation while you refine the template.

## Later — Automation Idea (n8n)
- Build a scheduled flow: Notion Query → transform to the same JSON shape → update `cms_pages.json` in the repo or storage → trigger deploy.
- Keep the schema identical so the app code doesn’t change.

## Acceptance Checklist for v1
- JSON exists at `myapp/data/cms_pages.json` and contains the fields above
- Local dev loads the JSON without errors
- Pages generate at `/<slug>` for published rows
- Title + Intro Paragraph render; 404 works
- GitHub push triggers Railway deploy; live site matches local

That’s it — once this loop feels stable, start polishing the page UI in Phase 4.


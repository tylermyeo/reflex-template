# SOP: Adding a New Product and Finding Its Selectors

Use this guide when you add a new product to the PriceDuck Products DB and need to fill in the CSS selectors so the scraper can extract the price (and optionally currency, period, plan name).

---

## 1. Add the product in Notion

1. Open your **Products** database in Notion.
2. Create a new page (row).
3. Fill in:
   - **Product Name** — e.g. "ChatGPT Plus", "Notion Personal"
   - **Product URL** — the full URL of the pricing page (e.g. `https://openai.com/chatgpt/pricing`)

Leave the selector fields and **Rendering** empty for now; you’ll fill them in the next steps.

---

## 2. Open the pricing page and decide: static or JS?

1. Open the **Product URL** in Chrome.
2. **Is the price visible as soon as the page loads?**
   - **Yes** → In Notion, set **Rendering** to **static**.
   - **No** (price appears after a moment, or after scrolling) → Set **Rendering** to **js**.

The scraper uses **static** for simple pages (faster) and **js** for pages that need a real browser (Playwright) to render the price.

---

## 3. Find the price selector (required)

You need a **CSS selector** that points to the **single element that contains the price text** (e.g. `$20`, `20`, or `19.99`). That element’s text is what the scraper will use.

### Option A: Chrome DevTools (right‑click → Inspect)

1. On the pricing page, **right‑click the price number** (not “/month” or the plan name) → **Inspect**.
2. In the **Elements** panel, the node that contains the price will be highlighted.
3. **Right‑click that node** → **Copy** → **Copy selector**.
4. Paste into Notion **Selector Price**.

Chrome’s selector is often long (e.g. `#app > div > main > section > div:nth-child(2) > span`). You can shorten it if you like (e.g. keep a unique class or ID), but **the selector must still match the element that has the price text**. If you’re unsure, use the full selector first.

### Option B: SelectorGadget (often easier)

1. Install the [SelectorGadget](https://selectorgadget.com/) Chrome extension or use the bookmarklet.
2. On the pricing page, **click the price**. SelectorGadget will highlight elements that match.
3. If it highlights too much (e.g. the whole card), **click the extra highlighted parts** to exclude them (they turn red) until **only the price element** is green.
4. Copy the selector shown (e.g. `.price-amount` or `span.text-mkt-h2`) and paste into Notion **Selector Price**.

**Important:** The selector must target the **element whose text is the price**. If you target a parent that has no direct text, the scraper will get an empty value. In DevTools, the correct node is the one whose text in the Elements panel is the number (or “$20” etc.).

---

## 4. Optional: currency, period, plan name

If you want the scraper to also extract currency, period, or plan name:

| Notion property       | What to find |
|-----------------------|--------------|
| **Selector Currency** | Element with `$`, `USD`, `€`, etc. |
| **Selector Period**   | Element with `/ month`, `Monthly`, `per year`, etc. |
| **Selector Plan Name**| Element with the tier name (e.g. `Plus`, `Pro`) |

Use the same method (DevTools or SelectorGadget): right‑click the text → Inspect → Copy selector, or use SelectorGadget and copy the suggested selector. Paste into the matching Notion property. You can leave any of these blank if you don’t need them.

---

## 5. Regions: do you need to set anything?

**Short answer:** No. The scraper is ready to run with just Product Name, Product URL, Rendering, and **Selector Price**. It will scrape the page once and push one row to Scraped Pricing (the price you see on that URL). It does **not** need region settings to run.

**When you *do* want multiple regions:** Some sites let you switch region via a dropdown, a button, or a URL (e.g. `?country=UK`). In that case you can optionally fill these Notion properties so the scraper visits each region and records a separate row per region:

| Notion property | Type | What to set |
|-----------------|------|-------------|
| **Region Switcher Selector** | Rich Text | CSS selector for the dropdown/button that opens the region menu. Leave empty if the site has no visible switcher. |
| **Region Switcher Type** | Select | `dropdown` or `button` (scraper will click it and then click the region), or `url-param` (scraper will build a URL per region), or `none` (default). |
| **Available Regions** | Rich Text | Comma-separated list of region codes to scrape, e.g. `US, UK, EU` or `US, CA, GB`. Only used when Type is not `none`. |
| **Region URL Pattern** | Rich Text | For `url-param` only: template like `?country={{REGION}}` or `&region={{REGION}}`. The scraper replaces `{{REGION}}` with each value from Available Regions. |

If **Region Switcher Type** is `none` or **Available Regions** is empty, the scraper simply scrapes the Product URL once and does not try to change regions.

**If the site no longer has a region selector:** Many sites show one price based on your location (or remove the switcher). In that case there is no way for the scraper to “switch” region—it can only scrape whatever the page shows (one region). To get other regions you’d need the site to expose them (e.g. different URLs per country or a visible dropdown). If the switcher disappears, leave region fields empty and use the scraper for the default region only.

---

## 6. Save and run the scraper

1. Save the Notion page. The scraper only runs for products where **Selector Price** is not empty.
2. From the project root, run:
   ```bash
   python -m scrapers.main_scraper
   ```
3. Check the **Scraped Pricing** database for a new row with the product name and the extracted price (and a **Region** value if you configured multi-region).

---

## Quick checklist

- [ ] Product added in Notion with **Product Name** and **Product URL**
- [ ] **Rendering** set to **static** or **js** (see step 2)
- [ ] **Selector Price** filled with a selector that targets the element containing the price number
- [ ] (Optional) **Selector Currency**, **Selector Period**, **Selector Plan Name** filled if needed
- [ ] (Optional) Region switcher fields filled only if the site has a visible switcher or URL-based regions (see step 5)
- [ ] Run `python -m scrapers.main_scraper` and confirm a row in Scraped Pricing

---

## Troubleshooting

**Scraper skips the product**  
- The scraper only runs for products that have **Selector Price** set. Make sure the field isn’t empty.

**Price is empty in Scraped Pricing**  
- The selector likely points at a wrapper element with no direct text. In DevTools, confirm the node you copied has the price as its text (or as the only text inside it). Try a more specific selector (e.g. a child span that actually contains “20” or “$20”).
- If the price only appears after JavaScript runs, set **Rendering** to **js** and try again.

**Wrong value (e.g. plan name instead of price)**  
- You’re selecting the wrong element. Use SelectorGadget or DevTools again and click only the price number so the selector targets that element.

**Page looks different when the scraper runs**  
- Some sites show different content to bots. If you use **Rendering** = **js**, the scraper already uses a real browser; if it still fails, the site may be blocking or changing content for automation.

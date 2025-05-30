
# Canva App Reviewer — Project Specification  
*A lightweight, open-source prototype that automatically audits Canva Apps for
code quality, accessibility, design consistency, performance, and UX.*

---

## 0  Background & Motivation  
Canva’s **Ecosystem Experiences** group manages an **App Marketplace** where
third-party developers upload JavaScript apps (iframes) built with the
[Canva Apps SDK](https://www.canva.dev/docs/apps/quickstart/).  
Canva reviewers must ensure every submission:

1. Follows SDK best-practice & security rules  
2. Meets Canva design and accessibility guidelines  
3. Loads fast and does not degrade the editor UX  

This prototype mirrors that internal review flow and demonstrates the exact
skills the **Machine Learning Engineer – Ecosystem Experiences** role demands.

---

## 1  Project Goals  

| # | Goal | Success Indicator |
|---|------|------------------|
| **G1** | Accept an app.js file | Upload widget accepts `.js` |
| **G2** | Produce an **HTML / Markdown** report with:<br>• Static code & security findings<br>• Accessibility violations<br>• Design / contrast heuristics<br>• Performance numbers<br>• GPT-4o recommendations<br>• Aggregate “Canva-Ready Score” (0-100) | Report renders in browser & downloadable |
| **G3** | Provide a REST endpoint (`/api/report`) returning JSON | cURL → JSON object |
| **G4** | One-click public demo (Streamlit Cloud) | Link works from résumé |
| **G5** | Fully Dockerised, CI builds, MIT licensed | `docker run …` works; GH Actions badge green |

---

## 2  High-Level Architecture  

```
User ─┐                                     ┌───────────────┐
      ▼  (app.js)                ┌───────────►│  FastAPI API   │── JSON ──► CI/Webhook
┌─────────────┐               │             └───────────────┘
│ Streamlit   │── HTML Report─┘                     ▲
└─────────────┘                                     │
             ╔══════════════════════════════════════╩═══════════════════════════╗
             ║           Docker-ised Worker Pool (Python)                       ║
             ║ • Static Lint & AST rules (ESLint/TS)                             ║
             ║ • Playwright + axe-core for runtime & a11y                        ║
             ║ • Lighthouse (light) for perf                                      ║
             ║ • OpenCV/Pillow heuristics on screenshot                          ║
             ║ • GPT-4o LLM summariser / recommender                             ║
             ╚══════════════════════════════════════════════════════════════════╝
```

---

## 3  Tech Stack  

| Layer | Choice | Notes |
|-------|--------|-------|
| **Frontend** | Streamlit | Free hosting on streamlit.io; fast to prototype |
| **API** | FastAPI | Async, typed, auto Swagger docs |
| **Static Analysis** | `eslint`, `@typescript-eslint`, custom rules | Detect bad patterns, security flags |
| **Runtime & a11y** | Playwright (headless Chromium) + `axe-core` | Launches local preview page |
| **Design Heuristics** | Pillow / OpenCV | Contrast & crowded-layout metrics |
| **Performance** | `lighthouse` (node CLI) | Grab FCP, total KB |
| **LLM** | OpenAI GPT-4o | Create markdown feedback from JSON issues |
| **Orchestration** | Python 3.11, Docker multi-stage | Node for build step, Python for analysis |
| **CI/CD** | GitHub Actions | Lint, tests, build image, deploy Streamlit |
| **License** | MIT | Showcase-friendly |

---

## 4  Input Specification  

### Primary Input  
**`<app>.zip`**  
Must contain at root:

```
canva-app.json        # Manifest
package.json          # Build meta (if source)
src/ or dist/         # Source or built bundle
assets/               # Icons, images
```

The prototype unpacks to a temp workspace, detects `canva-app.json`, then:

* **Source ZIP** → `npm ci && npm run build`
* **Built ZIP**  → skip build, analyse bundle directly

Accepted MIME types: `application/zip`, `application/x-gtar`, `application/gzip`
(for `.tar.gz`).

---

## 5  Milestone Timeline (12 Days ≈ 35 hrs)

| Day | Deliverable | Key Tasks |
|-----|-------------|-----------|
| **1** | Repo bootstrap | README, MIT, tasks board, Canva-made logo |
| **2** | Sample app harness | `canva apps create`; local preview URL |
| **3–4** | Static code checker | ESLint baseline + custom AST rules |
| **5** | a11y + perf runner | Playwright + axe; optional light Lighthouse |
| **6** | Screenshot heuristics | Contrast ratio calc; layout crowd metric |
| **7** | LLM recommender | Prompt GPT-4o, return markdown |
| **8** | Report generator | Jinja2 → HTML & Markdown |
| **9** | Streamlit UI | Upload, spinner, report preview, download |
| **10** | Docker & CI | Multi-stage image, GitHub Actions deploy |
| **11** | Docs & polish | GIF screencast, architecture diagram |
| **12** | Publish | Streamlit link + LinkedIn/blog article |

---

## 6  Implementation Pointers  

### 6.1 Playwright snippet
```python
from playwright.async_api import async_playwright

async def capture_preview(index_html: str, out_png: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(index_html, wait_until="domcontentloaded")
        html = await page.content()
        await page.screenshot(path=out_png, full_page=True)
    return html
```

### 6.2 Custom ESLint Rule (TypeScript)
```ts
export default {
  meta: { type: 'problem', messages: { noEval: 'Avoid eval() for security.' } },
  create: ctx => ({
    CallExpression(node) {
      if (node.callee.name === 'eval') {
        ctx.report({ node, messageId: 'noEval' });
      }
    }
  })
};
```

### 6.3 LLM Prompt Skeleton
```python
SYSTEM = "You are a senior Canva App reviewer..."
USER = """
<ISSUES_JSON>
Generate Markdown with:
## Summary
## Detected Issues
| Category | Impact | Suggestion |
...
"""
```

### 6.4 Scoring Formula
```python
score = round(
    0.30*design +
    0.30*accessibility +
    0.25*code_quality +
    0.15*performance
)
```

---

## 7  Stretch Ideas  

| Idea | Value |
|------|-------|
| **Auto-fix PR** | Generate patch or PR suggestions via GPT |
| **Connect API lint** | Validate OAuth scopes, rate limits |
| **Batch SaaS mode** | Review many apps → dashboard & CSV |
| **Webhook** | CI/CD integration: POST bundle, get JSON |
| **Fine-tuned LLM** | Train on Canva’s own review comments |

---

## 8  Setup Instructions (dev)  

```bash
git clone https://github.com/<you>/canva-app-reviewer
cd canva-app-reviewer
make dev       # poetry install + pre-commit
streamlit run ui/app.py
```

### Build & run Docker
```bash
docker build -t canva-reviewer .
docker run -p 8501:8501 canva-reviewer
```

---

## 9  Useful Canva Links  

* Marketplace: <https://www.canva.com/apps/>  
* Apps SDK Quick Start: <https://www.canva.dev/docs/apps/quickstart/>  
* App UI Guidelines: <https://www.canva.dev/docs/apps/design/>  
* Connect APIs overview: <https://www.canva.dev/docs/apis/>  
* Developer FAQ: <https://www.canva.com/developers/faq/>  

---

## 10  License  
This project is released under the **MIT License**.  
> “Not affiliated with Canva. Built for personal learning & job-application demo
> purposes only.”

---

**Happy building!** ✨

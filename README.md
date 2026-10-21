# Socioeconomic Status Quiz

**Where do you stand among the 8.2 billion people on Earth?**

A static website, hosted on GitHub Pages at https://acosmiccake.github.io/socialranking/ (English) and
https://acosmiccake.github.io/socialranking/vi/ (Vietnamese). It asks about 40 questions, each taken from an established
international survey, and compares your answers with real data for the world, your region, your income group, your country,
urban or rural areas, and people of your age and sex. All scoring runs in the browser, so answers never leave the visitor's device.

Originally a CS50 final project (2021). Rebuilt in 2026 so that every comparison rests on a published, reproducible dataset or
a cited report.

---

## What it measures

| Dimension | Question source (instrument) | Compared against | Data year |
|---|---|---|---|
| **Income** (headline) | Household income after tax ÷ household size, in local currency, converted to 2021 PPP $/day with IMF inflation | World Bank PIP (September 2026 release): world, regions, income groups, all 218 economies, urban/rural (China), 1990-2026 | 2024 (+ history, 2026 nowcast) |
| **Education** | Highest completed level, 9 ISCED 2011 levels; age and sex | UNESCO attainment of adults 25+ (World Bank WDI); Barro-Lee v3 for age/sex groups and missing countries | 2010-2025; 2015 |
| **Work** | ILO status in employment (ICSE-93), sector, and occupation (ISCO-08 major group, ranked by skill level) | ILO modelled estimates: employment by status and sector, vulnerable employment, unemployment (WDI); World Bank Global Jobs Indicators Database: occupations in 115 economies, by sex and urban/rural | 2010-2025 |
| **Living standards** | SDG definitions: electricity (7.1.1), clean cooking (7.1.2), JMP water/sanitation/hygiene ladders, Internet use (ITU), health-cost hardship (3.8.2) | WDI national, urban, rural and regional shares; Tracking SDG7 2026, JMP 2025, ITU 2025, UHC 2025 | 2022-2025 |
| **Multidimensional poverty** (shown, not in the index) | Global MPI's 10 indicators: nutrition, child mortality, schooling, attendance, cooking fuel, sanitation, water, electricity, housing, assets | UNDP/OPHI Global MPI 2026; UN-Habitat overcrowding | 2026 |
| **Financial security** | Gallup World Poll basic-needs items; FAO Food Insecurity Experience Scale (8 items); Global Findex account, saving, emergency funds, months of expenses covered, source of emergency money, biggest worry | Gallup 2020; FAO food insecurity for the world and each country (WDI); SOFI 2026; Findex 2025 for 142 economies (World Bank API) | 2019-2025 |
| **Social protection** (shown, not in the index) | Public programmes received, by ASPIRE type: social insurance, social assistance, labour market | World Bank ASPIRE coverage by country and income fifth (WDI); ILO World Social Protection Report 2024-26 | 2008-2023 |
| **Wealth** (optional) | Net worth per adult in US$ | UBS Global Wealth Report 2026 wealth pyramid | 2025 |
| **Your country** (context only) | Country | Income group, GDP, poverty rates, "you and the typical person" (median income and education, most common work status), the country's statistical performance score, and about 30 WDI indicators grouped by theme (Gini and income shares of the richest 10% and poorest 20%, national poverty rate, women's legal equality, life expectancy, literacy and internet use for your sex, child stunting, Human Capital Index and its schooling components, primary completion, tertiary enrolment, learning poverty, health spending, PM2.5 air pollution, homicide rate) vs region and world | 2019-2025 |
| **Social mobility** (not scored) | Mother's and father's education (4 broad levels) | Barro-Lee v3: each parent's birth cohort at ages 35-44 (1965-2015), by sex, world and 140+ countries | 1965-2015 |
| **Self-placement** (not scored) | MacArthur Scale of Subjective Social Status, country and world ladders | Your measured rung | - |

The results page shows:

- your percentile in the world, in your country, your region and (for China) your urban or rural area;
- the steps that turn your income into 2021 international dollars;
- interactive charts: the world's and your country's income distribution, and your rank in each year from 1990 to 2026;
- a world map and table of where your income would rank in each of the 218 economies, plus by region and income group;
- how much your rank would move if your income were 20% lower or higher;
- whether your income covers a healthy diet at your country's food prices (World Bank Food Prices for Nutrition);
- the income your household would need, in your own currency, to reach the median, top 10% and top 1% of your country and the world;
- a "what if?" slider for different incomes, and the income that would give you the same living standard in any other
  country, in its currency at today's prices;
- education compared with the world, your country and people of your age and sex, and your parents' education against their own generation (social mobility);
- work status and sector compared with the ILO's estimates, and your occupation's skill level compared with surveys in 115 economies;
- every household service compared with the world, your region, your country and your urban/rural area;
- your Multidimensional Poverty Index score and deprivations, and overcrowding;
- food security against FAO's world and country figures, and financial resilience against Global Findex;
- the public programmes your household receives, against coverage in your country and in your income fifth;
- your country at a glance;
- how your self-placement on the ladder compares with the data;
- highlight cards at the top, a section bar that follows your scrolling, and a back-to-top button;
- the dimensions still missing from your SES index, with a link to add them;
- a shareable link (the native share sheet on phones), a downloadable summary image, your numbers as CSV or everything as
  JSON, and a print or save-as-PDF layout;
- "Change my answers", which reopens the quiz pre-filled.

The quiz shows your step, progress and roughly how many minutes are left, lets you jump between visited sections, marks
required questions, and saves your
answers in your browser only (localStorage), so a reload or a closed tab resumes where you left off. The country question has
an accent-insensitive search and suggests the country of your browser's locale. Every page has a skip link and visible
keyboard focus, and fits a 360px phone screen in both languages. The site can be added to a phone's home screen
(web app manifest), and shared links show a preview card.

Every figure links to its source. The [`/methodology`](templates/methodology.html) page documents each calculation and its
limitations. The [`/questionnaire`](templates/questionnaire.html) page lists every question with its source instrument.

## How the income comparison works

1. `daily income per person = household income × 12 / 365 / household size` (for monthly amounts).
2. Convert to 2021 prices by compounding the country's annual average consumer-price inflation from 2022 to 2026, using the
   IMF World Economic Outlook (October 2026).
3. Divide by the 2021 PPP conversion factor to get 2021 international dollars per day. Where the country has a survey, this
   is PIP's own factor; otherwise it's WDI `PA.NUS.PRVT.PP`. Currencies replaced at a fixed rate since the survey (Croatia,
   Bulgaria, Sierra Leone, Belarus, Mauritania) are converted to today's currency.
4. Look this up on two distributions:
   - **Your country's distribution:** PIP's 2024 lined-up distribution, given as the income at the 1st, 2nd, 5th, 10th ... 90th,
     95th, 98th and 99th percentiles, with a Pareto tail above.
   - **The global distribution:** the population-weighted mixture of all 218 national distributions
     (100.0% of the world's population). It is calibrated to pass exactly
     through PIP's official 2024 world headcounts at 15 lines. Before calibration it is already within a few
     tenths of a point of every official figure:

     | $/day (2021 PPP) | Official world headcount (2024) | Uncalibrated mixture |
     |---|---|---|
     | 1 | 1.16% | 1.38% |
     | 2 | 4.80% | 5.10% |
     | 3 | 10.12% | 10.34% |
     | 4.2 | 18.21% | 18.55% |
     | 6 | 32.49% | 32.52% |
     | 8.3 | 46.16% | 46.16% |
     | 10 | 52.87% | 52.83% |
     | 15 | 65.16% | 65.13% |
     | 20 | 72.39% | 72.36% |
     | 30 | 80.67% | 80.55% |
     | 40 | 85.50% | 85.40% |
     | 60 | 91.42% | 91.34% |
     | 80 | 94.76% | 94.70% |
     | 100 | 96.68% | 96.61% |
     | 150 | 98.76% | 98.69% |

Exact local-currency income works for 192 of 218 economies. The rest use a range question: Venezuela and Zimbabwe
(currency replaced without a fixed rate), and economies with no price data (for example Cuba, North Korea, Syria and some
small territories).

## Data

`scripts/build_data.py` builds the country-level data from the official APIs, pinning the PIP release
(`20260922_2021_01_02_PROD`), plus pinned GitHub commits for the files that have no API:

| Source | Used for |
|---|---|
| [World Bank Poverty and Inequality Platform API](https://pip.worldbank.org) | National percentiles for 2024 (all 218 economies), China's urban/rural distributions, world and regional headcounts for 1990-2024 and the 2026 nowcast, survey years, PPP factors |
| [World Bank WDI API](https://datatopics.worldbank.org/world-development-indicators/) | Economies, regions and income groups; population and population 25+; GDP per capita; `PA.NUS.PRVT.PP`; UNESCO educational attainment (8 indicators); 80+ indicators on services (national/urban/rural), food security (FAO), work (ILO, by sex), account ownership (Findex, by group), human capital, health, social protection (ASPIRE, by income fifth) and context, for every economy and aggregate |
| [World Bank API: Global Findex, Food Prices for Nutrition, Global Jobs Indicators](https://api.worldbank.org/v2/sources) | Financial-resilience answers for 142 economies; cost of a healthy diet and the share who can't afford it; occupations (ISCO-08) for 115 economies |
| [IMF World Economic Outlook, October 2026](https://www.imf.org/external/datamapper/PCPIPCH@WEO) | Consumer-price inflation, 2022-2026 |
| [Barro-Lee v3](https://github.com/barrolee/BarroLeeDataSet) | Education by age and sex; education for countries without WDI data |
| [ISO 3166 / ISO 4217](https://github.com/datasets/country-codes) | Common country names, currencies, map codes |
| [Unicode CLDR via Babel](https://babel.pocoo.org/) | Vietnamese country names |

Validation:

- The build cross-checks the PIP PPP factors against WDI for every country and flags currency mismatches.
- Tests check that the IMF-based price index agrees with PIP's survey-year CPI, and that the global curve reproduces PIP's world headcounts.
- Tests also check that the regional mixtures match PIP's regional headcounts to within 2 points.

Global headline figures (JMP, SDG7, ITU, UHC, Findex, Gallup, SOFI, UBS, MPI, ILO social protection, World Bank poverty) are curated in
`ses/facts.py`, each with its citation.

To rebuild the data (this needs access to `api.worldbank.org`, `www.imf.org` and `raw.githubusercontent.com`):

```bash
pip install -r requirements-dev.txt
python scripts/build_data.py --refresh      # pinned releases; caches downloads in data/raw/ (git-ignored)
python scripts/build_data.py --latest       # newest PIP release, data year and IMF edition
```

### Monthly refresh

`.github/workflows/refresh-data.yml` runs `build_data.py --latest` on the 3rd of every month, runs the tests and, if the data
changed, opens a pull request. Merging it redeploys the site. To let the workflow open pull requests, enable **Settings →
Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests**. You can also run it by
hand from the Actions tab.

## Languages

English pages are at the site root and Vietnamese pages under `vi/`. Translations live in `ses/i18n.py`: interface strings,
questionnaire, labels and facts. The methodology and sources pages are English only. The Vietnamese survey wording is our own
translation, not each instrument's official Vietnamese version.

## Publishing on GitHub Pages

The workflow in `.github/workflows/pages.yml` tests the code, builds the site and deploys it on every push to `main`.

One-time setup:

1. On GitHub, open **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.
3. Push to `main`, or run the workflow by hand from the **Actions** tab.

The site is then published at `https://<user>.github.io/socialranking/`.

## Running locally

```bash
pip install -r requirements.txt          # Jinja2 and Babel are all that's needed to build the site
python scripts/build_site.py             # writes _site/ with relative links
python -m http.server -d _site           # http://localhost:8000
```

`python scripts/build_site.py --base-path /socialranking` builds with absolute links, as on GitHub Pages; the workflow does this
for you. Any static host (Netlify, Cloudflare Pages, S3) can serve `_site/`.

### Privacy

The results page reads the answers from the URL fragment (`results.html#country=...`). Browsers never send the fragment to the
server, so nothing is collected. The same link reopens or shares a result, and anyone who opens it can see the answers.

### Using the scorer in code

`static/js/ses.js` runs in the browser and in Node.js:

```js
const SES = require("./static/js/ses.js")(data);   // data = the SES_DATA object from _site/static/js/data.js
SES.score(SES.parseAnswers({country: "VNM", income_mode: "band", income_band: "b4", education: "secondary"}));
```

Field names and options are listed on the questionnaire page and in `ses/questionnaire.py`.

## Project layout

```
ses/questionnaire.py      Every question, its options and its source instrument
ses/i18n.py               Vietnamese translations
ses/facts.py              Cited global statistics
ses/data.py               Loads data/*.json
ses/distributions.py      Income distribution maths (reference implementation, used at build time)
static/js/ses.js          In-browser validation and scoring (all dimensions, MPI, regions, history)
static/js/quiz.js         Multi-step quiz form
static/js/results.js      Results page, charts, world map, what-if slider, share image
scripts/build_data.py     Data pipeline (World Bank, IMF, Barro-Lee) -> data/*.json
scripts/build_site.py     Renders templates/ into the static site _site/ (English + vi/) and the data bundles
templates/, static/       Pages (Jinja2, Bootstrap 5, Chart.js, d3 + world-atlas)
tests/                    pytest suite; tests/js/ holds the Node tests for the scorer
.github/workflows/        Deploy to GitHub Pages; monthly data refresh
```

## Tests

```bash
pip install -r requirements.txt pytest
python -m pytest                          # also runs the Node tests if Node.js is installed
node --test tests/js/ses.test.js          # Node tests on their own (build the site first)
```

A browser walkthrough (also run by the "Browser walkthrough" GitHub workflow on every push and pull request) builds the site with the Pages base path and drives the quiz and results in Chromium
(desktop, phone and Vietnamese), failing on JavaScript errors, missing sections, horizontal scrolling or broken downloads:

```bash
pip install playwright && python -m playwright install chromium
python tests/e2e/walkthrough.py [screenshot-dir]
```

The tests cover:

- **Data:** integrity, calibration against official headcounts, and that every distribution is monotone and invertible.
- **Site build:** every page renders, every internal link resolves, and absolute links work under a base path.
- **Scoring (JavaScript):** the conversions and all dimensions (education by age/sex, work, MPI, food security, regions,
  history), edge cases, validation, every country, and identical numbers in the Vietnamese bundle.
- **Parity:** the JavaScript distribution maths matches the Python implementation to 1e-12.

## Limitations

The headline figure is the income percentile, which is the best-supported single number. The SES index averages the dimension
percentiles, and an average of percentiles is not itself a percentile.

Other known limits:

- Household surveys under-capture the very rich.
- Many countries survey consumption rather than income.
- Survey and report years range from 2015 to 2025.
- The distributions describe 2024. Incomes are measured in today's prices and deflated to 2021, so real growth since 2024 makes results slightly flattering.

The [methodology page](templates/methodology.html) covers all of these.

## Credits

Created by Nguyễn Phan Anh ([nguyenphananh912@gmail.com](mailto:nguyenphananh912@gmail.com)). Background animation by
@Catchmaj.

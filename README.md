# Socioeconomic Status Quiz

**Where do you stand among the 8.2 billion people on Earth?**

A static website, hosted on GitHub Pages, that asks about 30 questions, each taken from an established international survey, and
compares your answers with real global data on income, education, living standards, financial security and wealth. All scoring
runs in the browser, so answers never leave the visitor's device.

Originally a CS50 final project (2021). Rebuilt in 2026 so that every comparison rests on a published, reproducible dataset or
a cited report.

---

## What it measures

| Dimension | Question source (instrument) | Compared against | Data year |
|---|---|---|---|
| **Income** (headline) | Household income after tax ÷ household size, in local currency, converted to 2021 PPP $/day | World Bank PIP (September 2026 release) global and national income/consumption distributions | 2024 |
| **Education** | Highest completed level (7 ISCED-based categories) | Barro-Lee Educational Attainment v3, adults 25-64, 146 countries | 2015 |
| **Living standards** | SDG definitions for electricity (7.1.1), clean cooking (7.1.2), water and sanitation ladders (6.1.1, 6.2.1), hygiene, Internet use (ITU), health-cost hardship (3.8.2) | Tracking SDG7 2026, WHO/UNICEF JMP 2025, ITU 2025, WHO/World Bank UHC 2025 | 2022-2025 |
| **Financial security** | Gallup World Poll basic-needs items; FAO Food Insecurity Experience Scale (8 items); Global Findex account and saving items | Gallup Basic Needs Vulnerability 2020; SOFI 2026; Findex 2025 | 2019-2025 |
| **Wealth** (optional) | Net worth per adult in US$ | UBS Global Wealth Report 2026 wealth pyramid | 2025 |
| **Location** (context only) | Country | GDP per capita rank, population-weighted (WDI) | 2023 |
| **Self-placement** (not scored) | MacArthur Scale of Subjective Social Status, country and world ladders | Your measured rung | - |

The results page shows:

- your percentile within the world and within your country;
- the steps that turn your income into 2021 international dollars;
- an interactive chart of the world's and your country's income distribution;
- a comparison for each service, with the number of people who lack it;
- how your self-placement on the ladder compares with the data.

Every figure links to its source.

The [`/methodology`](templates/methodology.html) page documents each calculation and its limitations. The
[`/questionnaire`](templates/questionnaire.html) page lists every question with its source instrument.

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
| [World Bank Poverty and Inequality Platform API](https://pip.worldbank.org) | National percentiles for 2024, world headcounts, survey years, PPP factors |
| [World Bank WDI API](https://datatopics.worldbank.org/world-development-indicators/) | Economies and income groups, population (world: 8,215,424,893 in 2025), GDP per capita, `PA.NUS.PRVT.PP` |
| [IMF World Economic Outlook, October 2026](https://www.imf.org/external/datamapper/PCPIPCH@WEO) | Consumer-price inflation, 2022-2026 |
| [Barro-Lee v3](https://github.com/barrolee/BarroLeeDataSet) | Educational attainment (144 economies) |
| [ISO 3166 / ISO 4217](https://github.com/datasets/country-codes) | Common country names and currencies |

The build cross-checks the PIP PPP factors against WDI for every country and flags any currency mismatch. A test also checks
that the IMF-based price index agrees with PIP's own survey-year CPI.

Global headline figures (JMP, SDG7, ITU, UHC, Findex, Gallup, SOFI, UBS, World Bank poverty) are curated in `ses/facts.py`,
each with its citation. Update the number and the citation together when a new report is published.

To rebuild the data (this needs access to `api.worldbank.org`, `www.imf.org` and `raw.githubusercontent.com`):

```bash
pip install -r requirements-dev.txt
python scripts/build_data.py --refresh      # caches downloads in data/raw/ (git-ignored), writes data/*.json
```

## Publishing on GitHub Pages

The workflow in `.github/workflows/pages.yml` tests the code, builds the site and deploys it on every push to `main`.

One-time setup:

1. On GitHub, open **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.
3. Push to `main`, or run the workflow by hand from the **Actions** tab.

The site is then published at `https://<user>.github.io/socialranking/`.

## Running locally

```bash
pip install -r requirements.txt          # only Jinja2 is needed to build the site
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
ses/facts.py              Cited global statistics
ses/data.py               Loads data/*.json
ses/distributions.py      Income distribution maths (reference implementation, used at build time)
static/js/ses.js          In-browser validation and scoring
static/js/quiz.js         Multi-step quiz form
static/js/results.js      Results page and chart
scripts/build_data.py     Reproducible data pipeline -> data/*.json
scripts/build_site.py     Renders templates/ into the static site _site/ (plus static/js/data.js)
templates/, static/       Pages (Jinja2, Bootstrap 5, Chart.js)
tests/                    pytest suite; tests/js/ holds the Node tests for the scorer
.github/workflows/        Build, test and deploy to GitHub Pages
```

## Tests

```bash
pip install -r requirements.txt pytest
python -m pytest                          # also runs the Node tests if Node.js is installed
node --test tests/js/ses.test.js          # Node tests on their own (build the site first)
```

The tests cover:

- **Data:** integrity, calibration against official headcounts, and that every distribution is monotone and invertible.
- **Site build:** every page renders, every internal link resolves, and absolute links work under a base path.
- **Scoring (JavaScript):** the conversions and all dimensions, edge cases, validation, and every country.
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

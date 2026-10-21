// Scoring engine: turns questionnaire answers into comparisons with the world's population.
//
// Conventions
// * A percentile is the share of people (0-100) who are worse off than you on that
//   measure. For categorical answers we use the mid-rank: everyone in a lower
//   category plus half of the people in your own category.
// * Each dimension is compared against its own source population.
// * The SES index is the plain average of the dimension percentiles answered. It
//   summarises your position; it is not itself a percentile.
//
// Works in the browser (window.SES, reading window.SES_DATA from data.js) and in
// Node for the tests (module.exports = create(data)).
(function (root) {
    "use strict";

    function create(D) {
        const Q = D.questionnaire;
        const F = D.facts;
        const G = D.global;
        const byIso3 = Object.fromEntries(D.countries.map(c => [c.iso3, c]));
        const world = G.aggregates.WLD.wdi;

        // Price data run to G.prices.last_year (IMF projections); later years are
        // carried forward at the last rate for at most this many years.
        const MAX_EXTRAPOLATION_YEARS = 3;
        const MAX_HOUSEHOLD_SIZE = 50;
        // People misreport income in surveys; show how far the rank moves at +/-20%.
        const INCOME_ERROR = 0.2;
        const THRESHOLD_PCTS = [50, 90, 99];
        // ASPIRE programme types and their WDI code prefixes.
        const SP_PROGRAMMES = [["any", "allsp"], ["assistance", "sa_allsa"], ["insurance", "si_allsi"],
                               ["labour_market", "lm_alllm"]];

        // Display strings; a translated data bundle can override any of them (D.labels).
        const L = Object.assign({
            dimensions: {income: "Income", education: "Education", work: "Work", living: "Living standards",
                         security: "Financial security", wealth: "Wealth"},
            poverty_lines: [
                ["International poverty line ($3.00)", "extreme poverty"],
                ["Lower-middle-income line ($4.20)", "the poverty line typical of lower-middle-income countries"],
                ["Upper-middle-income line ($8.30)", "the poverty line typical of upper-middle-income countries"],
            ],
            mpi: {nutrition: "Nutrition", child_mortality: "Child mortality", years_of_schooling: "Years of schooling",
                  school_attendance: "School attendance", cooking_fuel: "Cooking fuel", sanitation: "Sanitation",
                  drinking_water: "Drinking water", electricity: "Electricity", housing: "Housing", assets: "Assets"},
            glance: {
                "NY.GDP.PCAP.PP.KD": "GDP per person (2021 international $)",
                "SP.DYN.LE00.IN": "Life expectancy at birth (years)",
                "SH.DYN.MORT": "Under-5 deaths per 1,000 births",
                "SP.URB.TOTL.IN.ZS": "Living in cities and towns",
                "SE.ADT.LITR.ZS": "Adults who can read and write",
                "SN.ITK.DEFC.ZS": "Undernourished",
                "SL.UEM.TOTL.ZS": "Unemployment rate",
                "SL.EMP.VULN.ZS": "Workers in vulnerable employment",
                "SH.XPD.OOPC.CH.ZS": "Health spending paid out of pocket",
                "EN.POP.SLUM.UR.ZS": "City dwellers living in slums",
                "SI.POV.GINI": "Inequality (Gini index, 0-100)",
                "SI.DST.10TH.10": "Share of income going to the richest 10%",
                "SI.DST.FRST.20": "Share of income going to the poorest 20%",
                "SI.POV.NAHC": "Poor by the country's own poverty line",
                "GD_WBL_OVL_LAW": "Women's legal equality (Women, Business and the Law, 0-100)",
                "SP.DYN.LE00.FE.IN": "Life expectancy at birth, women (years)",
                "SP.DYN.LE00.MA.IN": "Life expectancy at birth, men (years)",
                "HD.HCI.OVRL": "Human Capital Index (0-1)",
                "HD.HCI.OVRL.FE": "Human Capital Index, girls (0-1)",
                "SE.ADT.LITR.FE.ZS": "Women who can read and write",
                "SE.ADT.LITR.MA.ZS": "Men who can read and write",
                "IT.NET.USER.FE.ZS": "Women using the internet",
                "IT.NET.USER.MA.ZS": "Men using the internet",
                "HD.HCI.OVRL.MA": "Human Capital Index, boys (0-1)",
                "HD.HCI.EYRS": "Expected years of school by age 18",
                "HD.HCI.LAYS": "Learning-adjusted years of school",
                "SE.LPV.PRIM": "10-year-olds who can't read a simple text",
                "IT.CEL.SETS.P2": "Mobile subscriptions per 100 people",
                "SH.XPD.CHEX.PC.CD": "Health spending per person (US$)",
            },
            findex: {
                emergency: {not_possible: "Not possible", very_difficult: "Possible, but very difficult",
                            somewhat_difficult: "Possible, but somewhat difficult", not_difficult: "Possible and not difficult at all"},
                cover_expenses: {under_2_weeks: "Less than two weeks", one_month: "About one month",
                                 two_months: "About two months", over_2_months: "More than two months"},
                emergency_source: {savings: "Savings", family: "Family or friends", work: "Work", borrowing: "Borrowing",
                                   sale_of_assets: "Selling something", other: "Other"},
                worry: {old_age: "Money for old age", business: "Money for a business", medical: "Medical costs",
                        bills: "Monthly expenses or bills", school: "School fees", none: "None of these"},
            },
            account_groups: {
                sex: {F: "Women", M: "Men"},
                income: {poor: "Poorest 40% of households", rich: "Richest 60% of households"},
                age: {young: "Young adults (15-24)", older: "Adults 25 and over"},
                education: {low: "Primary education or less", high: "Secondary education or more"},
            },
            no_cooking: "No cooking at home",
            errors: {
                option: "Please choose one of the options.",
                options: "Please choose from the options.",
                country: "Please choose your country.",
                education: "Please choose your highest completed level of education.",
                exact_unavailable: "We can't convert {country}'s currency reliably{why}, so please pick a range instead.",
                amount: "Please enter your household income as a number (0 or more).",
                size: "Please enter a whole number of people from 1 to {max}.",
                period: "Please say whether the amount is per month or per year.",
                band: "Please choose a range.",
                mode: "Please choose how you'd like to answer the income question.",
                rooms: "Please enter a whole number of rooms from 1 to 50, or leave it blank.",
                housing_none: "\"None of these\" can't be combined with the other options.",
            },
        }, D.labels || {});
        const fill = (template, vars) => template.replace(/\{(\w+)\}/g, (_, k) => vars[k]);

        const POVERTY_LINES = [3.0, 4.2, 8.3].map((line, i) => [line, ...L.poverty_lines[i]]);
        const DIMENSION_LABELS = L.dimensions;

        // Household services: World Bank indicator (total; urban/rural variants add .UR/.RU).
        const SERVICES = {
            electricity: {wdi: "EG.ELC.ACCS", area: true},
            clean_cooking: {wdi: "EG.CFT.ACCS", area: true},
            water: {wdi: "SH.H2O.SMDW", area: true},
            sanitation: {wdi: "SH.STA.SMSS", area: true},
            hygiene: {wdi: "SH.STA.HYGN", area: true},
            internet: {wdi: "IT.NET.USER", area: false},
            health_hardship: {wdi: null, area: false},
        };

        // ------------------------------------------------------------------
        // Distributions (all incomes per person per day, 2021 international $)
        // ------------------------------------------------------------------

        // Index of the last element <= x in a sorted array (bisect_right - 1).
        function bisect(arr, x) {
            let lo = 0, hi = arr.length;
            while (lo < hi) {
                const mid = (lo + hi) >> 1;
                if (x < arr[mid]) hi = mid; else lo = mid + 1;
            }
            return lo - 1;
        }

        // National distribution: PIP's income thresholds x at population shares p,
        // linear from zero below the first point, log-linear between points and
        // Pareto above the last one.
        function nationalCdf(dist, x) {
            const ps = dist.p, xs = dist.x, n = xs.length;
            if (x <= 0) return 0;
            if (x < xs[0]) return ps[0] * x / xs[0];
            if (x >= xs[n - 1]) return 1 - (1 - ps[n - 1]) * Math.pow(xs[n - 1] / x, dist.pareto_alpha);
            const i = bisect(xs, x);
            const frac = (Math.log(x) - Math.log(xs[i])) / (Math.log(xs[i + 1]) - Math.log(xs[i]));
            return ps[i] + frac * (ps[i + 1] - ps[i]);
        }

        function nationalQuantile(dist, p) {
            const ps = dist.p, xs = dist.x, n = xs.length;
            if (p <= ps[0]) return xs[0] * p / ps[0];
            if (p >= ps[n - 1]) return xs[n - 1] * Math.pow((1 - ps[n - 1]) / Math.max(1 - p, 1e-9), 1 / dist.pareto_alpha);
            const i = bisect(ps, p);
            const frac = (p - ps[i]) / (ps[i + 1] - ps[i]);
            return Math.exp(Math.log(xs[i]) + frac * (Math.log(xs[i + 1]) - Math.log(xs[i])));
        }

        // A CDF on the shared log-spaced grid (global distribution and history years).
        function gridCdf(cdf, x) {
            const grid = G.income.grid;
            if (x <= 0) return 0;
            if (x <= grid[0]) return cdf[0] * x / grid[0];
            if (x >= grid[grid.length - 1]) return cdf[cdf.length - 1];
            const i = bisect(grid, x);
            const l0 = Math.log(grid[i]), l1 = Math.log(grid[i + 1]);
            return cdf[i] + (cdf[i + 1] - cdf[i]) * (Math.log(x) - l0) / (l1 - l0);
        }

        const globalCdf = x => gridCdf(G.income.cdf, x);

        function globalQuantile(p) {
            const {grid, cdf} = G.income;
            if (p <= cdf[0]) return cdf[0] ? grid[0] * p / cdf[0] : grid[0];
            if (p >= cdf[cdf.length - 1]) return grid[grid.length - 1];
            let i = bisect(cdf, p);
            while (cdf[i + 1] === cdf[i]) i++;
            const l0 = Math.log(grid[i]), l1 = Math.log(grid[i + 1]);
            return Math.exp(l0 + (l1 - l0) * (p - cdf[i]) / (cdf[i + 1] - cdf[i]));
        }

        // Share below x among a group of economies (population-weighted mixture).
        function groupCdf(countries, x) {
            let below = 0, total = 0;
            for (const c of countries) {
                if (!c.income) continue;
                below += c.population * nationalCdf(c.income, x);
                total += c.population;
            }
            return total ? below / total : null;
        }

        // ------------------------------------------------------------------
        // Parsing
        // ------------------------------------------------------------------

        class ValidationError extends Error {
            constructor(errors) {
                super("invalid answers");
                this.errors = errors;
            }
        }

        function toNumber(raw) {
            if (raw === undefined || raw === null) return null;
            const s = String(raw).trim().replace(/[,\s_]/g, "");
            if (!s || !/^[+-]?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i.test(s)) return null;
            const v = Number(s);
            return Number.isFinite(v) ? v : null;
        }

        function exactIncomeAvailable(country) {
            return Boolean(country.prices && country.prices.exact_income);
        }

        // Validate answers (plain object of strings; checkbox answers comma-separated
        // or arrays) -> clean answers. Throws ValidationError with {field: message}.
        function parseAnswers(form) {
            const answers = {};
            const errors = {};
            for (const q of Q.questions) {
                let value = form[q.id];
                if (q.type === "checkbox") {
                    const list = Array.isArray(value) ? value : String(value || "").split(",");
                    const picked = list.map(v => String(v).trim()).filter(Boolean);
                    if (picked.some(v => !q.options.includes(v))) {
                        errors[q.id] = L.errors.options;
                        continue;
                    }
                    // Nothing ticked means unanswered; "none" is an explicit answer.
                    answers[q.id] = picked.length ? [...new Set(picked)] : null;
                    if (answers[q.id] && answers[q.id].includes("none") && answers[q.id].length > 1) {
                        errors[q.id] = L.errors.housing_none;
                    }
                    continue;
                }
                value = typeof value === "string" ? value.trim() : value;
                if ((q.type === "radio" || q.type === "ladder") && value && !q.options.includes(value)) {
                    errors[q.id] = L.errors.option;
                    continue;
                }
                answers[q.id] = value || null;
            }

            const country = byIso3[answers.country || ""];
            if (!country) errors.country = L.errors.country;
            if (!answers.education) errors.education = L.errors.education;

            const mode = answers.income_mode;
            if (mode === "exact") {
                if (country && !exactIncomeAvailable(country)) {
                    const why = country.prices && country.prices.exact_income_reason;
                    errors.income_mode = fill(L.errors.exact_unavailable,
                        {country: country.name, why: why ? ` (${why.replace(/\.$/, "")})` : ""});
                }
                const amount = toNumber(answers.income_amount);
                const size = toNumber(answers.household_size);
                if (amount === null || amount < 0) {
                    errors.income_amount = L.errors.amount;
                }
                if (size === null || size < 1 || size > MAX_HOUSEHOLD_SIZE || !Number.isInteger(size)) {
                    errors.household_size = fill(L.errors.size, {max: MAX_HOUSEHOLD_SIZE});
                }
                if (answers.income_period !== "month" && answers.income_period !== "year") {
                    errors.income_period = L.errors.period;
                }
                answers.income_amount = amount;
                answers.household_size = size;
            } else if (mode === "band") {
                if (!answers.income_band) errors.income_band = L.errors.band;
            } else {
                errors.income_mode = L.errors.mode;
            }

            if (answers.sleeping_rooms !== null) {
                const rooms = toNumber(answers.sleeping_rooms);
                if (rooms === null || rooms < 1 || rooms > 50 || !Number.isInteger(rooms)) {
                    errors.sleeping_rooms = L.errors.rooms;
                }
                answers.sleeping_rooms = rooms;
            }

            if (Object.keys(errors).length) throw new ValidationError(errors);
            return answers;
        }

        // ------------------------------------------------------------------
        // Helpers
        // ------------------------------------------------------------------

        const pct = share => Math.round(1000 * share) / 10;
        const people = share => share * G.world_population;
        const sum = xs => xs.reduce((a, b) => a + b, 0);
        const midrank = (shares, index) => sum(shares.slice(0, index)) + shares[index] / 2;
        const value = (wdi, code) => (wdi && wdi[code] ? wdi[code][1] : null);
        const year = (wdi, code) => (wdi && wdi[code] ? wdi[code][0] : null);
        // Display name of an income group (translated bundles add income_group_label).
        const groupLabel = name => {
            const c = D.countries.find(x => x.income_group === name);
            return (c && c.income_group_label) || name;
        };
        const regionAggregate = country => (country.region && G.aggregates[country.region]) || null;
        const incomeAggregate = country => {
            const code = {"Low income": "LIC", "Lower middle income": "LMC", "Upper middle income": "UMC", "High income": "HIC"}[country.income_group];
            return code ? G.aggregates[code] : null;
        };

        // Consumer prices in `year` relative to 2021 for this country.
        function priceLevel(prices, yr) {
            const years = Object.keys(prices.price_index).map(Number);
            const last = Math.max(...years);
            const y = Math.max(Math.min(...years), Math.min(yr, last + MAX_EXTRAPOLATION_YEARS));
            if (y <= last) return {level: prices.price_index[y], year: y, extrapolated: 0};
            return {
                level: prices.price_index[last] * Math.pow(1 + prices.current_inflation, y - last),
                year: y, extrapolated: y - last,
            };
        }

        function toPppPerDay(amount, period, householdSize, country, today) {
            const prices = country.prices;
            const perDay = amount * (period === "month" ? 12 : 1) / 365 / householdSize;
            const pl = priceLevel(prices, today.getFullYear());
            return {
                local_per_day: perDay,
                price_level_vs_2021: pl.level,
                price_year: pl.year,
                extrapolated_years: pl.extrapolated,
                estimated_years: prices.inflation_estimated_years,
                currency_change: prices.currency_change || null,
                ppp_2021: prices.ppp_2021,
                ppp_source: prices.ppp_source,
                ppp_per_day: perDay / pl.level / prices.ppp_2021,
            };
        }

        // ------------------------------------------------------------------
        // Income
        // ------------------------------------------------------------------

        function incomeChart(country, x) {
            const grid = Array.from({length: 72}, (_, i) => 0.5 * Math.pow(1.12, i)); // $0.50 .. ~$1,500 a day
            const dist = country.income;
            const r2 = v => Math.round(v * 100) / 100;
            return {
                x: grid.map(v => Math.round(v * 1000) / 1000),
                world: grid.map(v => r2(100 * globalCdf(v))),
                country: dist ? grid.map(v => r2(100 * nationalCdf(dist, v))) : null,
                you: Math.round(x * 1000) / 1000,
                you_world: r2(100 * globalCdf(x)),
                you_country: dist ? r2(100 * nationalCdf(dist, x)) : null,
            };
        }

        // The least-cost healthy diet in the country (World Bank Food Prices for Nutrition) against
        // income x. FAO and the World Bank count it unaffordable above 52% of income.
        function healthyDiet(country, x, today) {
            const hd = country.healthy_diet, gw = G.healthy_diet;
            const result = {income_share_rule: gw.income_share, world: gw.world};
            if (!hd) return result;
            Object.assign(result, {year: hd.year, unaffordable_pct: pct(hd.unaffordable_share),
                                   unaffordable_people: hd.unaffordable_people || null});
            if (hd.cost_2021ppp !== undefined) {
                Object.assign(result, {
                    cost_year: hd.cost_year, cost_2021ppp: hd.cost_2021ppp,
                    share_of_income: hd.cost_2021ppp / x,
                    affordable: hd.cost_2021ppp <= gw.income_share * x,
                });
                if (hd.cost_lcu !== undefined) {
                    const prices = country.prices;
                    result.cost_local_today = hd.cost_lcu * priceLevel(prices, today.getFullYear()).level
                        / prices.price_index[hd.cost_year];
                }
            }
            return result;
        }

        // Findex's emergency amount (1/20 of GNI per person) in today's local currency.
        function emergencyAmount(country, today) {
            const a = country.findex && country.findex.emergency_amount;
            if (!a) return null;
            const prices = country.prices;
            const scale = priceLevel(prices, today.getFullYear()).level / prices.price_index[a.year];
            const raw = a.lcu * scale;
            const unit = Math.pow(10, Math.max(0, Math.floor(Math.log10(raw)) - 1));
            return {amount: Math.round(raw / unit) * unit, currency: country.currency, gni_year: a.year};
        }

        // Income needed to reach the median, top 10% and top 1% of the country and the
        // world, in 2021 $ a day and (for exact answers) in the household's own terms.
        function incomeThresholds(answers, country, x, today) {
            const dist = country.income;
            const exact = answers.income_mode === "exact";
            const toLocal = exact ? (ppp => {
                const pl = priceLevel(country.prices, today.getFullYear());
                return ppp * country.prices.ppp_2021 * pl.level * answers.household_size * 365
                    / (answers.income_period === "month" ? 12 : 1);
            }) : null;
            const row = (scope, p, ppp) => ({
                scope, pct: p, ppp_per_day: ppp, reached: x >= ppp, multiple: ppp / x,
                local: toLocal ? toLocal(ppp) : null,
            });
            const rows = [];
            if (dist) for (const p of THRESHOLD_PCTS) rows.push(row("country", p, nationalQuantile(dist, p / 100)));
            for (const p of THRESHOLD_PCTS) rows.push(row("world", p, globalQuantile(p / 100)));
            return rows;
        }

        // Where income x (2021 $/day) ranks in every economy, region and income group.
        function incomeEverywhere(x) {
            const countries = D.countries.filter(c => c.income).map(c => ({
                iso3: c.iso3, name: c.name, m49: c.m49, region: c.region, income_group: c.income_group,
                pct: pct(nationalCdf(c.income, x)), median: c.income.median,
            }));
            const regions = Object.entries(G.regions).map(([code, name]) => {
                const members = D.countries.filter(c => c.region === code);
                const share = groupCdf(members, x);
                return {code, name, pct: share === null ? null : pct(share), population: sum(members.map(c => c.population))};
            }).filter(r => r.pct !== null);
            const groups = ["Low income", "Lower middle income", "Upper middle income", "High income"].map(name => {
                const share = groupCdf(D.countries.filter(c => c.income_group === name), x);
                return {name: groupLabel(name), pct: share === null ? null : pct(share)};
            }).filter(g => g.pct !== null);
            return {countries, regions, groups};
        }

        // Your (real) income placed in the world's distribution in earlier years.
        function incomeHistory(x) {
            return Object.entries(G.income.history).map(([yr, h]) => ({
                year: Number(yr), pct: pct(gridCdf(h.cdf, x)), estimate_type: h.estimate_type,
                share_below_3: pct(h.share_below_3), population: h.population,
            }));
        }

        function scoreIncome(answers, country, today) {
            const dist = country.income;
            const result = {mode: answers.income_mode, national_available: Boolean(dist)};
            let x;
            if (answers.income_mode === "exact") {
                Object.assign(result, toPppPerDay(answers.income_amount, answers.income_period,
                    answers.household_size, country, today));
                x = result.ppp_per_day;
                result.global_share = globalCdf(x);
                if (dist) result.national_share = nationalCdf(dist, x);
            } else {
                const [, low, high, label] = Q.income_bands.find(b => b[0] === answers.income_band);
                x = low ? Math.sqrt(low * high) : high / 2;
                Object.assign(result, {band_label: label, band_low: low, band_high: high, ppp_per_day: x});
                const gLow = globalCdf(low), gHigh = globalCdf(high);
                result.global_share = (gLow + gHigh) / 2;
                result.global_range = [pct(gLow), pct(gHigh)];
                if (dist) {
                    const nLow = nationalCdf(dist, low), nHigh = nationalCdf(dist, high);
                    result.national_share = (nLow + nHigh) / 2;
                    result.national_range = [pct(nLow), pct(nHigh)];
                }
            }
            const share = result.global_share;
            result.global_pct = pct(share);
            result.top_pct = Math.round(1000 - 1000 * share) / 10;
            result.people_below = people(share);
            result.people_above = people(1 - share);
            result.person_of_100 = Math.min(100, Math.max(1, Math.ceil(share * 100)));
            if (result.national_share !== undefined) result.national_pct = pct(result.national_share);
            if (dist && dist.by_area && answers.area && dist.by_area[answers.area]) {
                result.area_pct = pct(nationalCdf(dist.by_area[answers.area], x));
                result.area = answers.area;
            }
            result.lines = POVERTY_LINES.map(([line, label, meaning]) => ({
                line, label, meaning, above: x >= line, share_below: pct(globalCdf(line)),
                country_share_below: dist ? pct(nationalCdf(dist, line)) : null,
            }));
            result.world_median = G.income.world_median;
            result.multiple_of_world_median = x / result.world_median;
            if (dist) result.multiple_of_country_median = x / dist.median;
            result.chart = incomeChart(country, x);
            if (answers.income_mode === "exact") {
                result.basis = answers.income_basis || null;
                result.basis_mismatch = Boolean(dist && result.basis && result.basis !== dist.welfare_type);
                const lo = x * (1 - INCOME_ERROR), hi = x * (1 + INCOME_ERROR);
                result.sensitivity = {
                    error: INCOME_ERROR,
                    global: [pct(globalCdf(lo)), pct(globalCdf(hi))],
                    national: dist ? [pct(nationalCdf(dist, lo)), pct(nationalCdf(dist, hi))] : null,
                };
            }
            result.thresholds = incomeThresholds(answers, country, x, today);
            result.healthy_diet = healthyDiet(country, x, today);
            if (dist && dist.history) {
                const h = dist.history;
                result.national_history = {
                    years: h.median.map((_, i) => h.start + i), median: h.median,
                    below_3: h.below_3.map(v => pct(v)),
                    // The first year the country's median reached your income, if it has.
                    reached: (() => { const i = h.median.findIndex(m => m >= x); return i < 0 ? null : h.start + i; })(),
                };
            }
            result.everywhere = incomeEverywhere(x);
            result.history = incomeHistory(x);
            const region = result.everywhere.regions.find(r => r.code === country.region);
            if (region) result.region = region;
            return result;
        }

        // ------------------------------------------------------------------
        // Education
        // ------------------------------------------------------------------

        function scoreEducation(answers, country) {
            const keys = Q.education_options.map(o => o[0]);
            const idx = keys.indexOf(answers.education);
            const edu = G.education;
            const shares = edu.world_shares;
            const result = {
                level: idx,
                label: Q.education_options[idx][1],
                global_pct: pct(midrank(shares, idx)),
                world_shares: shares.map(pct),
                same_level_pct: pct(shares[idx]),
                higher_pct: pct(sum(shares.slice(idx + 1))),
                levels: edu.levels.map(l => l.label),
            };
            const ce = country.education;
            if (ce) {
                result.national_pct = pct(midrank(ce.shares, idx));
                result.country_shares = ce.shares.map(pct);
                result.country_source = ce.source;
                result.country_year = ce.year;
                result.country_mean_years = ce.mean_years;
            }
            // Women or men in your country and the world (WDI attainment by sex).
            const sex = answers.sex === "F" || answers.sex === "M" ? answers.sex : "MF";
            if (sex !== "MF") {
                const ws = edu.world_by_sex && edu.world_by_sex[sex];
                result.sex = sex;
                if (ws) result.world_sex_pct = pct(midrank(ws, idx));
                if (ce && ce.by_sex && ce.by_sex[sex]) {
                    result.national_sex_pct = pct(midrank(ce.by_sex[sex], idx));
                    result.country_sex_shares = ce.by_sex[sex].map(pct);
                }
            }
            // People of your age and sex (Barro-Lee broad levels).
            const group = answers.age && edu.groups[answers.age];
            if (group) {
                const broad = edu.broad_from_level[idx];
                const worldShares = group[sex] || group.MF;
                result.group = {
                    age: answers.age, sex, broad_label: edu.broad_levels[broad], year: edu.groups_year,
                    levels: edu.broad_levels,
                    world_shares: worldShares.map(pct),
                    world_pct: pct(midrank(worldShares, broad)),
                };
                const cg = ce && ce.groups && ce.groups[answers.age];
                if (cg && (cg[sex] || cg.MF)) {
                    const cs = cg[sex] || cg.MF;
                    result.group.country_shares = cs.map(pct);
                    result.group.country_pct = pct(midrank(cs, broad));
                }
            }
            return result;
        }

        // Social mobility: each parent's education ranked among people of the same sex in their
        // generation at ages 35-44 (Barro-Lee), against your own rank among people your age.
        const PARENT_GAP = 30;  // years between a parent's birth and their child's
        const AGE_MIDPOINT = {"15-24": 20, "25-34": 30, "35-44": 40, "45-54": 50, "55-64": 60, "65plus": 72};

        function scoreMobility(answers, country, today) {
            const edu = G.education, ce = country.education || {};
            const keys = Q.parent_education_options.map(o => o[0]).filter(k => k !== "dont_know");
            const given = [["mother", "F"], ["father", "M"]]
                .filter(([p]) => keys.includes(answers[`${p}_education`]));
            if (!given.length) return {};
            if (!answers.age) return {needs_age: true};
            const born = today.getFullYear() - AGE_MIDPOINT[answers.age];
            const year = Math.min(2015, Math.max(1965, Math.round((born - PARENT_GAP + 40) / 5) * 5));
            const result = {cohort_year: year, cohort_born: year - 40, parent_gap: PARENT_GAP, levels: edu.broad_levels, parents: []};
            for (const [parent, sex] of given) {
                const level = keys.indexOf(answers[`${parent}_education`]);
                const ws = edu.cohorts[year][sex];
                const cs = ce.cohorts && ce.cohorts[year] && ce.cohorts[year][sex];
                result.parents.push({
                    parent, sex, level, label: edu.broad_levels[level],
                    world_shares: ws.map(pct), world_pct: pct(midrank(ws, level)),
                    country_shares: cs ? cs.map(pct) : null, national_pct: cs ? pct(midrank(cs, level)) : undefined,
                });
            }
            const rank = p => (p.national_pct !== undefined ? p.national_pct : p.world_pct);
            const best = result.parents.reduce((a, b) => (rank(b) > rank(a) ? b : a));
            result.best = best.parent;
            const own = edu.broad_from_level[Q.education_options.findIndex(o => o[0] === answers.education)];
            result.own_level = own;
            result.own_label = edu.broad_levels[own];
            result.direction = own > best.level ? "up" : own === best.level ? "same" : "down";
            // Your own rank among people your age (still in education at 15-24, so not ranked).
            const groupKey = answers.age === "65plus" ? "55-64" : answers.age;
            const sx = answers.sex === "F" || answers.sex === "M" ? answers.sex : "MF";
            if (edu.groups[groupKey]) {
                result.own_world_pct = pct(midrank(edu.groups[groupKey][sx], own));
                const cg = ce.groups && ce.groups[groupKey];
                if (cg && cg[sx]) result.own_national_pct = pct(midrank(cg[sx], own));
                const useNational = result.own_national_pct !== undefined && best.national_pct !== undefined;
                result.basis = useNational ? "country" : "world";
                result.rank_change = useNational ? Math.round(10 * (result.own_national_pct - best.national_pct)) / 10
                    : Math.round(10 * (result.own_world_pct - best.world_pct)) / 10;
            }
            return result;
        }

        // ------------------------------------------------------------------
        // Work
        // ------------------------------------------------------------------

        // Employment status shares (% of employment) from ILO modelled estimates.
        // sfx: "" for everyone, ".FE"/".MA" for women/men.
        const sexCode = (code, sfx) => sfx ? code.replace(/\.ZS$/, `${sfx}.ZS`) : code;

        function statusShares(wdi, sfx = "") {
            const v = code => value(wdi, sexCode(code, sfx));
            const work = v("SL.EMP.WORK.ZS"), emp = v("SL.EMP.MPYR.ZS");
            const fam = v("SL.FAM.WORK.ZS"), vuln = v("SL.EMP.VULN.ZS");
            if ([work, emp, fam, vuln].some(v => v === null)) return null;
            return {employee: work, employer: emp, own_account: Math.max(vuln - fam, 0), family_worker: fam,
                    vulnerable: vuln, year: year(wdi, "SL.EMP.VULN.ZS")};
        }

        function sectorShares(wdi, sfx = "") {
            const v = code => value(wdi, sexCode(code, sfx));
            const s = {agriculture: v("SL.AGR.EMPL.ZS"), industry: v("SL.IND.EMPL.ZS"), services: v("SL.SRV.EMPL.ZS")};
            return Object.values(s).some(v => v === null) ? null : s;
        }

        function scoreWork(answers, country) {
            const status = answers.work_status;
            if (!status) return {};
            const label = Q.work_options.find(o => o[0] === status)[1];
            const result = {
                status, label,
                employed: Q.employed.includes(status),
                world: statusShares(world), country: statusShares(country.wdi),
                world_sectors: sectorShares(world), country_sectors: sectorShares(country.wdi),
                unemployment: {world: value(world, "SL.UEM.TOTL.ZS"), country: value(country.wdi, "SL.UEM.TOTL.ZS")},
                participation: {world: value(world, "SL.TLF.CACT.ZS"), country: value(country.wdi, "SL.TLF.CACT.ZS")},
            };
            const sfx = answers.sex === "F" ? ".FE" : answers.sex === "M" ? ".MA" : "";
            if (sfx) {
                result.sex = answers.sex;
                result.sex_world = statusShares(world, sfx);
                result.sex_country = statusShares(country.wdi, sfx);
                result.sex_world_sectors = sectorShares(world, sfx);
                result.sex_country_sectors = sectorShares(country.wdi, sfx);
                result.sex_unemployment = {world: value(world, sexCode("SL.UEM.TOTL.ZS", sfx)),
                                           country: value(country.wdi, sexCode("SL.UEM.TOTL.ZS", sfx))};
                result.sex_participation = {world: value(world, sexCode("SL.TLF.CACT.ZS", sfx)),
                                            country: value(country.wdi, sexCode("SL.TLF.CACT.ZS", sfx))};
            }
            if (answers.work_sector) {
                result.sector = answers.work_sector;
                result.sector_label = Q.sector_options.find(o => o[0] === answers.work_sector)[1];
            }
            // Job quality: the ILO's vulnerable-employment split, as a mid-rank, averaged with the
            // occupation's ISCO skill-level rank where the user gave one.
            if (result.employed && result.world) {
                const v = result.world.vulnerable / 100;
                const vulnerable = Q.vulnerable.includes(status);
                result.vulnerable = vulnerable;
                const statusRank = vulnerable ? v / 2 : v + (1 - v) / 2;
                result.status_pct = pct(statusRank);
                let nationalRank = null;
                if (result.country) {
                    const cv = result.country.vulnerable / 100;
                    nationalRank = vulnerable ? cv / 2 : cv + (1 - cv) / 2;
                    result.status_national_pct = pct(nationalRank);
                }
                const occ = answers.occupation ? scoreOccupation(answers, country) : null;
                if (occ) result.occupation = occ;
                const combine = (a, b) => (b === null || b === undefined ? a : (a + b) / 2);
                result.global_pct = pct(combine(statusRank, occ && occ.world_rank));
                if (nationalRank !== null) result.national_pct = pct(combine(nationalRank, occ && occ.national_rank));
            }
            return result;
        }

        // Occupation: share of workers in each ISCO-08 major group, and the user's mid-rank by
        // skill level (armed forces span several levels and get no rank).
        function skillRank(shares, level) {
            const levels = G.occupation.skill_levels;
            const byLevel = [1, 2, 3, 4].map(l => sum(shares.filter((_, i) => levels[i] === l)));
            const total = sum(byLevel);
            return midrank(byLevel.map(x => x / total), level - 1);
        }

        function scoreOccupation(answers, country) {
            const occ = G.occupation;
            const idx = occ.keys.indexOf(answers.occupation);
            const level = occ.skill_levels[idx];
            const label = Q.occupation_options.find(o => o[0] === answers.occupation)[1];
            const result = {key: answers.occupation, label, skill_level: level, labels: Q.occupation_options.map(o => o[1]),
                            pooled_shares: occ.shares.map(pct), pooled_same: pct(occ.shares[idx]),
                            economies: occ.economies, employed_covered_pct: pct(occ.employed_covered / occ.employed_world)};
            if (level) {
                result.world_rank = skillRank(occ.shares, level);
                result.world_pct = pct(result.world_rank);
            }
            const co = country.occupation;
            if (co) {
                Object.assign(result, {year: co.year, country_shares: co.shares.map(pct), country_same: pct(co.shares[idx])});
                if (level) {
                    result.national_rank = skillRank(co.shares, level);
                    result.national_pct = pct(result.national_rank);
                }
                const sexShares = co.by_sex && co.by_sex[answers.sex];
                if (sexShares) result.sex_country_same = pct(sexShares[idx]);
                const areaShares = co.by_area && co.by_area[answers.area];
                if (areaShares) result.area_country_same = pct(areaShares[idx]);
            }
            if (occ.by_sex[answers.sex]) result.sex_pooled_same = pct(occ.by_sex[answers.sex][idx]);
            return result;
        }

        // ------------------------------------------------------------------
        // Living standards
        // ------------------------------------------------------------------

        // Map answers to [hasService: true|false|null, status label] per service.
        function accessItems(answers) {
            const clean = Object.fromEntries(Q.cooking_options.map(([k, , c]) => [k, c]));
            const water = Object.fromEntries(Q.water_options.map(([k, , label]) => [k, label]));
            const sanitation = Object.fromEntries(Q.sanitation_options.map(([k, , label]) => [k, label]));
            const yesNo = v => v === "yes" ? true : v === "no" ? false : null;
            const c = answers.cooking, w = answers.water, s = answers.sanitation;
            return {
                electricity: [yesNo(answers.electricity), null],
                clean_cooking: [c ? clean[c] : null, c === "none" ? L.no_cooking : null],
                water: [w ? w === "safely_managed" : null, water[w] || null],
                sanitation: [s ? s === "safely_managed" : null, sanitation[s] || null],
                hygiene: [yesNo(answers.hygiene), null],
                internet: [yesNo(answers.internet), null],
                health_hardship: [answers.health_hardship === "no" ? true : answers.health_hardship === "yes" ? false : null, null],
            };
        }

        // Share (0-1) of people WITHOUT a service, from a WDI "% with access" value.
        const without = (wdi, code) => {
            const v = value(wdi, code);
            return v === null ? null : Math.max(0, Math.min(1, 1 - v / 100));
        };

        // Average of per-service percentile ranks against the world. For one service
        // with a share s of people lacking it, having it puts you at mid-rank (s + 1)/2
        // and lacking it at s/2. We also report the strict lower bound: at least
        // max(s) of people lack something you have.
        function scoreLiving(answers, country) {
            const items = [];
            const ranks = [];
            const region = regionAggregate(country);
            const suffix = answers.area === "urban" ? ".UR.ZS" : answers.area === "rural" ? ".RU.ZS" : null;
            for (const [key, [has, status]] of Object.entries(accessItems(answers))) {
                const info = F.access[key];
                const svc = SERVICES[key];
                const code = svc.wdi ? `${svc.wdi}.ZS` : null;
                // World figure from the World Bank aggregate, falling back to the cited report.
                const s = (code && without(world, code)) ?? info.share_without;
                const item = {
                    key, label: info.label, has, status,
                    share_without_pct: pct(s),
                    people_without: info.people_without,
                    note: info.note, cite: info.cite, year: (code && year(world, code)) || info.year,
                    wdi: code,
                };
                if (code) {
                    const cw = without(country.wdi, code);
                    if (cw !== null) item.country_without_pct = pct(cw);
                    if (region && without(region.wdi, code) !== null) item.region_without_pct = pct(without(region.wdi, code));
                    if (suffix && svc.area) {
                        const aw = without(country.wdi, svc.wdi + suffix);
                        if (aw !== null) item.area_without_pct = pct(aw);
                    }
                }
                items.push(item);
                if (has !== null && has !== undefined) ranks.push(has ? (s + 1) / 2 : s / 2);
            }
            const answered = items.filter(i => i.has !== null && i.has !== undefined);
            const result = {items, answered: answered.length, area: answers.area || null,
                            region_name: region ? region.name : null};
            if (!answered.length) return result;
            const have = answered.filter(i => i.has);
            return Object.assign(result, {
                global_pct: pct(sum(ranks) / ranks.length),
                lower_bound_pct: have.length ? Math.max(...have.map(i => i.share_without_pct)) : 0,
                lacking: answered.filter(i => !i.has).map(i => i.label),
                account: answers.account ? {has: answers.account === "yes", world: value(world, "FX.OWN.TOTL.ZS"),
                                            country: value(country.wdi, "FX.OWN.TOTL.ZS")} : null,
            });
        }

        // ------------------------------------------------------------------
        // Multidimensional poverty (Global MPI indicators and weights)
        // ------------------------------------------------------------------

        function scoreMpi(answers) {
            const educationAtLeastPrimary = Q.education_options.map(o => o[0]).indexOf(answers.education) >= 1;
            const yes = v => v === "yes" ? true : v === "no" ? false : null;
            const indicators = {
                health: {
                    nutrition: yes(answers.nutrition),
                    child_mortality: yes(answers.child_death),
                },
                education: {
                    years_of_schooling: educationAtLeastPrimary ? false
                        : answers.household_schooling ? answers.household_schooling === "no" : null,
                    school_attendance: answers.school_attendance === "yes" ? true
                        : answers.school_attendance ? false : null,
                },
                living: {
                    cooking_fuel: answers.cooking && answers.cooking !== "none"
                        ? ["biomass", "coal"].includes(answers.cooking) : null,
                    sanitation: answers.sanitation ? !["safely_managed", "basic"].includes(answers.sanitation) : null,
                    drinking_water: answers.water ? !["safely_managed", "basic"].includes(answers.water) : null,
                    electricity: answers.electricity ? answers.electricity === "no" : null,
                    housing: answers.housing ? !answers.housing.includes("none") && answers.housing.length > 0 : null,
                    assets: answers.assets ? (answers.assets.filter(a => Q.small_assets.includes(a)).length <= 1
                                              && !answers.assets.includes("car")) : null,
                },
            };
            const labels = L.mpi;
            // Each dimension weighs 1/3, split equally among its answered indicators;
            // unanswered dimensions are dropped and the rest re-weighted, as the MPI
            // does for missing data.
            const dims = Object.entries(indicators)
                .map(([dim, inds]) => [dim, Object.entries(inds).filter(([, v]) => v !== null)])
                .filter(([, inds]) => inds.length);
            const living = dims.find(([d]) => d === "living");
            if (!living || living[1].length < 4) return {available: false};
            let score = 0;
            const rows = [];
            for (const [dim, inds] of dims) {
                for (const [key, deprived] of inds) {
                    const weight = 1 / dims.length / inds.length;
                    if (deprived) score += weight;
                    rows.push({key, label: labels[key], dimension: dim, deprived, weight});
                }
            }
            const status = score >= 0.5 ? "severe" : score >= 1 / 3 ? "poor" : score >= 0.2 ? "vulnerable" : "not_poor";
            return {
                available: true, score: Math.round(score * 1000) / 10, status, indicators: rows,
                dimensions_used: dims.map(([d]) => d),
                deprived: rows.filter(r => r.deprived).map(r => r.label),
            };
        }

        function scoreCrowding(answers) {
            if (!answers.sleeping_rooms || !answers.household_size) return null;
            const perRoom = answers.household_size / answers.sleeping_rooms;
            return {per_room: Math.round(perRoom * 10) / 10, overcrowded: perRoom > 3};
        }

        // ------------------------------------------------------------------
        // Financial security
        // ------------------------------------------------------------------

        // Food insecurity shares (0-1): severe, moderate (not severe), secure or mild.
        function foodShares(wdi) {
            const ms = value(wdi, "SN.ITK.MSFI.ZS"), sv = value(wdi, "SN.ITK.SVFI.ZS");
            if (ms === null || sv === null) return null;
            return {severe: sv / 100, moderate: (ms - sv) / 100, secure: 1 - ms / 100, year: year(wdi, "SN.ITK.MSFI.ZS")};
        }

        function foodRank(shares, level) {
            if (!shares) return null;
            const order = [shares.severe, shares.moderate, shares.secure];
            const idx = level === "severe" ? 0 : level === "moderate" ? 1 : 2;
            return midrank(order, idx);
        }

        // Account ownership among people like you (Global Findex breakdowns).
        function accountGroups(answers, country, nationalPct) {
            const G_ = L.account_groups;
            const rows = [];
            const add = (label, code) => {
                const w = value(world, code), c = value(country.wdi, code);
                if (w !== null || c !== null) rows.push({label, world: w, country: c});
            };
            if (answers.sex === "F" || answers.sex === "M") add(G_.sex[answers.sex], `FX.OWN.TOTL.${answers.sex === "F" ? "FE" : "MA"}.ZS`);
            if (nationalPct !== undefined) add(nationalPct < 40 ? G_.income.poor : G_.income.rich,
                                               nationalPct < 40 ? "FX.OWN.TOTL.40.ZS" : "FX.OWN.TOTL.60.ZS");
            if (answers.age) add(answers.age === "15-24" ? G_.age.young : G_.age.older,
                                 answers.age === "15-24" ? "FX.OWN.TOTL.YG.ZS" : "FX.OWN.TOTL.OL.ZS");
            const level = Q.education_options.map(o => o[0]).indexOf(answers.education);
            if (level >= 0) add(level <= 1 ? G_.education.low : G_.education.high,
                                level <= 1 ? "FX.OWN.TOTL.PL.ZS" : "FX.OWN.TOTL.SO.ZS");
            return rows;
        }

        // Public programmes the household receives, against ASPIRE coverage in the country
        // (overall and in the user's income fifth). Context only; not scored.
        function scoreSocialProtection(answers, country, incomeNationalPct) {
            const w = country.wdi;
            const result = {};
            const picked = answers.social_protection;
            if (picked) {
                result.received = picked.filter(k => k !== "none");
                result.types = [...new Set(result.received.map(k => Q.social_protection_types[k]))];
            }
            const coverage = {};
            for (const [key, prefix] of SP_PROGRAMMES) {
                const v = value(w, `per_${prefix}.cov_pop_tot`);
                if (v !== null) coverage[key] = v;
            }
            if (Object.keys(coverage).length) {
                result.country = coverage;
                result.year = SP_PROGRAMMES.map(([, prefix]) => year(w, `per_${prefix}.cov_pop_tot`)).find(y => y) || null;
            }
            const quintiles = {};
            for (const [key, prefix] of SP_PROGRAMMES.filter(([k]) => k === "assistance" || k === "insurance")) {
                const q = [1, 2, 3, 4, 5].map(i => value(w, `per_${prefix}.cov_q${i}_tot`));
                if (q.some(v => v !== null)) quintiles[key] = q;
            }
            if (Object.keys(quintiles).length) result.quintiles = quintiles;
            if (incomeNationalPct !== undefined) result.quintile = Math.min(5, Math.floor(incomeNationalPct / 20) + 1);
            const region = regionAggregate(country), group = incomeAggregate(country);
            result.world_any = value(world, "per_allsp.cov_pop_tot");
            result.world_year = year(world, "per_allsp.cov_pop_tot");
            result.region_any = region ? value(region.wdi, "per_allsp.cov_pop_tot") : null;
            result.region_name = region ? region.name : null;
            result.group_any = group ? value(group.wdi, "per_allsp.cov_pop_tot") : null;
            result.group_name = group ? group.name : null;
            result.ilo = F.social_protection;
            return result;
        }

        // Global Findex 2025 resilience: emergency funds (scored), how long expenses could be covered,
        // the main source of emergency money and the biggest financial worry (context).
        function scoreResilience(answers, country) {
            const out = {};
            const fx = country.findex || {};
            const ordered = (group, answer) => {
                const w = G.findex[group];
                const idx = w.keys.indexOf(answer);
                const r = {key: answer, label: L.findex[group][answer], world_shares: w.shares.map(pct),
                           world_pct: pct(midrank(w.shares, idx)), share_below: midrank(w.shares, idx),
                           world_economies: w.economies, labels: w.keys.map(k => L.findex[group][k])};
                if (fx[group]) {
                    Object.assign(r, {country_shares: fx[group].shares.map(pct), year: fx[group].year,
                                      national_pct: pct(midrank(fx[group].shares, idx))});
                }
                return r;
            };
            const choice = (group, answer) => {
                const w = G.findex[group];
                const idx = w.keys.indexOf(answer);
                const r = {key: answer, label: L.findex[group][answer], labels: w.keys.map(k => L.findex[group][k]),
                           world_shares: w.shares.map(pct), world_economies: w.economies};
                if (idx >= 0) r.world_same = pct(w.shares[idx]);
                if (fx[group]) {
                    Object.assign(r, {country_shares: fx[group].shares.map(pct), year: fx[group].year});
                    if (idx >= 0) r.country_same = pct(fx[group].shares[idx]);
                }
                return r;
            };
            if (answers.emergency_funds) out.emergency = ordered("emergency", answers.emergency_funds);
            if (answers.cover_expenses) out.cover_expenses = ordered("cover_expenses", answers.cover_expenses);
            if (answers.emergency_source && answers.emergency_funds && answers.emergency_funds !== "not_possible") {
                out.emergency_source = choice("emergency_source", answers.emergency_source);
            }
            if (answers.worry) out.worry = choice("worry", answers.worry);
            return out;
        }

        function scoreSecurity(answers, country, incomeNationalPct) {
            const result = {};
            const ranks = [];
            const {food_money: food, shelter_money: shelter, count_on: countOn} = answers;
            if (food && shelter && (countOn || (food === "no" && shelter === "no"))) {
                const struggled = food === "yes" || shelter === "yes";
                const group = !struggled ? "low" : (countOn === "yes" ? "moderate" : "high");
                const order = F.gallup_order;
                const shares = order.map(g => F.gallup[g].share);
                const idx = order.indexOf(group);
                Object.assign(result, {
                    gallup_group: group,
                    gallup_label: F.gallup[group].label,
                    gallup_definition: F.gallup[group].definition,
                    gallup_share_pct: pct(shares[idx]),
                    gallup_pct: pct(midrank(shares, idx)),
                });
                ranks.push(midrank(shares, idx));
            }
            const fies = Q.fies_items.map(([k]) => answers[k]);
            if (fies.every(Boolean)) {
                const raw = fies.filter(a => a === "yes").length;
                const level = raw === 0 ? "secure" : raw <= 3 ? "mild" : raw <= 6 ? "moderate" : "severe";
                Object.assign(result, {fies_raw: raw, fies_level: level});
                const ws = foodShares(world), cs = foodShares(country.wdi);
                result.food_world = ws;
                result.food_country = cs;
                if (ws) {
                    result.fies_pct = pct(foodRank(ws, level));
                    ranks.push(foodRank(ws, level));
                }
                if (cs) result.fies_national_pct = pct(foodRank(cs, level));
            }
            result.fies_answered = fies.filter(a => a !== null && a !== undefined).length;
            Object.assign(result, scoreResilience(answers, country));
            if (result.emergency) ranks.push(result.emergency.share_below);
            for (const key of ["account", "saved"]) {
                if (answers[key]) result[key] = answers[key] === "yes";
            }
            result.account_world = value(world, "FX.OWN.TOTL.ZS");
            result.account_country = value(country.wdi, "FX.OWN.TOTL.ZS");
            result.account_groups = accountGroups(answers, country, incomeNationalPct);
            if (ranks.length) result.global_pct = pct(sum(ranks) / ranks.length);
            return result;
        }

        function scoreWealth(answers) {
            const band = answers.wealth;
            if (!band || band === "skip") return {};
            const pyramid = F.wealth_pyramid;
            const idx = pyramid.findIndex(b => b.key === band);
            const shares = pyramid.map(b => b.share);
            const below = sum(shares.slice(0, idx));
            return {
                band: pyramid[idx].label,
                range: [pct(below), pct(below + shares[idx])],
                global_pct: pct(midrank(shares, idx)),
                pyramid: pyramid.map((b, i) => ({label: b.label, pct: pct(b.share), you: i === idx})),
            };
        }

        // ------------------------------------------------------------------
        // Country context
        // ------------------------------------------------------------------

        const GLANCE = [
            ["NY.GDP.PCAP.PP.KD", "money"], ["SP.DYN.LE00.IN", "number"], ["SH.DYN.MORT", "number"],
            ["SP.URB.TOTL.IN.ZS", "pct"], ["SE.ADT.LITR.ZS", "pct"], ["SN.ITK.DEFC.ZS", "pct"],
            ["SL.UEM.TOTL.ZS", "pct"], ["SL.EMP.VULN.ZS", "pct"], ["SH.XPD.OOPC.CH.ZS", "pct"],
            ["EN.POP.SLUM.UR.ZS", "pct"], ["SI.POV.GINI", "number"], ["SI.DST.10TH.10", "pct"], ["SI.DST.FRST.20", "pct"],
            ["SI.POV.NAHC", "pct"], ["GD_WBL_OVL_LAW", "number"], ["HD.HCI.OVRL", "index"],
            ["HD.HCI.EYRS", "number"], ["HD.HCI.LAYS", "number"],
            ["SE.LPV.PRIM", "pct"], ["IT.CEL.SETS.P2", "number"], ["SH.XPD.CHEX.PC.CD", "money"],
        ].map(([code, fmt]) => [code, L.glance[code], fmt]);

        // Total indicator and its female and male versions.
        const SEX_GLANCE = [
            ["SP.DYN.LE00.IN", "SP.DYN.LE00.FE.IN", "SP.DYN.LE00.MA.IN"],
            ["SE.ADT.LITR.ZS", "SE.ADT.LITR.FE.ZS", "SE.ADT.LITR.MA.ZS"],
            ["HD.HCI.OVRL", "HD.HCI.OVRL.FE", "HD.HCI.OVRL.MA"],
        ];

        function scoreLocation(country, answers) {
            const result = {glance: []};
            const region = regionAggregate(country), group = incomeAggregate(country);
            const glance = GLANCE.slice();
            if (answers.sex === "F" || answers.sex === "M") {
                // Swap in the figure for your sex where the country publishes one, and add internet use.
                const fe = answers.sex === "F";
                for (const [total, female, male] of SEX_GLANCE) {
                    const code = fe ? female : male;
                    const at = glance.findIndex(g => g[0] === total);
                    if (at >= 0 && value(country.wdi, code) !== null) glance.splice(at, 1, [code, L.glance[code], glance[at][2]]);
                }
                const net = fe ? "IT.NET.USER.FE.ZS" : "IT.NET.USER.MA.ZS";
                glance.push([net, L.glance[net], "pct"]);
            }
            for (const [code, label, fmt] of glance) {
                const v = value(country.wdi, code);
                if (v === null) continue;
                result.glance.push({code, label, fmt, value: v, year: year(country.wdi, code),
                                    world: value(world, code), region: region ? value(region.wdi, code) : null});
            }
            result.region_name = region ? region.name : null;
            result.income_group = groupLabel(country.income_group);
            result.group_name = group ? group.name : null;
            if (country.income) {
                result.poverty = POVERTY_LINES.map(([line]) => ({line, pct: pct(nationalCdf(country.income, line))}));
                result.median = country.income.median;
                result.mean = country.income.mean;
            }
            if (country.gdp_per_capita_usd !== undefined) {
                const share = country.gdp_pc_population_share_below + country.gdp_pc_population_share_same / 2;
                Object.assign(result, {
                    gdp_per_capita_usd: country.gdp_per_capita_usd,
                    gdp_year: country.gdp_year,
                    global_pct: pct(share),
                    share_in_poorer_countries_pct: pct(country.gdp_pc_population_share_below),
                });
            }
            return result;
        }

        // Map a 0-100 percentile onto the 10-rung MacArthur ladder.
        const ladderRung = p => Math.min(10, Math.max(1, Math.ceil(p / 10)));

        function score(answers, today) {
            today = today || new Date();
            const country = byIso3[answers.country];
            const result = {
                country: {
                    iso3: country.iso3, name: country.name, currency: country.currency,
                    currency_name: country.currency_name, population: country.population,
                    income_group: groupLabel(country.income_group), region: country.region,
                },
                income: scoreIncome(answers, country, today),
                education: scoreEducation(answers, country),
                work: scoreWork(answers, country),
                living: scoreLiving(answers, country),
                mpi: scoreMpi(answers),
                crowding: scoreCrowding(answers),
                security: null,
                wealth: scoreWealth(answers),
                location: scoreLocation(country, answers),
                world_population: G.world_population,
            };
            result.security = scoreSecurity(answers, country, result.income.national_pct);
            result.social_protection = scoreSocialProtection(answers, country, result.income.national_pct);
            result.mobility = scoreMobility(answers, country, today);
            if (country.income) {
                const {survey_year, welfare_type, coverage, estimation_type, reference_year} = country.income;
                result.country.survey = {survey_year, welfare_type, coverage, estimation_type, reference_year};
                result.country.median_ppp = country.income.median;
            }
            result.dimensions = ["income", "education", "work", "living", "security", "wealth"]
                .filter(k => result[k].global_pct !== undefined)
                .map(k => ({key: k, label: DIMENSION_LABELS[k], pct: result[k].global_pct,
                            national_pct: result[k].national_pct}));
            result.ses_index = Math.round(10 * sum(result.dimensions.map(d => d.pct)) / result.dimensions.length) / 10;

            const perception = {measured_rung: ladderRung(result.ses_index)};
            for (const key of ["ladder_country", "ladder_world"]) {
                if (answers[key]) perception[key] = parseInt(answers[key], 10);
            }
            if (perception.ladder_world !== undefined) perception.gap = perception.ladder_world - perception.measured_rung;
            if (result.income.national_pct !== undefined) perception.national_income_rung = ladderRung(result.income.national_pct);
            result.perception = perception;
            return result;
        }

        // The household income in another economy's currency, at today's prices, that gives the same
        // living standard (2021 PPP $ per person per day), and where it ranks there.
        function equivalentIncome(country, pppPerDay, householdSize, period, today) {
            if (!exactIncomeAvailable(country)) return null;
            const level = priceLevel(country.prices, today.getFullYear()).level;
            const perDay = pppPerDay * country.prices.ppp_2021 * level;
            return {
                iso3: country.iso3, name: country.name, currency: country.currency,
                amount: perDay * householdSize * 365 / (period === "year" ? 1 : 12),
                national_pct: country.income ? pct(nationalCdf(country.income, pppPerDay)) : null,
            };
        }

        // Quick income-only ranking, for the what-if simulator.
        function rankIncome(country, x) {
            return {
                global_pct: pct(globalCdf(x)),
                national_pct: country.income ? pct(nationalCdf(country.income, x)) : null,
            };
        }

        return {
            data: D,
            country: iso3 => byIso3[iso3],
            nationalCdf, nationalQuantile, globalCdf, globalQuantile, gridCdf, groupCdf,
            exactIncomeAvailable, parseAnswers, score, rankIncome, toPppPerDay, ladderRung, ValidationError,
            equivalentIncome: (iso3, pppPerDay, householdSize, period, today) =>
                (byIso3[iso3] ? equivalentIncome(byIso3[iso3], pppPerDay, householdSize || 1, period || "month", today || new Date()) : null),
            emergencyAmount: (iso3, today) => (byIso3[iso3] ? emergencyAmount(byIso3[iso3], today || new Date()) : null),
        };
    }

    if (typeof module !== "undefined" && module.exports) {
        module.exports = create;
    } else {
        root.SES = create(root.SES_DATA);
    }
})(typeof window !== "undefined" ? window : globalThis);

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
        const byIso3 = Object.fromEntries(D.countries.map(c => [c.iso3, c]));

        // Above this average annual inflation (or after a currency redenomination) a
        // CPI-based conversion of today's income to 2017 prices isn't trustworthy.
        const MAX_RELIABLE_INFLATION = 1.0;
        const MAX_EXTRAPOLATION_YEARS = 3;
        const MAX_HOUSEHOLD_SIZE = 50;

        const POVERTY_LINES_2017 = [
            [2.15, "International poverty line ($2.15)", "extreme poverty"],
            [3.65, "Lower-middle-income line ($3.65)", "the poverty line typical of lower-middle-income countries"],
            [6.85, "Upper-middle-income line ($6.85)", "the poverty line typical of upper-middle-income countries"],
        ];

        const DIMENSION_LABELS = {
            income: "Income",
            education: "Education",
            living: "Living standards",
            security: "Financial security",
            wealth: "Wealth",
        };

        // ------------------------------------------------------------------
        // Distributions (all incomes per person per day, 2017 international $)
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

        // National distribution: nine decile thresholds, a uniform bottom decile
        // on [low, thr1], log-linear in between, and a Pareto top decile.
        function nationalCdf(dist, x) {
            const thr = dist.thresholds;
            if (x <= 0) return 0;
            if (x < thr[0]) {
                return Math.max(0, Math.min(1, (x - dist.low) / (thr[0] - dist.low))) * 0.1;
            }
            if (x > thr[thr.length - 1]) {
                return 1 - 0.1 * Math.pow(thr[thr.length - 1] / x, dist.pareto_alpha);
            }
            const i = bisect(thr, x);
            if (i >= thr.length - 1) return 0.9;
            const frac = (Math.log(x) - Math.log(thr[i])) / (Math.log(thr[i + 1]) - Math.log(thr[i]));
            return (i + 1 + frac) / 10;
        }

        function nationalQuantile(dist, p) {
            const thr = dist.thresholds;
            if (p <= 0.1) return dist.low + (thr[0] - dist.low) * p / 0.1;
            if (p >= 0.9) return thr[8] * Math.pow(0.1 / Math.max(1 - p, 1e-9), 1 / dist.pareto_alpha);
            const k = p * 10 - 1;
            const i = Math.floor(k);
            const frac = k - i;
            return Math.exp(Math.log(thr[i]) + frac * (Math.log(thr[i + 1]) - Math.log(thr[i])));
        }

        // Global distribution: calibrated CDF on a log-spaced grid.
        function globalCdf(x) {
            const {grid, cdf} = D.global.income;
            if (x <= 0) return 0;
            if (x <= grid[0]) return cdf[0] * x / grid[0];
            if (x >= grid[grid.length - 1]) return cdf[cdf.length - 1];
            const i = bisect(grid, x);
            const l0 = Math.log(grid[i]), l1 = Math.log(grid[i + 1]);
            return cdf[i] + (cdf[i + 1] - cdf[i]) * (Math.log(x) - l0) / (l1 - l0);
        }

        function globalQuantile(p) {
            const {grid, cdf} = D.global.income;
            if (p <= cdf[0]) return cdf[0] ? grid[0] * p / cdf[0] : grid[0];
            if (p >= cdf[cdf.length - 1]) return grid[grid.length - 1];
            let i = bisect(cdf, p);
            while (cdf[i + 1] === cdf[i]) i++;
            const l0 = Math.log(grid[i]), l1 = Math.log(grid[i + 1]);
            return Math.exp(l0 + (l1 - l0) * (p - cdf[i]) / (cdf[i + 1] - cdf[i]));
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
            const prices = country.prices;
            return Boolean(prices) && prices.inflation_recent_annual <= MAX_RELIABLE_INFLATION;
        }

        // Validate answers (plain object of strings) -> clean answers.
        // Throws ValidationError with {field: message}.
        function parseAnswers(form) {
            const answers = {};
            const errors = {};
            for (const q of Q.questions) {
                let value = form[q.id];
                value = typeof value === "string" ? value.trim() : value;
                if ((q.type === "radio" || q.type === "ladder") && value && !q.options.includes(value)) {
                    errors[q.id] = "Please choose one of the options.";
                    continue;
                }
                answers[q.id] = value || null;
            }

            const country = byIso3[answers.country || ""];
            if (!country) errors.country = "Please choose your country.";
            if (!answers.education) errors.education = "Please choose your highest completed level of education.";

            const mode = answers.income_mode;
            if (mode === "exact") {
                if (country && !exactIncomeAvailable(country)) {
                    errors.income_mode = `We don't have reliable price data for ${country.name}, so please pick a range instead.`;
                }
                const amount = toNumber(answers.income_amount);
                const size = toNumber(answers.household_size);
                if (amount === null || amount < 0) {
                    errors.income_amount = "Please enter your household income as a number (0 or more).";
                }
                if (size === null || size < 1 || size > MAX_HOUSEHOLD_SIZE || !Number.isInteger(size)) {
                    errors.household_size = `Please enter a whole number of people from 1 to ${MAX_HOUSEHOLD_SIZE}.`;
                }
                if (answers.income_period !== "month" && answers.income_period !== "year") {
                    errors.income_period = "Please say whether the amount is per month or per year.";
                }
                answers.income_amount = amount;
                answers.household_size = size;
            } else if (mode === "band") {
                if (!answers.income_band) errors.income_band = "Please choose a range.";
            } else {
                errors.income_mode = "Please choose how you'd like to answer the income question.";
            }

            if (Object.keys(errors).length) throw new ValidationError(errors);
            return answers;
        }

        // ------------------------------------------------------------------
        // Dimensions
        // ------------------------------------------------------------------

        const pct = share => Math.round(1000 * share) / 10;
        const people = share => share * D.global.world_population;
        const sum = xs => xs.reduce((a, b) => a + b, 0);
        const midrank = (shares, index) => sum(shares.slice(0, index)) + shares[index] / 2;

        function toPppPerDay(amount, period, householdSize, country, today) {
            const prices = country.prices;
            const perDay = amount * (period === "month" ? 12 : 1) / 365 / householdSize;
            const yearsAhead = Math.max(0, Math.min(today.getFullYear() - prices.inflation_latest_year, MAX_EXTRAPOLATION_YEARS));
            const priceLevel = prices.inflation_factor_since_2017 * Math.pow(1 + prices.inflation_recent_annual, yearsAhead);
            return {
                local_per_day: perDay,
                price_level_vs_2017: priceLevel,
                extrapolated_years: yearsAhead,
                prices_through: prices.inflation_latest_year,
                recent_inflation: prices.inflation_recent_annual,
                ppp_2017: prices.ppp_2017,
                ppp_per_day: perDay / priceLevel / prices.ppp_2017,
            };
        }

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
            result.person_of_100 = Math.min(100, Math.max(1, Math.ceil(share * 100)));
            if (result.national_share !== undefined) result.national_pct = pct(result.national_share);
            result.lines = POVERTY_LINES_2017.map(([line, label, meaning]) => ({
                line, label, meaning, above: x >= line, share_below: pct(globalCdf(line)),
            }));
            result.world_median = D.global.income.world_median;
            result.multiple_of_world_median = x / result.world_median;
            result.chart = incomeChart(country, x);
            return result;
        }

        function scoreEducation(answers, country) {
            const keys = Q.education_options.map(o => o[0]);
            const idx = keys.indexOf(answers.education);
            const edu = D.global.education;
            const world = edu.world_shares;
            const result = {
                level: idx,
                label: Q.education_options[idx][1],
                global_pct: pct(midrank(world, idx)),
                world_shares: world.map(pct),
                same_level_pct: pct(world[idx]),
                higher_pct: pct(sum(world.slice(idx + 1))),
                levels: Q.education_options.map(o => o[1]),
                year: edu.year,
            };
            if (country.education) {
                const shares = country.education.shares;
                result.national_pct = pct(midrank(shares, idx));
                result.country_shares = shares.map(pct);
                result.country_mean_years = country.education.mean_years;
            }
            return result;
        }

        // Map answers to [hasService: true|false|null, status label] per service.
        function accessItems(answers) {
            const clean = Object.fromEntries(Q.cooking_options.map(([k, , c]) => [k, c]));
            const water = Object.fromEntries(Q.water_options.map(([k, , label]) => [k, label]));
            const sanitation = Object.fromEntries(Q.sanitation_options.map(([k, , label]) => [k, label]));
            const yesNo = v => v === "yes" ? true : v === "no" ? false : null;
            const c = answers.cooking, w = answers.water, s = answers.sanitation;
            return {
                electricity: [yesNo(answers.electricity), null],
                clean_cooking: [c ? clean[c] : null, c === "none" ? "No cooking at home" : null],
                water: [w ? w === "safely_managed" : null, water[w] || null],
                sanitation: [s ? s === "safely_managed" : null, sanitation[s] || null],
                hygiene: [yesNo(answers.hygiene), null],
                internet: [yesNo(answers.internet), null],
                health_hardship: [answers.health_hardship === "no" ? true : answers.health_hardship === "yes" ? false : null, null],
            };
        }

        // Average of per-service percentile ranks. For one service with a share s
        // of people lacking it, having it puts you at mid-rank (s + 1)/2 and lacking
        // it at s/2. We also report the strict lower bound: at least max(s) of
        // people lack something you have.
        function scoreLiving(answers) {
            const items = [];
            const ranks = [];
            for (const [key, [has, status]] of Object.entries(accessItems(answers))) {
                const info = F.access[key];
                const s = info.share_without;
                items.push({
                    key, label: info.label, has, status,
                    share_without_pct: pct(s),
                    people_without: info.people_without,
                    note: info.note, cite: info.cite, year: info.year,
                });
                if (has !== null && has !== undefined) ranks.push(has ? (s + 1) / 2 : s / 2);
            }
            const answered = items.filter(i => i.has !== null && i.has !== undefined);
            if (!answered.length) return {items, answered: 0};
            const have = answered.filter(i => i.has);
            return {
                items,
                answered: answered.length,
                global_pct: pct(sum(ranks) / ranks.length),
                lower_bound_pct: have.length ? Math.max(...have.map(i => i.share_without_pct)) : 0,
                lacking: answered.filter(i => !i.has).map(i => i.label),
            };
        }

        function scoreSecurity(answers) {
            const result = {};
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
                    global_pct: pct(midrank(shares, idx)),
                });
            }
            const fies = Q.fies_items.map(([k]) => answers[k]);
            if (fies.every(Boolean)) {
                const raw = fies.filter(a => a === "yes").length;
                const level = raw === 0 ? "secure" : raw <= 3 ? "mild" : raw <= 6 ? "moderate" : "severe";
                Object.assign(result, {fies_raw: raw, fies_level: level});
            }
            result.fies_answered = fies.filter(a => a !== null && a !== undefined).length;
            for (const key of ["account", "saved"]) {
                if (answers[key]) result[key] = answers[key] === "yes";
            }
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

        function scoreLocation(country) {
            if (country.gdp_per_capita_usd === undefined) return {};
            const share = country.gdp_pc_population_share_below + country.gdp_pc_population_share_same / 2;
            return {
                gdp_per_capita_usd: country.gdp_per_capita_usd,
                gdp_year: country.gdp_year,
                global_pct: pct(share),
                share_in_poorer_countries_pct: pct(country.gdp_pc_population_share_below),
            };
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
                },
                income: scoreIncome(answers, country, today),
                education: scoreEducation(answers, country),
                living: scoreLiving(answers),
                security: scoreSecurity(answers),
                wealth: scoreWealth(answers),
                location: scoreLocation(country),
                world_population: D.global.world_population,
            };
            if (country.income) {
                const {survey_year, welfare_type, coverage} = country.income;
                result.country.survey = {survey_year, welfare_type, coverage};
                result.country.median_ppp = country.income.median;
            }
            result.dimensions = ["income", "education", "living", "security", "wealth"]
                .filter(k => result[k].global_pct !== undefined)
                .map(k => ({key: k, label: DIMENSION_LABELS[k], pct: result[k].global_pct}));
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

        return {
            data: D,
            country: iso3 => byIso3[iso3],
            nationalCdf, nationalQuantile, globalCdf, globalQuantile,
            exactIncomeAvailable, parseAnswers, score, ladderRung, ValidationError,
        };
    }

    if (typeof module !== "undefined" && module.exports) {
        module.exports = create;
    } else {
        root.SES = create(root.SES_DATA);
    }
})(typeof window !== "undefined" ? window : globalThis);

// Scorer tests. Run with: python scripts/build_site.py && node --test tests/js/
const test = require("node:test");
const assert = require("node:assert/strict");
const {load} = require("./load");

const SES = load();
const TODAY = new Date(2026, 9, 21);

const FULL = {
    country: "VNM", income_mode: "exact", income_amount: "20,000,000", income_period: "month", household_size: "4",
    education: "tertiary", electricity: "yes", cooking: "gas", water: "safely_managed", sanitation: "safely_managed",
    hygiene: "yes", internet: "yes", health_hardship: "no", food_money: "no", shelter_money: "no", count_on: "yes",
    fies_worried: "no", fies_healthy: "no", fies_few_kinds: "no", fies_skipped: "no", fies_ate_less: "no",
    fies_ran_out: "no", fies_hungry: "no", fies_whole_day: "no", account: "yes", saved: "yes", wealth: "10k_100k",
    ladder_country: "6", ladder_world: "5",
};
const MINIMAL = {country: "USA", income_mode: "band", income_band: "b5", education: "secondary"};
const FIES = Object.keys(FULL).filter(k => k.startsWith("fies_"));

const run = answers => SES.score(SES.parseAnswers(answers), TODAY);
const close = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg || ""} ${a} != ${b} (tol ${tol})`);

test("full answers produce all dimensions", () => {
    const r = run(FULL);
    assert.deepEqual(r.dimensions.map(d => d.key), ["income", "education", "living", "security", "wealth"]);
    assert.ok(r.ses_index > 0 && r.ses_index < 100);
    assert.equal(r.perception.ladder_world, 5);
    assert.ok(r.perception.measured_rung >= 1 && r.perception.measured_rung <= 10);
});

test("income conversion", () => {
    const inc = run(FULL).income;
    const local = 20e6 * 12 / 365 / 4;
    close(inc.local_per_day, local, 1e-6);
    close(inc.ppp_per_day, local / inc.price_level_vs_2017 / inc.ppp_2017, 1e-9);
    assert.equal(inc.extrapolated_years, 2);  // inflation data run to 2024
    assert.ok(inc.global_pct > 0 && inc.global_pct < 100 && inc.national_pct > 0 && inc.national_pct < 100);
});

test("more income ranks higher", () => {
    const low = run({...FULL, income_amount: "5000000"}).income;
    const high = run({...FULL, income_amount: "80000000"}).income;
    assert.ok(high.global_pct > low.global_pct);
    assert.ok(high.national_pct > low.national_pct);
});

test("US household at the national median lands near the 50th percentile", () => {
    const us = SES.country("USA");
    const probe = run({...FULL, country: "USA", income_amount: "1", household_size: "1"}).income;
    const monthly = us.income.median * probe.price_level_vs_2017 * 365 / 12;
    const r = run({...FULL, country: "USA", income_amount: monthly.toFixed(2), household_size: "1"});
    close(r.income.national_pct, 50, 0.2);
    assert.ok(r.income.global_pct > 85);
});

test("yearly period matches monthly", () => {
    const m = run(FULL).income.ppp_per_day;
    const y = run({...FULL, income_amount: "240000000", income_period: "year"}).income.ppp_per_day;
    close(y, m, 1e-9);
});

test("band mode reports a range", () => {
    const r = run(MINIMAL);
    const [lo, hi] = r.income.global_range;
    assert.ok(lo < r.income.global_pct && r.income.global_pct < hi);
    assert.deepEqual(r.dimensions.map(d => d.key), ["income", "education"]);
});

test("zero income is the bottom", () => {
    const inc = run({...FULL, income_amount: "0"}).income;
    assert.equal(inc.global_pct, 0);
    assert.equal(inc.person_of_100, 1);
});

test("education mid-rank", () => {
    assert.ok(run({...MINIMAL, education: "none"}).education.global_pct < 10);
    const top = run({...MINIMAL, education: "tertiary"}).education;
    assert.ok(top.global_pct > 90);
    assert.equal(top.higher_pct, 0);
});

test("living standards", () => {
    const all = run(FULL).living;
    const s = Object.values(SES.data.facts.access).map(a => a.share_without);
    close(all.global_pct, 100 * s.reduce((a, x) => a + (x + 1) / 2, 0) / s.length, 0.1);
    close(all.lower_bound_pct, 100 * Math.max(...s), 0.1);
    const none = run({...FULL, electricity: "no", cooking: "biomass", water: "surface", sanitation: "open",
        hygiene: "no", internet: "no", health_hardship: "yes"}).living;
    assert.ok(none.global_pct < all.global_pct);
    assert.equal(none.lacking.length, 7);
    assert.equal(run({...FULL, cooking: "none"}).living.answered, 6);
});

test("Gallup vulnerability groups", () => {
    const low = run(FULL).security;
    const moderate = run({...FULL, food_money: "yes"}).security;
    const high = run({...FULL, food_money: "yes", count_on: "no"}).security;
    assert.deepEqual([low.gallup_group, moderate.gallup_group, high.gallup_group], ["low", "moderate", "high"]);
    assert.ok(high.global_pct < moderate.global_pct && moderate.global_pct < low.global_pct);
});

test("FIES levels", () => {
    assert.equal(run(FULL).security.fies_level, "secure");
    const five = Object.fromEntries(FIES.slice(0, 5).map(k => [k, "yes"]));
    assert.equal(run({...FULL, ...five}).security.fies_level, "moderate");
    const all = Object.fromEntries(FIES.map(k => [k, "yes"]));
    const sec = run({...FULL, ...all}).security;
    assert.equal(sec.fies_raw, 8);
    assert.equal(sec.fies_level, "severe");
});

test("wealth", () => {
    assert.deepEqual(run({...FULL, wealth: "skip"}).wealth, {});
    assert.deepEqual(run({...FULL, wealth: "over_1m"}).wealth.range, [98.5, 100]);
});

for (const [field, value] of [
    ["country", "XXX"], ["income_mode", ""], ["income_amount", "abc"], ["income_amount", "-5"],
    ["income_amount", "12abc"], ["household_size", "0"], ["household_size", "2.5"], ["education", ""],
    ["water", "not-an-option"],
]) {
    test(`validation: ${field}=${JSON.stringify(value)}`, () => {
        assert.throws(() => SES.parseAnswers({...FULL, [field]: value}),
            e => e instanceof SES.ValidationError && field in e.errors);
    });
}

test("exact mode is rejected without reliable prices", () => {
    for (const iso3 of ["ZWE", "CHL"]) {
        assert.throws(() => SES.parseAnswers({...FULL, country: iso3}),
            e => e instanceof SES.ValidationError && "income_mode" in e.errors);
    }
});

test("country without a survey has no national rank", () => {
    const inc = run({...MINIMAL, country: "SAU"}).income;
    assert.equal(inc.national_pct, undefined);
    assert.equal(inc.national_available, false);
});

test("every country can be scored with a range", () => {
    for (const c of SES.data.countries) {
        const r = run({...MINIMAL, country: c.iso3});
        assert.ok(Number.isFinite(r.ses_index), c.iso3);
    }
});

test("every country with reliable prices can be scored exactly", () => {
    for (const c of SES.data.countries.filter(SES.exactIncomeAvailable)) {
        const r = run({...FULL, country: c.iso3, income_amount: "1000"});
        assert.ok(Number.isFinite(r.income.ppp_per_day) && r.income.ppp_per_day > 0, c.iso3);
    }
});

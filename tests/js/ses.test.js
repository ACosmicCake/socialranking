// Scorer tests. Run with: python scripts/build_site.py && node --test tests/js/
const test = require("node:test");
const assert = require("node:assert/strict");
const {load} = require("./load");

const SES = load();
const TODAY = new Date(2026, 9, 21);

const FULL = {
    country: "VNM", income_mode: "exact", income_amount: "20,000,000", income_period: "month", household_size: "4",
    education: "bachelor", electricity: "yes", cooking: "gas", water: "safely_managed", sanitation: "safely_managed",
    hygiene: "yes", internet: "yes", health_hardship: "no", food_money: "no", shelter_money: "no", count_on: "yes",
    fies_worried: "no", fies_healthy: "no", fies_few_kinds: "no", fies_skipped: "no", fies_ate_less: "no",
    fies_ran_out: "no", fies_hungry: "no", fies_whole_day: "no", account: "yes", saved: "yes", wealth: "10k_100k",
    ladder_country: "6", ladder_world: "5",
};
const MINIMAL = {country: "USA", income_mode: "band", income_band: "b5", education: "upper_secondary"};
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
    close(inc.ppp_per_day, local / inc.price_level_vs_2021 / inc.ppp_2021, 1e-9);
    assert.equal(inc.price_year, 2026);
    assert.equal(inc.extrapolated_years, 0);  // IMF data run to 2026
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
    const monthly = us.income.median * probe.price_level_vs_2021 * 365 / 12;
    const r = run({...FULL, country: "USA", income_amount: monthly.toFixed(2), household_size: "1"});
    close(r.income.national_pct, 50, 0.5);
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
    assert.ok(run({...MINIMAL, education: "below_primary"}).education.global_pct < 15);
    const top = run({...MINIMAL, education: "doctoral"}).education;
    assert.ok(top.global_pct > 99);
    assert.equal(top.higher_pct, 0);
    const levels = SES.data.questionnaire.education_options.map(o => o[0]);
    const pcts = levels.map(l => run({...MINIMAL, education: l}).education.global_pct);
    assert.ok(pcts.every((v, i) => i === 0 || v > pcts[i - 1]), "education ranks must rise with level");
});

test("education by age and sex", () => {
    const e = run({...FULL, age: "25-34", sex: "F"}).education;
    assert.equal(e.group.age, "25-34");
    assert.equal(e.group.sex, "F");
    assert.ok(e.group.world_pct > 0 && e.group.country_pct > 0);
    assert.equal(run({...FULL, age: "15-24"}).education.group, undefined);
});

test("living standards", () => {
    const all = run(FULL).living;
    const s = all.items.map(i => i.share_without_pct / 100);
    close(all.global_pct, 100 * s.reduce((a, x) => a + (x + 1) / 2, 0) / s.length, 0.2);
    close(all.lower_bound_pct, 100 * Math.max(...s), 0.1);
    const none = run({...FULL, electricity: "no", cooking: "biomass", water: "surface", sanitation: "open",
        hygiene: "no", internet: "no", health_hardship: "yes"}).living;
    assert.ok(none.global_pct < all.global_pct);
    assert.equal(none.lacking.length, 7);
    const vnm = run({...FULL, area: "rural"}).living.items.find(i => i.key === "electricity");
    assert.ok(vnm.country_without_pct !== undefined && vnm.area_without_pct !== undefined && vnm.region_without_pct !== undefined);
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
    for (const iso3 of ["ZWE", "VEN", "CUB"]) {
        assert.throws(() => SES.parseAnswers({...FULL, country: iso3}),
            e => e instanceof SES.ValidationError && "income_mode" in e.errors);
    }
});

test("every economy has a national distribution", () => {
    for (const c of SES.data.countries) {
        assert.ok(c.income, c.iso3);
        assert.equal(run({...MINIMAL, country: c.iso3}).income.national_available, true);
    }
});

test("countries that changed currency accept today's currency", () => {
    // 1,000 euro/month per person in Croatia and in Slovakia should be in the same ballpark.
    const hrv = run({...FULL, country: "HRV", income_amount: "1000", household_size: "1"}).income;
    const svk = run({...FULL, country: "SVK", income_amount: "1000", household_size: "1"}).income;
    assert.ok(hrv.ppp_per_day / svk.ppp_per_day > 0.6 && hrv.ppp_per_day / svk.ppp_per_day < 1.6);
    assert.ok(hrv.currency_change);
});

test("price index runs to the visitor's year, extrapolating at most 3 years", () => {
    const later = SES.score(SES.parseAnswers(FULL), new Date(2031, 0, 1)).income;
    assert.equal(later.price_year, 2029);
    assert.equal(later.extrapolated_years, 3);
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

test("work status", () => {
    const emp = run({...FULL, work_status: "employee", work_sector: "services"}).work;
    const own = run({...FULL, work_status: "own_account"}).work;
    assert.ok(emp.global_pct > own.global_pct);
    assert.equal(emp.sector, "services");
    const shares = emp.world;
    close(shares.employee + shares.employer + shares.own_account + shares.family_worker, 100, 3);
    const student = run({...FULL, work_status: "student"});
    assert.equal(student.work.global_pct, undefined);
    assert.ok(!student.dimensions.some(d => d.key === "work"));
});

const MPI_ITEMS = {electricity: "yes", cooking: "gas", water: "safely_managed", sanitation: "safely_managed",
    housing: "none", assets: "phone,tv", school_attendance: "no", nutrition: "no", child_death: "no"};

test("MPI: not poor, poor and severe", () => {
    const ok = run({...FULL, ...MPI_ITEMS}).mpi;
    assert.equal(ok.status, "not_poor");
    assert.equal(ok.score, 0);
    const poor = run({...FULL, ...MPI_ITEMS, education: "below_primary", household_schooling: "no",
        school_attendance: "yes"}).mpi;
    close(poor.score, 33.3, 0.1);
    assert.equal(poor.status, "poor");
    const severe = run({...FULL, ...MPI_ITEMS, education: "below_primary", household_schooling: "no",
        school_attendance: "yes", cooking: "biomass", water: "surface", sanitation: "open", electricity: "no",
        housing: "floor,walls", assets: "radio", nutrition: "yes"}).mpi;
    assert.equal(severe.status, "severe");
    close(severe.score, 83.3, 0.1);  // every indicator except child mortality
});

test("MPI re-weights skipped indicators and needs living standards", () => {
    const m = run({...FULL, ...MPI_ITEMS, nutrition: "skip", child_death: "skip"}).mpi;
    assert.deepEqual(m.dimensions_used, ["education", "living"]);
    close(m.indicators.reduce((a, i) => a + i.weight, 0), 1, 1e-9);
    assert.equal(run(MINIMAL).mpi.available, false);
});

test("checkbox answers are validated", () => {
    assert.deepEqual(SES.parseAnswers({...FULL, assets: "tv,phone,tv"}).assets, ["tv", "phone"]);
    assert.throws(() => SES.parseAnswers({...FULL, assets: "tv,spaceship"}), e => "assets" in e.errors);
    assert.throws(() => SES.parseAnswers({...FULL, housing: "none,floor"}), e => "housing" in e.errors);
    assert.throws(() => SES.parseAnswers({...FULL, assets: "none,tv"}), e => "assets" in e.errors);
    assert.equal(SES.parseAnswers({...FULL, assets: ""}).assets, null);
    const nothing = run({...FULL, ...MPI_ITEMS, assets: "none"}).mpi.indicators.find(i => i.key === "assets");
    assert.equal(nothing.deprived, true);
});

test("crowding uses household size", () => {
    const c = run({...FULL, household_size: "7", sleeping_rooms: "2"}).crowding;
    assert.equal(c.per_room, 3.5);
    assert.equal(c.overcrowded, true);
});

test("food security uses FAO world and country shares", () => {
    const sec = run(FULL).security;
    assert.ok(sec.fies_pct > 50 && sec.fies_national_pct > 0);
    const all = Object.fromEntries(FIES.map(k => [k, "yes"]));
    assert.ok(run({...FULL, ...all}).security.fies_pct < 10);
});

test("income everywhere, regions and history", () => {
    const inc = run(FULL).income;
    assert.equal(inc.everywhere.countries.length, SES.data.countries.length);
    assert.ok(inc.region && inc.region.code === "EAS");
    assert.equal(inc.everywhere.groups.length, 4);
    const years = inc.history.map(h => h.year);
    assert.deepEqual(years, [...years].sort());
    assert.ok(inc.history[0].pct > inc.history[inc.history.length - 1].pct, "same income ranks lower as the world grows");
});

test("China has urban and rural distributions", () => {
    const urban = run({...MINIMAL, country: "CHN", area: "urban"}).income;
    const rural = run({...MINIMAL, country: "CHN", area: "rural"}).income;
    assert.ok(urban.area_pct < rural.area_pct);
});

test("Vietnamese bundle gives the same numbers with translated labels", () => {
    const VI = load("data.vi.js");
    const en = run(FULL);
    const vi = VI.score(VI.parseAnswers(FULL), TODAY);
    assert.equal(vi.ses_index, en.ses_index);
    assert.deepEqual(vi.dimensions.map(d => d.pct), en.dimensions.map(d => d.pct));
    assert.equal(vi.dimensions[0].label, "Thu nhập");
    assert.equal(vi.country.name, "Việt Nam");
    assert.throws(() => VI.parseAnswers({...FULL, education: ""}), e => /trình độ/.test(e.errors.education));
});

test("comparisons by sex", () => {
    const r = run({...FULL, sex: "F", age: "25-34"});
    assert.equal(r.education.sex, "F");
    assert.ok(r.education.world_sex_pct > 0 && r.education.national_sex_pct > 0);
    assert.equal(r.education.country_sex_shares.length, 9);
    assert.ok(r.work.sex_world && r.work.sex_country);
    assert.ok(r.work.sex_participation.country > 0);
    assert.ok(r.location.glance.some(g => g.code === "SP.DYN.LE00.FE.IN"));
    assert.equal(run(FULL).education.sex, undefined);
});

test("account ownership among people like you", () => {
    const groups = run({...FULL, sex: "M", age: "15-24"}).security.account_groups;
    assert.ok(groups.length >= 3);
    assert.ok(groups.every(g => g.world > 0 && g.world <= 100));
});

test("national history and survey basis", () => {
    const inc = run(FULL).income;
    assert.ok(inc.national_history.years[0] <= 1990);
    assert.equal(inc.national_history.years.length, inc.national_history.median.length);
    assert.equal(inc.basis_mismatch, false);  // no basis given
    assert.equal(run({...FULL, income_basis: "income"}).income.basis_mismatch, true);  // Vietnam surveys consumption
    assert.equal(run({...FULL, income_basis: "consumption"}).income.basis_mismatch, false);
    const rich = run({...FULL, income_amount: "1000000000"}).income;
    assert.equal(rich.national_history.reached, null);
});

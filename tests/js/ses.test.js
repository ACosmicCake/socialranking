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
    const r = run({...FULL, sex: "F", age: "25-34", work_status: "employee", work_sector: "services"});
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

test("rank sensitivity to misreported income", () => {
    const inc = run(FULL).income;
    assert.equal(inc.sensitivity.error, 0.2);
    assert.ok(inc.sensitivity.global[0] < inc.global_pct && inc.global_pct < inc.sensitivity.global[1]);
    assert.ok(inc.sensitivity.national[0] < inc.national_pct && inc.national_pct < inc.sensitivity.national[1]);
    assert.equal(run(MINIMAL).income.sensitivity, undefined);  // a band already shows its range
});

test("income thresholds convert back to the household's currency", () => {
    const inc = run(FULL).income;
    const median = inc.thresholds.find(t => t.scope === "country" && t.pct === 50);
    close(median.ppp_per_day, SES.country("VNM").income.median, 0.05);
    // Entering the threshold's local amount gives back the threshold's rank.
    const back = run({...FULL, income_amount: String(median.local)}).income;
    close(back.national_pct, 50, 0.2);
    close(back.ppp_per_day, median.ppp_per_day, 1e-6);
    const top1 = inc.thresholds.find(t => t.scope === "world" && t.pct === 99);
    close(SES.globalCdf(top1.ppp_per_day), 0.99, 1e-3);
    assert.equal(top1.reached, inc.ppp_per_day >= top1.ppp_per_day);
    assert.ok(run(MINIMAL).income.thresholds.every(t => t.local === null));
});

test("social protection against national coverage", () => {
    const sp = run({...FULL, social_protection: "contributory_pension,cash_transfer"}).social_protection;
    assert.deepEqual(sp.types.sort(), ["assistance", "insurance"]);
    assert.ok(sp.country.any > 0 && sp.country.any <= 100);
    assert.equal(sp.quintiles.assistance.length, 5);
    assert.ok(sp.quintile >= 1 && sp.quintile <= 5);
    assert.ok(sp.world_any > 40 && sp.world_any < 70);
    assert.equal(sp.ilo.covered_share, 0.524);
    assert.deepEqual(run({...FULL, social_protection: "none"}).social_protection.received, []);
    assert.equal(run(FULL).social_protection.received, undefined);
    assert.throws(() => SES.parseAnswers({...FULL, social_protection: "none,in_kind"}), SES.ValidationError);
});

test("human capital, learning poverty and connectivity in the country glance", () => {
    const codes = run(FULL).location.glance.map(g => g.code);
    for (const code of ["HD.HCI.OVRL", "SE.LPV.PRIM", "IT.CEL.SETS.P2", "SH.XPD.CHEX.PC.CD"]) assert.ok(codes.includes(code), code);
    const hci = run(FULL).location.glance.find(g => g.code === "HD.HCI.OVRL");
    assert.ok(hci.value > 0 && hci.value < 1);
});

test("healthy diet affordability uses the same prices as income", () => {
    const hd = run(FULL).income.healthy_diet;
    assert.equal(hd.income_share_rule, 0.52);
    assert.ok(hd.cost_2021ppp > 1 && hd.cost_2021ppp < 10);
    close(hd.share_of_income, hd.cost_2021ppp / run(FULL).income.ppp_per_day, 1e-9);
    assert.equal(hd.affordable, true);
    // At about 1.6 times the cost, the diet takes more than 52% of income.
    const poor = run({...FULL, income_amount: String(hd.cost_local_today * 30 * 4 / 0.6)}).income.healthy_diet;
    assert.equal(poor.affordable, false);
    assert.ok(hd.world.unaffordable_share > 0.2 && hd.world.unaffordable_share < 0.5);
    assert.ok(hd.unaffordable_pct >= 0 && hd.unaffordable_pct <= 100);
});

test("Findex emergency money joins the financial-security score", () => {
    const base = run(FULL).security;
    const weak = run({...FULL, emergency_funds: "not_possible"}).security;
    const strong = run({...FULL, emergency_funds: "not_difficult"}).security;
    assert.ok(weak.global_pct < base.global_pct && base.global_pct < strong.global_pct);
    assert.ok(weak.emergency.world_pct < 10 && strong.emergency.world_pct > 80);
    assert.equal(strong.emergency.country_shares.length, 4);
    close(strong.emergency.world_shares.reduce((a, b) => a + b), 100, 0.2);
    assert.ok(strong.emergency.national_pct > 0);
});

test("Findex context items", () => {
    const sec = run({...FULL, emergency_funds: "very_difficult", emergency_source: "family",
                     cover_expenses: "one_month", worry: "medical"}).security;
    assert.ok(sec.emergency_source.world_same > 10 && sec.emergency_source.country_same > 10);
    assert.ok(sec.cover_expenses.world_pct > 0 && sec.cover_expenses.national_pct > 0);
    assert.ok(sec.worry.world_same > 0);
    assert.equal(run({...FULL, worry: "none"}).security.worry.world_same, undefined);
    // The source is only asked of people who could raise the money.
    assert.equal(run({...FULL, emergency_funds: "not_possible", emergency_source: "family"}).security.emergency_source, undefined);
});

test("emergency amount is 1/20 of GNI per person at today's prices", () => {
    const a = SES.emergencyAmount("VNM", TODAY);
    const c = SES.country("VNM");
    const expected = c.findex.emergency_amount.lcu * c.prices.price_index[TODAY.getFullYear()]
        / c.prices.price_index[c.findex.emergency_amount.year];
    close(a.amount, expected, expected * 0.05);
    assert.equal(a.currency, "VND");
    assert.equal(SES.emergencyAmount("LBR", TODAY), null);  // currency units don't match
});

test("occupation by ISCO-08 skill level joins the work score", () => {
    const base = {...FULL, country: "BRA", income_mode: "band", income_band: "b4", work_status: "employee",
                  work_sector: "services", sex: "F", area: "urban"};
    const statusOnly = run(base).work;
    const prof = run({...base, occupation: "professionals"}).work;
    const elem = run({...base, occupation: "elementary"}).work;
    assert.equal(statusOnly.occupation, undefined);
    assert.equal(prof.occupation.skill_level, 4);
    assert.ok(prof.occupation.world_pct > 80 && elem.occupation.world_pct < 20);
    assert.ok(prof.global_pct > statusOnly.global_pct && elem.global_pct < statusOnly.global_pct);
    close(prof.global_pct, (prof.status_pct + prof.occupation.world_pct) / 2, 0.1);
    assert.ok(prof.occupation.national_pct > 0 && prof.occupation.country_same > 0);
    assert.ok(prof.occupation.sex_country_same > 0 && prof.occupation.area_country_same > 0);
    // Armed forces span skill levels: shown but not ranked.
    const army = run({...base, occupation: "armed_forces"}).work;
    assert.equal(army.occupation.world_pct, undefined);
    assert.equal(army.global_pct, statusOnly.global_pct);
    // No usable survey for Vietnam: the pooled comparison still works.
    const vn = run({...FULL, work_status: "employee", work_sector: "services", occupation: "clerks"}).work.occupation;
    assert.equal(vn.country_shares, undefined);
    assert.ok(vn.world_pct > 0);
});

test("social mobility against parents' generation", () => {
    const base = {...FULL, age: "25-34", sex: "F", mother_education: "primary", father_education: "secondary"};
    const m = run(base).mobility;
    assert.equal(m.cohort_year, 2005);  // parents born about 1966, aged 35-44 in 2005
    assert.equal(m.parents.length, 2);
    assert.equal(m.best, "father");
    assert.equal(m.direction, "up");  // bachelor's is tertiary
    assert.ok(m.own_national_pct > m.parents[1].national_pct);
    close(m.rank_change, m.own_national_pct - m.parents[1].national_pct, 0.11);
    // Older users are matched to earlier generations.
    assert.equal(run({...base, age: "65plus"}).mobility.cohort_year, 1965);
    assert.equal(run({...base, age: "15-24"}).mobility.rank_change, undefined);
    assert.equal(run({...base, education: "primary"}).mobility.direction, "down");
    assert.deepEqual(run({...FULL, mother_education: "dont_know"}).mobility, {});
    assert.equal(run({...FULL, mother_education: "tertiary"}).mobility.needs_age, true);
});

test("Human Capital Index components and the index for your sex", () => {
    const glance = run({...FULL, sex: "F"}).location.glance;
    const codes = glance.map(g => g.code);
    assert.ok(codes.includes("HD.HCI.OVRL.FE") && !codes.includes("HD.HCI.OVRL"));
    const eyrs = glance.find(g => g.code === "HD.HCI.EYRS"), lays = glance.find(g => g.code === "HD.HCI.LAYS");
    assert.ok(lays.value > 0 && lays.value < eyrs.value && eyrs.value <= 14);
    assert.ok(run(FULL).location.glance.some(g => g.code === "HD.HCI.OVRL"));
});

test("the same living standard in another currency", () => {
    const inc = run(FULL).income;
    // Back in Vietnam, the equivalent is the household's own income.
    const home = SES.equivalentIncome("VNM", inc.ppp_per_day, 4, "month", TODAY);
    close(home.amount, 20e6, 1);
    close(home.national_pct, inc.national_pct, 0.05);
    const us = SES.equivalentIncome("USA", inc.ppp_per_day, 4, "month", TODAY);
    assert.equal(us.currency, "USD");
    assert.ok(us.amount > 1000 && us.amount < 20000 && us.national_pct < inc.national_pct);
    assert.equal(SES.equivalentIncome("ZWE", inc.ppp_per_day, 4, "month", TODAY), null);  // no reliable prices
});

test("inequality and national poverty in the country overview", () => {
    const g = Object.fromEntries(run(FULL).location.glance.map(x => [x.code, x.value]));
    assert.ok(g["SI.DST.10TH.10"] > g["SI.DST.FRST.20"]);
    assert.ok(g["SI.POV.NAHC"] >= 0 && g["SI.POV.NAHC"] <= 100);
});

test("women's legal equality in the country overview", () => {
    const wbl = run(FULL).location.glance.find(g => g.code === "GD_WBL_OVL_LAW");
    assert.ok(wbl.value > 0 && wbl.value <= 100 && wbl.world > 0);
});

test("literacy and internet use for your sex", () => {
    const codes = run({...FULL, sex: "M"}).location.glance.map(g => g.code);
    assert.ok(codes.includes("SE.ADT.LITR.MA.ZS") && !codes.includes("SE.ADT.LITR.ZS"));
    assert.ok(codes.includes("IT.NET.USER.MA.ZS") && codes.includes("SP.DYN.LE00.MA.IN") && codes.includes("HD.HCI.OVRL.MA"));
    assert.ok(run(FULL).location.glance.some(g => g.code === "SE.ADT.LITR.ZS"));
});

test("air pollution and safety in the country overview", () => {
    const g = Object.fromEntries(run(FULL).location.glance.map(x => [x.code, x]));
    assert.ok(g["EN.ATM.PM25.MC.M3"].value > 0 && g["EN.ATM.PM25.MC.M3"].world > 5);
    assert.equal(g["VC.IHR.PSRC.P5"], undefined);  // Vietnam's latest figure (2011) is older than the cut-off
    const us = run({...FULL, country: "USA", income_mode: "band", income_band: "b5"}).location.glance;
    assert.ok(us.find(x => x.code === "VC.IHR.PSRC.P5").value > 0);
});

test("child stunting and schooling rates in the country overview", () => {
    const g = Object.fromEntries(run(FULL).location.glance.map(x => [x.code, x]));
    assert.ok(g["SH.STA.STNT.ZS"].value > 0 && g["SH.STA.STNT.ZS"].value < 100);
    assert.ok(g["SE.PRM.CMPT.ZS"].world > 50 && g["SE.TER.ENRR"].world > 0);
});

test("population rank of the country on each indicator", () => {
    const g = Object.fromEntries(run(FULL).location.glance.map(x => [x.code, x]));
    assert.equal(g["SP.URB.TOTL.IN.ZS"].better_than_pct, null);
    for (const code of ["SP.DYN.LE00.IN", "EN.ATM.PM25.MC.M3", "NY.GDP.PCAP.PP.KD"]) {
        assert.ok(g[code].better_than_pct > 0 && g[code].better_than_pct < 100, code);
    }
    // Lower is better for pollution: the country with the cleanest air beats almost everyone.
    const pm = SES.data.countries.filter(c => c.wdi && c.wdi["EN.ATM.PM25.MC.M3"]).sort((a, b) => a.wdi["EN.ATM.PM25.MC.M3"][1] - b.wdi["EN.ATM.PM25.MC.M3"][1]);
    const cleanest = run({...FULL, country: pm[0].iso3, income_mode: "band", income_band: "b4"}).location.glance.find(x => x.code === "EN.ATM.PM25.MC.M3");
    assert.ok(cleanest.better_than_pct > 95);
});

test("plausible ranges for each dimension and the SES index", () => {
    const r = run({...FULL, work_status: "employee", work_sector: "services", occupation: "professionals", emergency_funds: "somewhat_difficult"});
    for (const d of r.dimensions) {
        assert.ok(d.range[0] <= d.pct && d.pct <= d.range[1], `${d.key} ${d.range} ${d.pct}`);
    }
    assert.ok(r.ses_index_range[0] <= r.ses_index && r.ses_index <= r.ses_index_range[1]);
    // A category's range is its band: education "bachelor" spans the share of adults at that level.
    const edu = r.dimensions.find(d => d.key === "education");
    close(edu.range[1] - edu.range[0], r.education.same_level_pct, 0.2);
    // Exact incomes use the +/-20% sensitivity.
    assert.deepEqual(r.dimensions.find(d => d.key === "income").range, r.income.sensitivity.global);
});

test("the slim quiz bundle validates exactly like the full one", () => {
    const QUIZ = load("data.quiz.js");
    for (const answers of [FULL, MINIMAL, {...FULL, income_amount: ""}, {...FULL, country: "ZWE"}, {...FULL, education: ""},
                           {...FULL, social_protection: "none,in_kind"}, {...FULL, sleeping_rooms: "0"}]) {
        const outcome = S => { try { return S.parseAnswers(answers); } catch (e) { return e.errors; } };
        assert.deepEqual(outcome(QUIZ), outcome(SES));
    }
    assert.deepEqual(QUIZ.emergencyAmount("VNM", TODAY), SES.emergencyAmount("VNM", TODAY));
    assert.equal(QUIZ.exactIncomeAvailable(QUIZ.country("ZWE")), SES.exactIncomeAvailable(SES.country("ZWE")));
    const VIQ = load("data.quiz.vi.js");
    assert.throws(() => VIQ.parseAnswers({...FULL, education: ""}), e => /trình độ/.test(e.errors.education));
});

test("health system capacity in the country overview", () => {
    const g = Object.fromEntries(run(FULL).location.glance.map(x => [x.code, x]));
    for (const code of ["SH.MED.PHYS.ZS", "SH.MED.NUMW.P3", "SH.MED.BEDS.ZS"]) {
        assert.ok(g[code] && g[code].value > 0 && g[code].better_than_pct > 0, code);
    }
});

test("age against the world's and the country's population", () => {
    const young = run({...FULL, age: "15-24"}).age, old = run({...FULL, age: "65plus", sex: "F"}).age;
    assert.ok(young.world_pct > 20 && young.world_pct < 50, young.world_pct);
    assert.ok(old.world_pct > 85 && old.national_pct > 80 && old.national_sex_pct > 0);
    assert.deepEqual(run(FULL).age, {});  // no age given
    close(SES.data.global.age_structure.shares.reduce((a, b) => a + b), 1, 1e-3);
});

test("Mobile phone is ranked as context only", () => {
    const smart = run({...FULL, phone: "smartphone"}).living;
    const basic = run({...FULL, phone: "basic"}).living;
    const none = run({...FULL, phone: "none"}).living;
    assert.ok(smart.phone.world_pct > basic.phone.world_pct && basic.phone.world_pct > none.phone.world_pct);
    assert.ok(smart.phone.national_pct > 0 && smart.phone.year >= 2021);
    close(smart.phone.world_shares.reduce((a, b) => a + b), 100, 0.2);
    // Not part of the living-standards score.
    assert.equal(smart.global_pct, run(FULL).living.global_pct);
    assert.equal(run(FULL).living.phone, undefined);
    // Women and rural adults in Viet Nam, where Findex reports the breakdowns.
    const groups = run({...FULL, phone: "basic", sex: "F", area: "rural"}).living.phone.groups;
    assert.deepEqual(groups.map(g => g.key), ["F", "rural"]);
    for (const g of groups) assert.ok(g.pct > 0 && g.pct < 50);
    assert.deepEqual(smart.phone.groups, []);
});

test("Saving, borrowing and digital payments are compared with Findex", () => {
    const sec = run({...FULL, sex: "F", area: "urban", saved: "yes", borrowed: "no", digital_payment: "yes"}).security;
    assert.deepEqual(sec.findex_yes.map(y => y.key), ["saved", "borrowed", "digital_payment"]);
    // Old-age saving: asked only of savers, so not saving counts as no; pooled over surveyed economies.
    const old = run({...FULL, saved: "no", saved_old_age: "yes"}).security.findex_yes.find(y => y.key === "saved_old_age");
    assert.equal(old.has, false);
    assert.ok(old.world_partial && old.world > 5 && old.world < 40 && old.country > 0);
    assert.equal(sec.findex_yes.find(y => y.key === "saved").world_partial, false);
    for (const y of sec.findex_yes) assert.ok(y.world > 5 && y.world < 90 && y.country > 0 && y.year >= 2021);
    // Splits only where Findex reports them (not for borrowing in Viet Nam).
    assert.deepEqual(sec.findex_yes[0].groups.map(g => g.key), ["F", "urban"]);
    assert.deepEqual(sec.findex_yes[1].groups, []);
    assert.equal(sec.findex_yes[1].has, false);
    // Context only: the security score doesn't change.
    assert.equal(sec.global_pct, run(FULL).security.global_pct);
});

test("youth, gender and demography indicators in the country glance", () => {
    const glance = run(FULL).location.glance;
    const get = code => glance.find(g => g.code === code);
    for (const code of ["SL.UEM.NEET.ZS", "SG.GEN.PARL.ZS", "SH.STA.MMRT", "SP.ADO.TFRT"]) {
        assert.ok(get(code) && get(code).better_than_pct > 0, code);
    }
    // Fertility and women's labour-force participation are shown but not ranked.
    assert.equal(get("SP.DYN.TFRT.IN").better_than_pct, null);
    assert.equal(get("SL.TLF.CACT.FE.ZS").better_than_pct, null);
});

test("missing world and regional aggregates are estimated, except for inequality", () => {
    const glance = run(FULL).location.glance;
    const get = code => glance.find(g => g.code === code);
    const neet = get("SL.UEM.NEET.ZS");
    assert.ok(neet.world_estimated && neet.world > 5 && neet.world < 35);
    // No estimate when the economies with data hold under half the population (China has no NEET figure).
    assert.equal(neet.region, null);
    const gender = get("GD_WBL_OVL_LAW");
    assert.ok(gender.region_estimated && gender.region > 30 && gender.region < 100);
    assert.ok(get("HD.HCI.OVRL").world > 0.4 && get("HD.HCI.OVRL").world < 0.8);
    // Published aggregates are left alone; Gini is never averaged.
    assert.equal(get("SP.DYN.LE00.IN").world_estimated, undefined);
    assert.equal(get("SI.POV.GINI").world, null);
});

test("country glance compares with the income group", () => {
    const loc = run(FULL).location;
    assert.ok(loc.group_name);
    const le = loc.glance.find(g => g.code === "SP.DYN.LE00.IN");
    assert.ok(le.group > 50 && le.group < 90 && le.group_estimated === undefined);
    const hci = loc.glance.find(g => g.code === "HD.HCI.OVRL");
    assert.ok(hci.group_estimated && hci.group > 0.3 && hci.group < 0.8);
});

test("account ownership among rural or urban adults", () => {
    const groups = run({...FULL, area: "rural"}).security.account_groups;
    const rural = groups.find(g => g.label === "Rural adults");
    assert.ok(rural && rural.world > 60 && rural.world < 90 && rural.country > 40 && rural.country < 95);
    assert.equal(run(FULL).security.account_groups.find(g => g.label === "Rural adults"), undefined);
});

test("online activities against the country and low- and middle-income economies", () => {
    const on = run({...FULL, internet: "yes", online: "social_media,job"}).living.online;
    assert.deepEqual(on.done, ["social_media", "job"]);
    assert.equal(on.items.length, 6);
    const social = on.items.find(i => i.key === "social_media");
    assert.ok(social.you && social.lmy > 30 && social.lmy < 60 && social.country > 50);
    assert.equal(on.items.find(i => i.key === "news").you, false);
    // Only for internet users; high-income economies have no country column.
    assert.equal(run({...FULL, internet: "no", online: "news"}).living.online, undefined);
    const us = run({...FULL, country: "USA", income_mode: "band", income_band: "b7", internet: "yes", online: "none"}).living.online;
    assert.ok(us && us.year === null && us.done.length === 0);
});

test("country glance shows the value about ten years earlier", () => {
    const glance = run(FULL).location.glance;
    const le = glance.find(g => g.code === "SP.DYN.LE00.IN");
    assert.ok(le.earlier && le.year - le.earlier.year >= 5 && le.earlier.value > 60);
    const net = glance.find(g => g.code === "IT.NET.USER.ZS");
    if (net) assert.ok(net.earlier.value < net.value);
});

// Prints JS distribution values as JSON so the Python tests can compare them.
const {load} = require("./load");
const SES = load();
const xs = Array.from({length: 60}, (_, i) => 0.05 * Math.pow(1.2, i));
const ps = [0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99];
const out = {global_cdf: xs.map(SES.globalCdf), global_quantile: ps.map(SES.globalQuantile), national: {}};
for (const c of SES.data.countries) {
    if (!c.income) continue;
    out.national[c.iso3] = {cdf: xs.map(x => SES.nationalCdf(c.income, x)), quantile: ps.map(p => SES.nationalQuantile(c.income, p))};
}
process.stdout.write(JSON.stringify({xs, ps, ...out}));

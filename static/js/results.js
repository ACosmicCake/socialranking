// Renders the results page from the answers in the URL fragment (#country=...&...).
(function () {
    const root = document.getElementById("results");
    if (!root) return;
    const base = window.SES_BASE || "";
    const D = SES.data;
    const citations = D.facts.citations;

    // ---------------------------------------------------------------- formatting
    const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"})[c]);
    const fixed = (v, d) => Number(v).toLocaleString("en-US", {minimumFractionDigits: d, maximumFractionDigits: d});
    const pct = (v, d = 1) => v === null || v === undefined ? "-" : `${Number(v).toFixed(d)}%`;
    const money = (v, d = 2) => `$${fixed(v, d)}`;
    const people = v => v >= 1e9 ? `${(v / 1e9).toFixed(1)} billion` : v >= 1e6 ? `${fixed(v / 1e6, 0)} million` : fixed(v, 0);
    const cite = key => {
        const c = citations[key];
        const short = c.publisher.split(",")[0].split(" (")[0];
        return `<a class="cite" href="${esc(c.url)}" target="_blank" rel="noopener" title="${esc(c.title)}, ${esc(c.publisher)}">[${esc(short)} ${c.year}]</a>`;
    };
    const meter = (v, label) => `<div class="meter" role="img" aria-label="${esc(label)} ${pct(v)}"><div class="meter-fill" style="width: ${Math.min(v, 100)}%"></div></div>`;
    const lower = s => s.charAt(0).toLowerCase() + s.slice(1);

    // ---------------------------------------------------------------- answers
    const form = Object.fromEntries(new URLSearchParams(window.location.hash.slice(1)));
    let r;
    try {
        r = SES.score(SES.parseAnswers(form));
    } catch (e) {
        if (!(e instanceof SES.ValidationError)) throw e;
        root.innerHTML = `<section class="container page-section text-center">
            <h1 class="h3">No results to show yet</h1>
            <p class="text-secondary">This page shows results after you finish the quiz${Object.keys(form).length ? ", and the answers in this link are incomplete" : ""}.</p>
            <a class="btn btn-light" href="${base}quiz.html">Take the quiz</a></section>`;
        return;
    }

    const inc = r.income, edu = r.education, liv = r.living, sec = r.security, p = r.perception;
    const cname = esc(r.country.name);
    const html = [];

    // ---------------------------------------------------------------- hero
    html.push(`<div class="hero hero-results d-flex flex-column justify-content-center align-items-center text-center px-3">
        <p class="text-uppercase small text-white-50 mb-1">Income, compared with everyone on Earth</p>
        <h1 class="display-5 fw-bold">Your household income per person is higher than
            <span class="highlight">${pct(inc.global_pct)}</span> of the world's population</h1>
        <p class="lead mb-1">That's about <strong>${people(inc.people_below)}</strong> people. You're in the
            <strong>top ${pct(inc.top_pct)}</strong>.</p>
        <p class="text-white-50">If the world were 100 people lined up from poorest to richest, you'd be person
            <strong class="text-white">#${inc.person_of_100}</strong>.</p>
        ${inc.mode === "band" ? `<p class="small text-white-50">You picked a range (${esc(inc.band_label)}), which puts you somewhere between
            ${pct(inc.global_range[0])} and ${pct(inc.global_range[1])}. We show the midpoint.</p>` : ""}
        <button class="btn btn-outline-light btn-sm mt-2" id="copy-link" type="button">Copy a link to these results</button>
        <span class="small text-white-50 mt-1" id="copy-status" aria-live="polite"></span>
    </div>
    <section class="container page-section">`);

    // ---------------------------------------------------------------- profile + ladder
    const badges = rung => [
        p.ladder_world === rung ? `<span class="badge text-bg-info">You placed yourself (world)</span>` : "",
        p.ladder_country === rung ? `<span class="badge text-bg-secondary">You placed yourself (${cname})</span>` : "",
        p.measured_rung === rung ? `<span class="badge text-bg-light">Measured (world)</span>` : "",
        p.national_income_rung === rung ? `<span class="badge text-bg-warning">Income rank in ${cname}</span>` : "",
    ].join(" ");
    let gapText;
    if (p.gap === undefined) gapText = "You skipped the ladder questions, so only the measured rung is shown.";
    else if (p.gap < -1) gapText = `You placed yourself <strong>${-p.gap} rungs lower</strong> than the data suggests. That's common: people judge their standing against those around them, not against the whole world.`;
    else if (p.gap > 1) gapText = `You placed yourself <strong>${p.gap} rungs higher</strong> than the data suggests.`;
    else gapText = "Your self-placement is close to what the data suggests.";

    html.push(`<div class="row g-4">
        <div class="col-lg-7">
            <h2 class="h3">Your profile</h2>
            <p class="text-secondary">For each dimension, the share of people in the world who are worse off than you
                (people in your own category count as half). Each one is compared with its own data source.</p>
            ${r.dimensions.map(d => `<div class="mb-3">
                <div class="d-flex justify-content-between"><a href="#${d.key}" class="link-light">${d.label}</a><span>${pct(d.pct)}</span></div>
                ${meter(d.pct, d.label)}</div>`).join("")}
            <div class="card bg-transparent border-light mt-4"><div class="card-body">
                <h3 class="h5">SES index: ${r.ses_index} / 100</h3>
                <p class="mb-0 small text-secondary">The average of the ${r.dimensions.length} dimension scores above, weighted equally.
                    It summarises your position but isn't itself a percentile: no dataset records all of these dimensions for the
                    same people. See the <a href="${base}methodology.html#index">methodology</a>.</p>
            </div></div>
        </div>
        <div class="col-lg-5">
            <h2 class="h3">How you see yourself</h2>
            <div class="ladder-compare">
                ${[10, 9, 8, 7, 6, 5, 4, 3, 2, 1].map(rung => `<div class="rung-row"><span class="rung-num">${rung}</span><span class="rung-bar">${badges(rung)}</span></div>`).join("")}
            </div>
            <p class="small text-secondary mt-2">${gapText} Ladder questions: ${cite("macarthur")}.</p>
        </div>
    </div>`);

    // ---------------------------------------------------------------- income
    const survey = r.country.survey;
    const dl = (k, v, bold) => `<dt class="col-7">${k}</dt><dd class="col-5 text-end${bold ? " fw-bold" : ""}">${v}</dd>`;
    html.push(`<hr class="my-5"><h2 id="income" class="h3">Income</h2>
    <div class="row g-4">
        <div class="col-lg-7">
            <div class="chart-box"><canvas id="incomeChart" aria-label="Cumulative income distribution of the world${inc.chart.country ? ` and ${cname}` : ""}, with your position marked"></canvas></div>
            <p class="small text-secondary mt-2">Share of people living on less than each amount per person per day
                (2017 international dollars, log scale). World: ${cite("pip")}, lined up to 2019.
                ${survey ? `${cname}: national ${esc(survey.welfare_type)} survey, ${survey.survey_year}${survey.coverage !== "national" ? ` (${esc(survey.coverage)} only)` : ""}.` : ""}</p>
        </div>
        <div class="col-lg-5">
            <dl class="row small">
                ${inc.mode === "exact" ? dl("Household income per person per day", `${fixed(inc.local_per_day, 2)} ${esc(r.country.currency || "")}`)
                    + dl(`Prices today vs 2017 (${cname})`, `&times;${fixed(inc.price_level_vs_2017, 3)}`)
                    + dl(`PPP factor, 2017 (${esc(r.country.currency)} per int. $)`, fixed(inc.ppp_2017, 3)) : ""}
                ${dl("Your income, 2017 int. $ per day", money(inc.ppp_per_day), true)}
                ${dl("World median (2019)", money(inc.world_median))}
                ${dl("You vs the world median", `${fixed(inc.multiple_of_world_median, 1)}&times;`)}
                ${r.country.median_ppp ? dl(`${cname} median (${survey.survey_year})`, money(r.country.median_ppp)) : ""}
                ${dl(`Richer than, in ${cname}`, inc.national_pct !== undefined ? pct(inc.national_pct) : "no survey data", true)}
            </dl>
            <ul class="list-unstyled small">
                ${inc.lines.map(l => `<li>${l.above ? "&#10003; Above" : "&#10007; Below"} the ${esc(l.label)}, ${esc(l.meaning)}.
                    ${pct(l.share_below)} of the world live below it.</li>`).join("")}
            </ul>
            ${inc.mode === "exact" && inc.extrapolated_years ? `<p class="small text-secondary">Inflation data for ${cname} run to
                ${inc.prices_through}; we carried prices forward ${inc.extrapolated_years} year(s) at the recent average of
                ${pct(inc.recent_inflation * 100)} a year. ${cite("wdi")}</p>` : ""}
        </div>
    </div>`);

    // ---------------------------------------------------------------- education
    html.push(`<hr class="my-5"><h2 id="education" class="h3">Education</h2>
    <p>You have <strong>${esc(lower(edu.label))}</strong>. That's more education than about
        <strong>${pct(edu.global_pct)}</strong> of the world's adults aged 25-64.
        ${edu.national_pct !== undefined ? `In ${cname} the figure is ${pct(edu.national_pct)}.` : ""}
        ${pct(edu.same_level_pct)} of adults worldwide share your level and ${pct(edu.higher_pct)} have gone further.</p>
    <div class="table-responsive"><table class="table table-sm table-dark align-middle edu-table">
        <thead><tr><th>Level</th><th class="w-50">World (${edu.year})</th>${edu.country_shares ? `<th class="w-25">${cname}</th>` : ""}</tr></thead>
        <tbody>${edu.levels.map((label, i) => `<tr class="${i === edu.level ? "you" : ""}">
            <td>${esc(label)}${i === edu.level ? ` <span class="badge text-bg-light">you</span>` : ""}</td>
            <td><div class="bar" style="width: ${edu.world_shares[i] * 2}%"></div> ${pct(edu.world_shares[i])}</td>
            ${edu.country_shares ? `<td>${pct(edu.country_shares[i])}</td>` : ""}</tr>`).join("")}</tbody>
    </table></div>
    <p class="small text-secondary">Source: ${cite("barro_lee")}. The latest estimates are for 2015; average schooling has risen since.
        ${edu.country_mean_years ? `Average years of schooling in ${cname}: ${edu.country_mean_years}.` : ""}</p>`);

    // ---------------------------------------------------------------- living standards
    const mark = has => has === null || has === undefined ? `<span class="text-secondary" title="Not answered">&ndash;</span>`
        : has ? `<span class="text-success" title="You have this">&#10003;</span>` : `<span class="text-danger" title="You lack this">&#10007;</span>`;
    html.push(`<hr class="my-5"><h2 id="living" class="h3">Living standards at home</h2>
    ${liv.answered ? `<p>Averaged over the ${liv.answered} services you answered about, you're better off than about
        <strong>${pct(liv.global_pct)}</strong> of people.
        ${liv.lower_bound_pct ? `At the very least, <strong>${pct(liv.lower_bound_pct)}</strong> of the world lacks something you have.` : ""}</p>`
        : `<p class="text-secondary">You skipped this section.</p>`}
    <div class="table-responsive"><table class="table table-dark table-sm align-middle">
        <thead><tr><th></th><th>Service</th><th>People in the world without it</th><th>Context</th></tr></thead>
        <tbody>${liv.items.map(i => `<tr><td class="fs-5">${mark(i.has)}</td>
            <td>${esc(i.label)}${i.status ? `<div class="small text-secondary">Your answer: ${esc(i.status)}</div>` : ""}</td>
            <td class="text-nowrap">${pct(i.share_without_pct, 0)} (${people(i.people_without)})</td>
            <td class="small">${esc(i.note)} ${cite(i.cite)}</td></tr>`).join("")}</tbody>
    </table></div>
    <p class="small text-secondary">"Safely managed" water and sanitation also require the water to be free from contamination and
        waste to be safely treated, which you can't check yourself, so we classify your answers approximately.</p>`);

    // ---------------------------------------------------------------- security
    const food = D.facts.food, findex = D.facts.findex;
    const fiesName = {secure: "food security", mild: "mild food insecurity", moderate: "moderate food insecurity", severe: "severe food insecurity"};
    let foodHtml;
    if (sec.fies_raw !== undefined) {
        foodHtml = `<p>You answered yes to <strong>${sec.fies_raw} of 8</strong> questions on the Food Insecurity Experience Scale
            ${cite("fies")}, which roughly corresponds to <strong>${fiesName[sec.fies_level]}</strong> ${cite("fies_raw_score")}.
            ${["moderate", "severe"].includes(sec.fies_level)
                ? `You are among the ${people(food.moderate_or_severe_people)} people (${pct(food.moderate_or_severe_share * 100)}) facing moderate or severe food insecurity in ${food.year}.`
                : `About ${pct(100 - food.moderate_or_severe_share * 100)} of the world is in this position; ${people(food.moderate_or_severe_people)} people faced moderate or severe food insecurity in ${food.year}.`}
            ${cite(food.cite)}</p>`;
    } else if (sec.fies_answered) {
        foodHtml = `<p class="text-secondary">You answered ${sec.fies_answered} of the 8 food questions; all 8 are needed for a score.</p>`;
    } else {
        foodHtml = `<p class="text-secondary">Not answered.</p>`;
    }
    const bank = [];
    if (sec.account !== undefined) bank.push(sec.account
        ? `You have an account, as do ${pct(findex.account_share * 100, 0)} of adults worldwide; ${people(findex.unbanked_adults)} adults have none.`
        : `You don't have an account. Neither do ${people(findex.unbanked_adults)} adults (${pct(100 - findex.account_share * 100, 0)}).`);
    if (sec.saved !== undefined) bank.push(sec.saved
        ? `You saved money in the past year, as did ${pct(findex.saved_share * 100, 0)} of adults.`
        : `You didn't save money in the past year; ${pct(100 - findex.saved_share * 100, 0)} of adults also didn't.`);
    html.push(`<hr class="my-5"><h2 id="security" class="h3">Financial security</h2>
    <div class="row g-4">
        <div class="col-md-6"><h3 class="h5">Basic needs</h3>
            ${sec.gallup_group ? `<p>You're in Gallup's <strong>${esc(lower(sec.gallup_label))}</strong> group: ${esc(lower(sec.gallup_definition))}
                ${pct(sec.gallup_share_pct, 0)} of the world's adults are in this group. You're more secure than about
                <strong>${pct(sec.global_pct)}</strong> of adults.
                ${sec.gallup_group === "high" ? `You're one of the roughly ${people(D.facts.gallup_people_high)} people Gallup found struggling with no safety net.` : ""}
                ${cite("gallup_2020")}</p>` : `<p class="text-secondary">Not answered.</p>`}
        </div>
        <div class="col-md-6"><h3 class="h5">Food security</h3>${foodHtml}</div>
        <div class="col-md-6"><h3 class="h5">Banking and saving</h3>
            ${bank.length ? `<ul class="small">${bank.map(b => `<li>${b}</li>`).join("")}</ul>` : `<p class="text-secondary">Not answered.</p>`}
            <p class="small">${cite(findex.cite)}</p>
        </div>
    </div>`);

    // ---------------------------------------------------------------- wealth
    if (r.wealth.band) {
        const w = r.wealth;
        html.push(`<hr class="my-5"><h2 id="wealth" class="h3">Wealth</h2>
        <p>A net worth of ${esc(lower(w.band))} puts you between the ${pct(w.range[0])} and ${pct(w.range[1])} marks of the world's
            adults (midpoint ${pct(w.global_pct)}). ${cite("ubs_2026")}</p>
        <div class="pyramid">${w.pyramid.slice().reverse().map(b => `<div class="pyramid-row ${b.you ? "you" : ""}">
            <div class="pyramid-bar" style="width: ${Math.max(b.pct * 1.6, 4)}%">${pct(b.pct)}</div>
            <span>${esc(b.label)}${b.you ? " &larr; you" : ""}</span></div>`).join("")}</div>`);
    }

    // ---------------------------------------------------------------- location
    if (r.location.gdp_per_capita_usd !== undefined) {
        html.push(`<hr class="my-5"><h2 id="location" class="h3">Where you live</h2>
        <p>${cname}'s GDP per person was ${money(r.location.gdp_per_capita_usd, 0)} in ${r.location.gdp_year}.
            ${pct(r.location.share_in_poorer_countries_pct)} of the world lives in countries with a lower GDP per person. ${cite("wdi")}</p>
        <p class="small text-secondary">This is context, not part of your SES index: your income has already been adjusted for prices
            in ${cname} and compared globally, so counting your country again would double-count it.</p>`);
    }

    html.push(`<hr class="my-5"><div class="text-center">
        <a class="btn btn-light" href="${base}quiz.html">Take it again</a>
        <a class="btn btn-outline-light" href="${base}methodology.html">How this was calculated</a>
    </div></section>`);
    root.innerHTML = html.join("\n");

    // ---------------------------------------------------------------- copy link
    document.getElementById("copy-link").addEventListener("click", () => {
        const status = document.getElementById("copy-status");
        navigator.clipboard.writeText(window.location.href)
            .then(() => { status.textContent = "Link copied. It contains your answers."; })
            .catch(() => { status.textContent = "Copy the address from your browser's address bar."; });
    });

    // ---------------------------------------------------------------- chart
    const canvas = document.getElementById("incomeChart");
    if (typeof Chart === "undefined") return;
    const d = inc.chart;
    const toPoints = ys => d.x.map((x, i) => ({x, y: ys[i]}));
    const datasets = [{
        label: "World", data: toPoints(d.world), borderColor: "#7dd3fc",
        backgroundColor: "rgba(125, 211, 252, 0.15)", fill: true, pointRadius: 0, tension: 0.2,
    }];
    if (d.country) {
        datasets.push({label: r.country.name, data: toPoints(d.country), borderColor: "#fbbf24", pointRadius: 0, borderDash: [6, 4], tension: 0.2});
    }
    datasets.push({
        label: "You", type: "scatter", pointRadius: 7, pointBackgroundColor: "#ffffff", pointBorderColor: "#000000",
        data: [{x: d.you, y: d.you_world}].concat(d.you_country !== null ? [{x: d.you, y: d.you_country}] : []),
    });
    const axis = text => ({display: true, text, color: "#ccc"});
    const grid = {color: "rgba(255,255,255,0.08)"};
    new Chart(canvas, {
        type: "line",
        data: {datasets},
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {type: "logarithmic", min: 0.5, max: 1000, title: axis("Income per person per day (2017 int. $)"), grid,
                    ticks: {color: "#ccc", callback: v => [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000].includes(v) ? `$${v}` : ""}},
                y: {min: 0, max: 100, title: axis("% of people living on less"), grid, ticks: {color: "#ccc", callback: v => `${v}%`}},
            },
            plugins: {
                legend: {labels: {color: "#eee"}},
                tooltip: {callbacks: {label: c => `${c.dataset.label}: ${c.parsed.y.toFixed(1)}% live on less than $${c.parsed.x.toFixed(2)}/day`}},
            },
        },
    });
})();

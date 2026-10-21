// Renders the results page from the answers in the URL fragment (#country=...&...).
(function () {
    const root = document.getElementById("results");
    if (!root) return;
    const base = window.SES_BASE || "";
    const assetBase = window.SES_ASSET_BASE || base;
    const VI = window.SES_LANG === "vi";
    const tr = (en, vi) => (VI ? vi : en);
    const D = SES.data;
    const citations = D.facts.citations;

    // ---------------------------------------------------------------- formatting
    const locale = VI ? "vi-VN" : "en-US";
    const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"})[c]);
    const fixed = (v, d) => Number(v).toLocaleString(locale, {minimumFractionDigits: d, maximumFractionDigits: d});
    const pct = (v, d = 1) => v === null || v === undefined ? "-" : `${fixed(v, d)}%`;
    const money = (v, d = 2) => `$${fixed(v, d)}`;
    const people = v => v >= 1e9 ? `${fixed(v / 1e9, 1)} ${tr("billion", "tỷ")}`
        : v >= 1e6 ? `${fixed(v / 1e6, 0)} ${tr("million", "triệu")}` : fixed(v, 0);
    const cite = key => {
        const c = citations[key];
        const short = c.publisher.split(",")[0].split(" (")[0];
        return `<a class="cite" href="${esc(c.url)}" target="_blank" rel="noopener" title="${esc(c.title)}, ${esc(c.publisher)}">[${esc(short)} ${c.year}]</a>`;
    };
    const meter = (v, label, cls = "") => `<div class="meter ${cls}" role="img" aria-label="${esc(label)} ${pct(v)}"><div class="meter-fill" style="width: ${Math.min(Math.max(v, 0), 100)}%"></div></div>`;
    const lower = s => (VI ? s : s.charAt(0).toLowerCase() + s.slice(1));
    const section = (id, title, body) => `<hr class="my-5"><section id="${id}" class="result-section"><h2 class="h3">${title}</h2>${body}</section>`;
    const table = (head, rows, cls = "") => `<div class="table-responsive"><table class="table table-dark table-sm align-middle ${cls}">
        <thead><tr>${head.map(h => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`;
    const fmtGlance = (v, f) => v === null || v === undefined ? "-" : f === "money" ? money(v, 0) : f === "pct" ? pct(v) : f === "index" ? fixed(v, 2) : fixed(v, 1);

    // ---------------------------------------------------------------- answers
    // The fragment holds the answers, so in-page links scroll instead of changing it.
    const shareUrl = window.location.href;
    const params = new URLSearchParams(window.location.hash.slice(1));
    const form = Object.fromEntries(params);
    let answers, r;
    try {
        answers = SES.parseAnswers(form);
        r = SES.score(answers);
    } catch (e) {
        if (!(e instanceof SES.ValidationError)) throw e;
        const partial = Object.keys(form).length;
        root.innerHTML = `<section class="container page-section text-center">
            <h1 class="h3">${tr("No results to show yet", "Chưa có kết quả")}</h1>
            <p class="text-secondary">${tr(`This page shows results after you finish the quiz${partial ? ", and the answers in this link are incomplete" : ""}.`,
                `Trang này hiện kết quả sau khi bạn làm xong bài${partial ? ", và câu trả lời trong đường dẫn này chưa đầy đủ" : ""}.`)}</p>
            <a class="btn btn-light" href="${base}quiz.html">${tr("Take the quiz", "Làm bài")}</a></section>`;
        return;
    }
    const country = SES.country(r.country.iso3);
    const inc = r.income, edu = r.education, work = r.work, liv = r.living, sec = r.security, p = r.perception;
    const cname = esc(r.country.name);
    const refYear = D.global.income.reference_year;
    const html = [];

    // ---------------------------------------------------------------- hero
    const nowcast = inc.history.find(h => h.estimate_type === "nowcast");
    html.push(`<div class="hero hero-results d-flex flex-column justify-content-center align-items-center text-center px-3">
        <p class="text-uppercase small text-white-50 mb-1">${tr("Income, compared with everyone on Earth", "Thu nhập, so với mọi người trên Trái Đất")}</p>
        <h1 class="display-5 fw-bold">${tr(
            `Your household income per person is higher than <span class="highlight">${pct(inc.global_pct)}</span> of the world's population`,
            `Thu nhập bình quân đầu người của hộ bạn cao hơn <span class="highlight">${pct(inc.global_pct)}</span> dân số thế giới`)}</h1>
        <p class="lead mb-1">${tr(
            `That's about <strong>${people(inc.people_below)}</strong> people. You're in the <strong>top ${pct(inc.top_pct)}</strong>${inc.national_pct !== undefined ? `, and richer than <strong>${pct(inc.national_pct)}</strong> of people in ${cname}` : ""}.`,
            `Tức là khoảng <strong>${people(inc.people_below)}</strong> người. Bạn thuộc nhóm <strong>${pct(inc.top_pct)} cao nhất</strong>${inc.national_pct !== undefined ? `, và khá giả hơn <strong>${pct(inc.national_pct)}</strong> dân số ${cname}` : ""}.`)}</p>
        <p class="text-white-50">${tr(
            `If the world were 100 people lined up from poorest to richest, you'd be person <strong class="text-white">#${inc.person_of_100}</strong>.`,
            `Nếu thế giới là 100 người xếp hàng từ nghèo nhất đến giàu nhất, bạn là người thứ <strong class="text-white">${inc.person_of_100}</strong>.`)}</p>
        ${inc.mode === "band" ? `<p class="small text-white-50">${tr(
            `You picked a range (${esc(inc.band_label)}), which puts you somewhere between ${pct(inc.global_range[0])} and ${pct(inc.global_range[1])}. We show the midpoint.`,
            `Bạn đã chọn một khoảng (${esc(inc.band_label)}), tức là ở đâu đó giữa ${pct(inc.global_range[0])} và ${pct(inc.global_range[1])}. Chúng tôi hiển thị điểm giữa.`)}</p>` : ""}
        <div class="d-flex flex-wrap gap-2 justify-content-center mt-2">
            <button class="btn btn-outline-light btn-sm" id="copy-link" type="button">${tr("Copy a link to these results", "Sao chép đường dẫn kết quả")}</button>
            <button class="btn btn-outline-light btn-sm" id="save-image" type="button">${tr("Save a summary image", "Lưu ảnh tóm tắt")}</button>
            <button class="btn btn-outline-light btn-sm" id="save-csv" type="button">${tr("Download the numbers (CSV)", "Tải số liệu (CSV)")}</button>
            <button class="btn btn-outline-light btn-sm" id="save-json" type="button">${tr("Download everything (JSON)", "Tải toàn bộ (JSON)")}</button>
            <button class="btn btn-outline-light btn-sm" id="print-page" type="button">${tr("Print or save as PDF", "In hoặc lưu PDF")}</button>
        </div>
        <span class="small text-white-50 mt-1" id="copy-status" aria-live="polite"></span>
    </div>`);

    // ---------------------------------------------------------------- section nav
    const navItems = [["profile", tr("Profile", "Tổng quan")], ["income", tr("Income", "Thu nhập")],
        ["world", tr("Around the world", "Khắp thế giới")], ["history", tr("Over time", "Theo thời gian")],
        ["education", tr("Education", "Học vấn")], ["work", tr("Work", "Công việc")], ["living", tr("Home", "Nhà ở")],
        ["mpi", tr("Poverty index", "Nghèo đa chiều")], ["security", tr("Security", "An ninh tài chính")],
        ["protection", tr("Social protection", "An sinh xã hội")], ["wealth", tr("Wealth", "Tài sản")],
        ["country", tr("Your country", "Nước bạn")]]
        .filter(([id]) => !(id === "work" && !work.status) && !(id === "wealth" && !r.wealth.band) && !(id === "mpi" && !r.mpi.available)
            && !(id === "protection" && !r.social_protection.received && !r.social_protection.country));
    html.push(`<nav class="result-nav sticky-top" aria-label="${tr("Result sections", "Các phần kết quả")}"><div class="container d-flex gap-1 py-2">
        ${navItems.map(([id, label]) => `<a class="btn btn-sm btn-outline-secondary" href="#${id}">${label}</a>`).join("")}</div></nav>
        <div class="container pb-5">`);

    // ---------------------------------------------------------------- profile + ladder
    const badges = rung => [
        p.ladder_world === rung ? `<span class="badge text-bg-info">${tr("You placed yourself (world)", "Bạn tự đặt (thế giới)")}</span>` : "",
        p.ladder_country === rung ? `<span class="badge text-bg-secondary">${tr(`You placed yourself (${cname})`, `Bạn tự đặt (${cname})`)}</span>` : "",
        p.measured_rung === rung ? `<span class="badge text-bg-light">${tr("Measured (world)", "Đo được (thế giới)")}</span>` : "",
        p.national_income_rung === rung ? `<span class="badge text-bg-warning">${tr(`Income rank in ${cname}`, `Thứ hạng thu nhập ở ${cname}`)}</span>` : "",
    ].join(" ");
    let gapText;
    if (p.gap === undefined) gapText = tr("You skipped the ladder questions, so only the measured rung is shown.",
        "Bạn đã bỏ qua câu hỏi chiếc thang, nên chỉ hiện bậc đo được.");
    else if (p.gap < -1) gapText = tr(
        `You placed yourself <strong>${-p.gap} rungs lower</strong> than the data suggests. That's common: people judge their standing against those around them, not against the whole world.`,
        `Bạn tự đặt mình <strong>thấp hơn ${-p.gap} bậc</strong> so với số liệu. Điều này rất phổ biến: mọi người thường so mình với những người xung quanh, không phải với cả thế giới.`);
    else if (p.gap > 1) gapText = tr(`You placed yourself <strong>${p.gap} rungs higher</strong> than the data suggests.`,
        `Bạn tự đặt mình <strong>cao hơn ${p.gap} bậc</strong> so với số liệu.`);
    else gapText = tr("Your self-placement is close to what the data suggests.", "Cách bạn tự đánh giá khá sát với số liệu.");

    // Highlights: the most telling numbers from each section, linking to the details.
    const highlights = [];
    const hl = (id, value, text) => highlights.push(`<a class="stat-card" href="#${id}"><span class="stat-value">${value}</span><span class="stat-text">${text}</span></a>`);
    hl("income", tr(`Top ${pct(inc.top_pct)}`, `${pct(inc.top_pct)} cao nhất`), tr("of the world by income per person", "thế giới theo thu nhập bình quân đầu người"));
    if (inc.national_pct !== undefined) hl("income", pct(inc.national_pct), tr(`of people in ${cname} have less income`, `dân số ${cname} có thu nhập thấp hơn`));
    hl("education", pct(edu.global_pct), tr("of adults worldwide have less education", "người trưởng thành trên thế giới học vấn thấp hơn"));
    if (inc.healthy_diet.share_of_income !== undefined) hl("income", pct(inc.healthy_diet.share_of_income * 100, 0),
        tr(`of your income: what a healthy diet costs in ${cname}`, `thu nhập của bạn: chi phí một chế độ ăn lành mạnh ở ${cname}`));
    if (sec.emergency) hl("security", pct(sec.emergency.world_pct), tr("of adults are less able to raise emergency money", "người trưởng thành khó xoay tiền khẩn cấp hơn bạn"));
    if (r.mobility.rank_change !== undefined) hl("education", `${r.mobility.rank_change > 0 ? "+" : ""}${fixed(r.mobility.rank_change, 1)}`,
        tr("rank points in education compared with your parents", "điểm thứ hạng học vấn so với bố mẹ"));
    if (r.mpi.available) hl("mpi", `${fixed(r.mpi.score, 0)}%`, tr("multidimensional poverty score (33% or more counts as poor)", "điểm nghèo đa chiều (từ 33% là nghèo)"));
    if (work.occupation && work.occupation.world_pct !== undefined) hl("work", pct(work.occupation.world_pct), tr("of workers are in less-skilled occupations", "lao động làm nghề có trình độ kỹ năng thấp hơn"));
    html.push(`<section class="result-section pt-4" aria-label="${tr("Highlights", "Điểm nổi bật")}">
        <div class="stat-grid">${highlights.slice(0, 8).join("")}</div></section>`);

    html.push(`<section id="profile" class="result-section pt-4"><div class="row g-4">
        <div class="col-lg-7">
            <h2 class="h3">${tr("Your profile", "Tổng quan của bạn")}</h2>
            <p class="text-secondary">${tr(
                `For each dimension, the share of people who are worse off than you (people in your own category count as half): <span class="legend-world">in the world</span> and, where we have national data, <span class="legend-country">in ${cname}</span>.`,
                `Với mỗi khía cạnh, tỷ lệ người kém hơn bạn (người cùng nhóm với bạn được tính một nửa): <span class="legend-world">trên thế giới</span> và, khi có số liệu quốc gia, <span class="legend-country">ở ${cname}</span>.`)}</p>
            ${r.dimensions.map(d => `<div class="mb-3">
                <div class="d-flex justify-content-between"><a href="#${d.key}" class="link-light">${d.label}</a>
                    <span>${pct(d.pct)}${d.national_pct !== undefined ? ` <span class="text-warning small">/ ${pct(d.national_pct)}</span>` : ""}</span></div>
                ${meter(d.pct, d.label)}
                ${d.national_pct !== undefined ? meter(d.national_pct, `${d.label} ${r.country.name}`, "meter-country") : ""}</div>`).join("")}
            ${(() => {
                if (r.dimensions.length < 2) return "";
                const sorted = r.dimensions.slice().sort((a, b) => b.pct - a.pct);
                const top = sorted[0], low = sorted[sorted.length - 1];
                if (top.pct - low.pct < 5) return `<p class="small text-secondary">${tr("Your dimensions are close to one another: no single one stands out.", "Các khía cạnh của bạn khá sát nhau: không có khía cạnh nào nổi bật.")}</p>`;
                const link = d => `<a href="#${d.key}" class="link-light">${esc(VI ? d.label.toLowerCase() : lower(d.label))}</a>`;
                return `<p class="small">${tr(`Your strongest dimension is ${link(top)} (${pct(top.pct)}); the one holding your index down most is ${link(low)} (${pct(low.pct)}).`,
                    `Khía cạnh mạnh nhất của bạn là ${link(top)} (${pct(top.pct)}); khía cạnh kéo chỉ số của bạn xuống nhiều nhất là ${link(low)} (${pct(low.pct)}).`)}</p>`;
            })()}
            <div class="card bg-transparent border-light mt-4"><div class="card-body">
                <h3 class="h5">${tr("SES index", "Chỉ số SES")}: ${fixed(r.ses_index, 1)} / 100</h3>
                <p class="mb-0 small text-secondary">${tr(
                    `The average of the ${r.dimensions.length} world scores above, weighted equally. It summarises your position but isn't itself a percentile: no dataset records all of these dimensions for the same people. See the <a href="${assetBase}methodology.html#index">methodology</a>.`,
                    `Trung bình của ${r.dimensions.length} điểm thế giới ở trên, trọng số bằng nhau. Nó tóm tắt vị trí của bạn nhưng bản thân không phải là một bách phân vị: không có bộ dữ liệu nào ghi nhận tất cả các khía cạnh này cho cùng một người. Xem <a href="${base}methodology.html#index">phương pháp</a>.`)}</p>
                ${(() => {
                    const names = {income: tr("income", "thu nhập"), education: tr("education", "học vấn"), work: tr("work", "công việc"),
                                   living: tr("living standards", "mức sống"), security: tr("financial security", "an ninh tài chính"),
                                   wealth: tr("wealth", "tài sản")};
                    const have = new Set(r.dimensions.map(d => d.key));
                    const missing = Object.keys(names).filter(k => !have.has(k) && !(k === "work" && work.status && !work.employed));
                    if (!missing.length) return "";
                    return `<p class="small mt-2 mb-0">${tr(`Not included yet: ${missing.map(k => names[k]).join(", ")}.`,
                        `Chưa tính: ${missing.map(k => names[k]).join(", ")}.`)}
                        <a href="${base}quiz.html" class="prefill-quiz">${tr("Add answers", "Thêm câu trả lời")}</a></p>`;
                })()}
            </div></div>
        </div>
        <div class="col-lg-5">
            <h2 class="h3">${tr("How you see yourself", "Bạn tự đánh giá thế nào")}</h2>
            <div class="ladder-compare">
                ${[10, 9, 8, 7, 6, 5, 4, 3, 2, 1].map(rung => `<div class="rung-row"><span class="rung-num">${rung}</span><span class="rung-bar">${badges(rung)}</span></div>`).join("")}
            </div>
            <p class="small text-secondary mt-2">${gapText} ${tr("Ladder questions", "Câu hỏi chiếc thang")}: ${cite("macarthur")}.</p>
        </div>
    </div></section>`);

    // ---------------------------------------------------------------- compare with someone else
    html.push(`<div class="card bg-transparent border-secondary mt-4" id="compare"><div class="card-body">
        <h3 class="h5">${tr("Compare with someone else", "So sánh với người khác")}</h3>
        <p class="small text-secondary">${tr("Paste another results link, a friend's or your own from another time, to see both profiles side by side. Nothing is sent anywhere: both are calculated in your browser.",
                                             "Dán một đường dẫn kết quả khác, của bạn bè hoặc của chính bạn vào lúc khác, để xem hai hồ sơ cạnh nhau. Không có gì được gửi đi: cả hai đều được tính trong trình duyệt của bạn.")}</p>
        <div class="input-group">
            <input type="url" class="form-control" id="compare-url" placeholder="https://…/results.html#country=…" aria-label="${tr("Results link to compare", "Đường dẫn kết quả để so sánh")}">
            <button class="btn btn-outline-light" type="button" id="compare-go">${tr("Compare", "So sánh")}</button>
        </div>
        <div id="compare-out" class="mt-3" aria-live="polite"></div>
    </div></div>`);

    // ---------------------------------------------------------------- income
    const survey = r.country.survey;
    let surveyText = "";
    if (survey) {
        const coverage = survey.coverage !== "national" ? tr(` (${esc(survey.coverage)} areas only)`, " (chỉ khu vực thành thị)") : "";
        surveyText = survey.estimation_type === "CMD estimation" || !survey.survey_year
            ? tr(`${cname}: World Bank model estimate for ${survey.reference_year}${coverage}; there's no recent household survey.`,
                 `${cname}: ước tính mô hình của Ngân hàng Thế giới cho năm ${survey.reference_year}${coverage}; không có khảo sát hộ gia đình gần đây.`)
            : tr(`${cname}: World Bank estimate for ${survey.reference_year}, based on its ${survey.survey_year} national ${esc(survey.welfare_type)} survey${coverage}.`,
                 `${cname}: ước tính của Ngân hàng Thế giới cho năm ${survey.reference_year}, dựa trên khảo sát ${survey.welfare_type === "income" ? "thu nhập" : "chi tiêu"} quốc gia năm ${survey.survey_year}${coverage}.`);
    }
    const dl = (k, v, bold) => `<dt class="col-7">${k}</dt><dd class="col-5 text-end${bold ? " fw-bold" : ""}">${v}</dd>`;
    const areaName = inc.area === "urban" ? tr("urban", "thành thị") : tr("rural", "nông thôn");
    html.push(section("income", tr("Income", "Thu nhập"), `
    <div class="row g-4">
        <div class="col-lg-7">
            <div class="chart-box"><canvas id="incomeChart" aria-label="${tr("Cumulative income distribution, with your position marked", "Phân phối thu nhập tích lũy, có đánh dấu vị trí của bạn")}"></canvas></div>
            <p class="small text-secondary mt-2">${tr(
                "Share of people living on less than each amount per person per day (2021 international dollars, log scale). World:",
                "Tỷ lệ người sống bằng ít hơn mỗi mức tiền mỗi người mỗi ngày (đô la quốc tế 2021, thang logarit). Thế giới:")} ${cite("pip")}, ${refYear}. ${surveyText}</p>
        </div>
        <div class="col-lg-5">
            <dl class="row small">
                ${inc.mode === "exact" ? dl(tr("Household income per person per day", "Thu nhập hộ mỗi người mỗi ngày"), `${fixed(inc.local_per_day, 2)} ${esc(r.country.currency || "")}`)
                    + dl(tr(`Prices in ${inc.price_year} vs 2021 (${cname})`, `Giá năm ${inc.price_year} so với 2021 (${cname})`), `&times;${fixed(inc.price_level_vs_2021, 3)}`)
                    + dl(tr(`PPP factor, 2021 (${esc(r.country.currency || "local currency")} per int. $)`, `Hệ số PPP 2021 (${esc(r.country.currency || "nội tệ")} mỗi đô la quốc tế)`), fixed(inc.ppp_2021, 3))
                    + (country.exchange_rate ? dl(tr(`At market exchange rates (${country.exchange_rate.year}), per person per day`, `Theo tỷ giá thị trường (${country.exchange_rate.year}), mỗi người mỗi ngày`),
                        `US$${fixed(inc.local_per_day / country.exchange_rate.lcu_per_usd, 2)}`) : "") : ""}
                ${dl(tr("Your income, 2021 int. $ per day", "Thu nhập của bạn, đô la quốc tế 2021 mỗi ngày"), money(inc.ppp_per_day), true)}
                ${dl(tr("&nbsp;&nbsp;per month", "&nbsp;&nbsp;mỗi tháng"), money(inc.ppp_per_day * 365 / 12, 0))}
                ${dl(tr(`World median (${refYear})`, `Trung vị thế giới (${refYear})`), money(inc.world_median))}
                ${dl(tr("You vs the world median", "Bạn so với trung vị thế giới"), `${fixed(inc.multiple_of_world_median, 1)}&times;`)}
                ${r.country.median_ppp ? dl(tr(`${cname} median (${survey.reference_year})`, `Trung vị ${cname} (${survey.reference_year})`), money(r.country.median_ppp))
                    + dl(tr(`You vs ${cname}'s median`, `Bạn so với trung vị ${cname}`), `${fixed(inc.multiple_of_country_median, 1)}&times;`) : ""}
                ${dl(tr(`Richer than, in ${cname}`, `Khá giả hơn, ở ${cname}`), inc.national_pct !== undefined ? pct(inc.national_pct) : tr("no data", "không có số liệu"), true)}
                ${inc.area_pct !== undefined ? dl(tr(`Richer than, ${areaName} ${cname}`, `Khá giả hơn, ${areaName} ${cname}`), pct(inc.area_pct), true) : ""}
                ${inc.region ? dl(tr(`Richer than, in ${esc(inc.region.name)}`, `Khá giả hơn, ở ${esc(inc.region.name)}`), pct(inc.region.pct)) : ""}
                ${dl(tr("People richer than you", "Số người khá giả hơn bạn"), people(inc.people_above))}
            </dl>
        </div>
    </div>
    ${inc.basis_mismatch ? `<div class="alert alert-secondary small">${inc.basis === "income"
        ? tr(`${cname}'s survey measures <strong>spending</strong>, and you gave <strong>income</strong>. Better-off households spend less than they earn, so your rank in ${cname} is probably somewhat overstated.`,
             `Khảo sát của ${cname} đo <strong>chi tiêu</strong>, còn bạn nhập <strong>thu nhập</strong>. Hộ khá giả thường chi ít hơn thu nhập, nên thứ hạng của bạn ở ${cname} có lẽ hơi cao hơn thực tế.`)
        : tr(`${cname}'s survey measures <strong>income</strong>, and you gave <strong>spending</strong>. Households usually spend less than they earn, so your rank in ${cname} is probably somewhat understated.`,
             `Khảo sát của ${cname} đo <strong>thu nhập</strong>, còn bạn nhập <strong>chi tiêu</strong>. Hộ gia đình thường chi ít hơn thu nhập, nên thứ hạng của bạn ở ${cname} có lẽ hơi thấp hơn thực tế.`)}</div>` : ""}
    ${inc.sensitivity ? `<p class="small text-secondary">${tr(
        `<strong>How precise is this?</strong> People rarely know their household income exactly. If yours were ${fixed(inc.sensitivity.error * 100, 0)}% lower or higher, your world rank would be between ${pct(inc.sensitivity.global[0])} and ${pct(inc.sensitivity.global[1])}${inc.sensitivity.national ? `, and your rank in ${cname} between ${pct(inc.sensitivity.national[0])} and ${pct(inc.sensitivity.national[1])}` : ""}.`,
        `<strong>Kết quả chính xác đến đâu?</strong> Ít ai biết chính xác thu nhập của hộ mình. Nếu thu nhập thấp hơn hoặc cao hơn ${fixed(inc.sensitivity.error * 100, 0)}%, thứ hạng thế giới của bạn sẽ nằm trong khoảng ${pct(inc.sensitivity.global[0])} đến ${pct(inc.sensitivity.global[1])}${inc.sensitivity.national ? `, và thứ hạng ở ${cname} trong khoảng ${pct(inc.sensitivity.national[0])} đến ${pct(inc.sensitivity.national[1])}` : ""}.`)}</p>` : ""}
    ${inc.national_history ? `<h3 class="h5 mt-3">${tr(`${cname} over time`, `${cname} qua các năm`)}</h3>
    <p class="small">${inc.national_history.reached
        ? tr(`Half of ${cname}'s people lived on less than your income until ${inc.national_history.reached}; the median reached ${money(inc.ppp_per_day)} a day that year.`,
             `Một nửa dân số ${cname} sống bằng mức thấp hơn thu nhập của bạn cho đến năm ${inc.national_history.reached}; năm đó trung vị đạt ${money(inc.ppp_per_day)} mỗi ngày.`)
        : tr(`${cname}'s median has never reached your income (${money(inc.ppp_per_day)} a day): it was ${money(inc.national_history.median[inc.national_history.median.length - 1])} in ${inc.national_history.years[inc.national_history.years.length - 1]}.`,
             `Trung vị của ${cname} chưa bao giờ đạt mức thu nhập của bạn (${money(inc.ppp_per_day)} mỗi ngày): năm ${inc.national_history.years[inc.national_history.years.length - 1]} là ${money(inc.national_history.median[inc.national_history.median.length - 1])}.`)}
        ${tr(`The share living below $3.00 a day went from ${pct(inc.national_history.below_3[0])} in ${inc.national_history.years[0]} to ${pct(inc.national_history.below_3[inc.national_history.below_3.length - 1])}.`,
             `Tỷ lệ sống dưới 3,00 đô la mỗi ngày giảm từ ${pct(inc.national_history.below_3[0])} năm ${inc.national_history.years[0]} xuống ${pct(inc.national_history.below_3[inc.national_history.below_3.length - 1])}.`)}</p>
    <div class="chart-box chart-small"><canvas id="countryHistoryChart" aria-label="${tr(`${cname}'s median income and poverty rate over time`, `Trung vị thu nhập và tỷ lệ nghèo của ${cname} theo thời gian`)}"></canvas></div>
    <p class="small text-secondary">${tr("World Bank lined-up estimates for each year", "Ước tính theo năm của Ngân hàng Thế giới")} ${cite("pip")}.</p>` : ""}
    <h3 class="h5 mt-3">${tr("Poverty lines", "Chuẩn nghèo")}</h3>
    ${table([tr("Line ($ per person per day, 2021 prices)", "Chuẩn (đô la mỗi người mỗi ngày, giá 2021)"), tr("You", "Bạn"),
             tr("World below the line", "Thế giới dưới chuẩn"), tr(`${cname} below the line`, `${cname} dưới chuẩn`)],
        inc.lines.map(l => `<tr><td>${esc(l.label)}: ${esc(l.meaning)}</td><td>${l.above ? tr("&#10003; above", "&#10003; trên") : tr("&#10007; below", "&#10007; dưới")}</td>
            <td>${pct(l.share_below)}</td><td>${pct(l.country_share_below)}</td></tr>`))}
    ${(() => {
        const hd = inc.healthy_diet;
        const rule = pct(hd.income_share_rule * 100, 0);
        const worldLine = hd.world ? tr(`Worldwide, ${pct(hd.world.unaffordable_share * 100)} of people (${people(hd.world.unaffordable_people)}) couldn't afford one in ${hd.world.year}.`,
                                        `Trên thế giới, ${pct(hd.world.unaffordable_share * 100)} dân số (${people(hd.world.unaffordable_people)} người) không đủ khả năng chi trả năm ${hd.world.year}.`) : "";
        if (hd.cost_2021ppp === undefined) {
            return `<h3 class="h5 mt-4">${tr("Can you afford a healthy diet?", "Bạn có đủ tiền cho một chế độ ăn lành mạnh?")}</h3>
                <p class="small">${hd.unaffordable_pct !== undefined ? tr(`${pct(hd.unaffordable_pct)} of people in ${cname} can't afford a healthy diet (${hd.year}).`, `${pct(hd.unaffordable_pct)} dân số ${cname} không đủ khả năng chi trả cho chế độ ăn lành mạnh (${hd.year}).`) : ""} ${worldLine} ${cite("fpn")}</p>`;
        }
        return `<h3 class="h5 mt-4">${tr("Can you afford a healthy diet?", "Bạn có đủ tiền cho một chế độ ăn lành mạnh?")}</h3>
        <p>${tr(`The cheapest diet that meets dietary guidelines cost <strong>${money(hd.cost_2021ppp)}</strong> per person a day in ${cname} in ${hd.cost_year} (2021 int. $)${hd.cost_local_today !== undefined ? `, about ${fixed(hd.cost_local_today, 0)} ${esc(r.country.currency || "")} today` : ""}.
                 That's <strong>${pct(hd.share_of_income * 100, 0)}</strong> of your income per person. The FAO and World Bank count a healthy diet as unaffordable when it costs more than ${rule} of income, so for you it is <strong>${hd.affordable ? "affordable" : "not affordable"}</strong>.`,
                `Chế độ ăn rẻ nhất đáp ứng khuyến nghị dinh dưỡng có giá <strong>${money(hd.cost_2021ppp)}</strong> mỗi người mỗi ngày ở ${cname} năm ${hd.cost_year} (đô la quốc tế 2021)${hd.cost_local_today !== undefined ? `, khoảng ${fixed(hd.cost_local_today, 0)} ${esc(r.country.currency || "")} hiện nay` : ""}.
                 Tức là <strong>${pct(hd.share_of_income * 100, 0)}</strong> thu nhập bình quân đầu người của bạn. FAO và Ngân hàng Thế giới coi chế độ ăn lành mạnh là không vừa khả năng khi chi phí vượt ${rule} thu nhập, nên với bạn nó <strong>${hd.affordable ? "vừa khả năng" : "không vừa khả năng"}</strong>.`)}</p>
        <p class="small text-secondary">${tr(`${pct(hd.unaffordable_pct)} of people in ${cname}${hd.unaffordable_people ? ` (${people(hd.unaffordable_people)})` : ""} can't afford it (${hd.year}).`,
                                             `${pct(hd.unaffordable_pct)} dân số ${cname}${hd.unaffordable_people ? ` (${people(hd.unaffordable_people)} người)` : ""} không đủ khả năng (${hd.year}).`)} ${worldLine} ${cite("fpn")} ${cite("sofi_2026")}</p>`;
    })()}
    <h3 class="h5 mt-4">${tr("What it takes to move up", "Cần bao nhiêu để lên hạng")}</h3>
    ${(() => {
        const period = answers.income_period === "year" ? tr("a year", "mỗi năm") : tr("a month", "mỗi tháng");
        const local = inc.mode === "exact";
        const rank = t => t.pct === 50
            ? (t.scope === "world" ? tr("World median", "Trung vị thế giới") : tr(`${cname} median`, `Trung vị ${cname}`))
            : (t.scope === "world" ? tr(`Top ${100 - t.pct}% of the world`, `${100 - t.pct}% cao nhất thế giới`)
                                   : tr(`Top ${100 - t.pct}% in ${cname}`, `${100 - t.pct}% cao nhất ở ${cname}`));
        return table([tr("To reach", "Để đạt"), tr("Per person a day (2021 int. $)", "Mỗi người mỗi ngày (đô la quốc tế 2021)"),
                      local ? tr(`Your household's income, ${period} (${esc(r.country.currency || "")})`, `Thu nhập của hộ bạn, ${period} (${esc(r.country.currency || "")})`) : null,
                      tr("You", "Bạn")].filter(h => h !== null),
            inc.thresholds.map(t => `<tr><td>${rank(t)}</td><td>${money(t.ppp_per_day)}</td>
                ${local ? `<td>${fixed(t.local, 0)}</td>` : ""}
                <td>${t.reached ? tr("&#10003; reached", "&#10003; đã đạt") : tr(`needs ${fixed(t.multiple, 1)}&times; your income`, `cần gấp ${fixed(t.multiple, 1)} lần thu nhập của bạn`)}</td></tr>`));
    })()}
    <p class="small text-secondary">${tr(
        `Income thresholds of the national and world distributions${inc.mode === "exact" ? `, converted back into ${esc(r.country.currency || "local currency")} at today's prices for a household of ${answers.household_size}` : ""}.`,
        `Các ngưỡng thu nhập của phân phối quốc gia và thế giới${inc.mode === "exact" ? `, quy đổi ngược về ${esc(r.country.currency || "nội tệ")} theo giá hiện nay cho hộ ${answers.household_size} người` : ""}.`)} ${cite("pip")}</p>
    <h3 class="h5 mt-4">${tr("What if?", "Nếu như?")}</h3>
    <p class="small text-secondary">${tr(
        "Move the slider to see how your rank would change if your household's income per person were different. Each step roughly doubles or halves it.",
        "Kéo thanh trượt để xem thứ hạng thay đổi thế nào nếu thu nhập bình quân đầu người của hộ bạn khác đi. Mỗi bước tăng gấp đôi hoặc giảm một nửa.")}</p>
    <div class="whatif card bg-transparent border-secondary"><div class="card-body">
        <input type="range" class="form-range" id="whatif" min="-4" max="4" step="0.25" value="0" aria-label="${tr("Income multiplier", "Hệ số thu nhập")}">
        <div class="d-flex flex-wrap justify-content-between small" id="whatif-out" aria-live="polite"></div>
    </div></div>
    <h3 class="h5 mt-4">${tr("The same living standard elsewhere", "Cùng mức sống ở nơi khác")}</h3>
    <p class="small text-secondary">${tr(
        `Pick a country to see the ${inc.mode === "exact" ? `${answers.income_period === "year" ? "yearly" : "monthly"} income a household of ${answers.household_size}` : "monthly income per person"} would need there, in its own currency at today's prices, to live as you do, and where that would rank.`,
        `Chọn một nước để xem ${inc.mode === "exact" ? `một hộ ${answers.household_size} người cần thu nhập ${answers.income_period === "year" ? "mỗi năm" : "mỗi tháng"}` : "mỗi người cần thu nhập mỗi tháng"} bao nhiêu ở đó, bằng nội tệ theo giá hiện nay, để sống như bạn, và mức đó xếp hạng ra sao.`)}</p>
    <div class="d-flex flex-wrap gap-2 align-items-center">
        <select class="form-select w-auto mw-100" id="elsewhere" aria-label="${tr("Country to compare", "Nước để so sánh")}">
            ${D.countries.filter(c => SES.exactIncomeAvailable(c) && c.iso3 !== r.country.iso3)
                .map(c => `<option value="${c.iso3}"${c.iso3 === (r.country.iso3 === "USA" ? "DEU" : "USA") ? " selected" : ""}>${esc(c.name)}</option>`).join("")}
        </select>
        <span id="elsewhere-out" aria-live="polite"></span>
    </div>
    ${inc.mode === "exact" ? `<p class="small text-secondary mt-3">${tr("Prices", "Giá cả")}: ${tr(`${cname}'s consumer-price inflation since 2021`, `lạm phát giá tiêu dùng của ${cname} từ 2021`)}
        ${cite("imf_weo")}${inc.estimated_years.length || inc.extrapolated_years
            ? tr(` (the IMF has no figure for ${[...inc.estimated_years].join(", ") || "recent years"}, so we carried the latest rate forward)`,
                 ` (IMF chưa có số liệu cho ${[...inc.estimated_years].join(", ") || "các năm gần đây"}, nên chúng tôi dùng tiếp tỷ lệ gần nhất)`) : ""}.
        PPP: ${inc.ppp_source === "PIP" ? cite("pip") : cite("wdi")}.
        ${inc.currency_change ? tr(`Currency: ${esc(inc.currency_change)}; we converted the PPP factor to today's currency.`,
                                   `Tiền tệ: ${esc(inc.currency_change)}; chúng tôi đã quy đổi hệ số PPP sang đồng tiền hiện nay.`) : ""}</p>` : ""}`));

    // ---------------------------------------------------------------- around the world
    const every = inc.everywhere;
    const sorted = every.countries.slice().sort((a, b) => b.pct - a.pct);
    const countryRow = c => `<tr class="${c.iso3 === r.country.iso3 ? "you" : ""}"><td>${esc(c.name)}</td><td>${pct(c.pct)}</td>
        <td><div class="bar" style="width:${c.pct * 0.9}%"></div></td><td>${money(c.median)}</td></tr>`;
    const topHalf = every.countries.filter(c => c.pct >= 50).length, topTenth = every.countries.filter(c => c.pct >= 90).length;
    html.push(section("world", tr("Your income around the world", "Thu nhập của bạn trên khắp thế giới"), `
    <p>${tr(
        `With the same income per person (${money(inc.ppp_per_day)} a day in 2021 prices), here is where you'd rank in each of ${every.countries.length} economies. You'd be in the top half in <strong>${topHalf}</strong> of them and in the top 10% in <strong>${topTenth}</strong>.`,
        `Với cùng mức thu nhập mỗi người (${money(inc.ppp_per_day)} mỗi ngày theo giá 2021), đây là thứ hạng của bạn ở mỗi trong ${every.countries.length} nền kinh tế. Bạn thuộc nửa trên ở <strong>${topHalf}</strong> nước và thuộc nhóm 10% cao nhất ở <strong>${topTenth}</strong> nước.`)}</p>
    <div class="map-box"><svg id="worldMap" role="img" aria-label="${tr("World map shaded by your income percentile in each country", "Bản đồ thế giới tô màu theo bách phân vị thu nhập của bạn ở mỗi nước")}"></svg>
        <div class="map-legend small"><span>0%</span><span class="map-scale"></span><span>100%</span></div>
        <div class="map-tip small" id="mapTip" hidden></div></div>
    <div class="row g-4 mt-1">
        <div class="col-md-6"><h3 class="h5">${tr("By region", "Theo khu vực")}</h3>
            ${table([tr("Region", "Khu vực"), tr("Richer than", "Khá giả hơn")], every.regions.slice().sort((a, b) => b.pct - a.pct).map(g =>
                `<tr class="${g.code === r.country.region ? "you" : ""}"><td>${esc(g.name)}</td><td>${pct(g.pct)}</td></tr>`))}</div>
        <div class="col-md-6"><h3 class="h5">${tr("By World Bank income group", "Theo nhóm thu nhập của Ngân hàng Thế giới")}</h3>
            ${table([tr("Countries", "Nhóm nước"), tr("Richer than", "Khá giả hơn")], every.groups.map(g =>
                `<tr class="${g.name === r.country.income_group ? "you" : ""}"><td>${esc(g.name)}</td><td>${pct(g.pct)}</td></tr>`))}</div>
    </div>
    <details class="mt-3"><summary>${tr(`All ${every.countries.length} economies`, `Tất cả ${every.countries.length} nền kinh tế`)}</summary>
        ${table([tr("Economy", "Nền kinh tế"), tr("Richer than", "Khá giả hơn"), "", tr("Median ($/day)", "Trung vị ($/ngày)")], sorted.map(countryRow), "country-table")}</details>
    <p class="small text-secondary">${tr(
        `Each economy's ${refYear} distribution`, `Phân phối ${refYear} của mỗi nền kinh tế`)} ${cite("pip")}. ${tr(
        "Regions and income groups combine their economies' distributions, weighted by population. This compares your income in 2021 international dollars, which adjusts for each country's prices.",
        "Khu vực và nhóm thu nhập gộp phân phối của các nền kinh tế thành viên, theo trọng số dân số. Phép so sánh dùng thu nhập của bạn tính bằng đô la quốc tế 2021, đã điều chỉnh theo giá cả của từng nước.")}</p>`));

    // ---------------------------------------------------------------- history
    html.push(section("history", tr("The same income in other years", "Cùng mức thu nhập ở các năm khác"), `
    <p>${tr(
        `How your real income (${money(inc.ppp_per_day)} a day in 2021 prices) would have ranked in the world in earlier years. As the world got richer, the same income ranks lower.`,
        `Thu nhập thực tế của bạn (${money(inc.ppp_per_day)} mỗi ngày theo giá 2021) sẽ xếp hạng thế nào trên thế giới ở các năm trước. Khi thế giới giàu lên, cùng mức thu nhập đó xếp hạng thấp hơn.`)}</p>
    <div class="chart-box chart-small"><canvas id="historyChart" aria-label="${tr("Your world percentile over time", "Bách phân vị thế giới của bạn theo thời gian")}"></canvas></div>
    ${table([tr("Year", "Năm"), tr("You'd be richer than", "Bạn khá giả hơn"), tr("World below $3.00 a day", "Thế giới dưới 3,00 đô la/ngày"), tr("World population", "Dân số thế giới"), ""], inc.history.map(h =>
        `<tr><td>${h.year}</td><td>${pct(h.pct)}</td><td>${pct(h.share_below_3)}</td><td>${people(h.population)}</td>
            <td class="small text-secondary">${h.estimate_type === "nowcast" ? tr("nowcast", "ước tính tức thời") : h.estimate_type === "projection" ? tr("projection", "dự báo") : ""}</td></tr>`))}
    <p class="small text-secondary">${tr("World headcounts for each year", "Tỷ lệ của thế giới cho từng năm")} ${cite("pip")}. ${tr(
        `Between published lines we use the shape of the ${refYear} distribution, so earlier years are approximate.`,
        `Giữa các mức được công bố, chúng tôi dùng hình dạng phân phối năm ${refYear}, nên các năm trước chỉ là gần đúng.`)} ${nowcast ? tr(`${nowcast.year} is the World Bank's nowcast.`, `${nowcast.year} là ước tính tức thời của Ngân hàng Thế giới.`) : ""}</p>`));

    // ---------------------------------------------------------------- education
    const eduRows = edu.levels.map((label, i) => `<tr class="${i === edu.level ? "you" : ""}">
        <td>${esc(label)}${i === edu.level ? ` <span class="badge text-bg-light">${tr("you", "bạn")}</span>` : ""}</td>
        <td><div class="bar" style="width: ${edu.world_shares[i] * 2}%"></div> ${pct(edu.world_shares[i])}</td>
        ${edu.country_shares ? `<td>${pct(edu.country_shares[i])}</td>` : ""}
        ${edu.country_sex_shares ? `<td>${pct(edu.country_sex_shares[i])}</td>` : ""}</tr>`);
    let groupHtml = "";
    if (edu.group) {
        const g = edu.group;
        const who = tr(`${g.sex === "F" ? "women" : g.sex === "M" ? "men" : "people"} aged ${esc(g.age)}`,
                       `${g.sex === "F" ? "phụ nữ" : g.sex === "M" ? "nam giới" : "người"} ${esc(g.age)} tuổi`);
        groupHtml = `<h3 class="h5 mt-4">${tr(`Compared with ${who}`, `So với ${who}`)}</h3>
        <p>${tr(
            `In broad terms (${esc(lower(g.broad_label))}), you have more education than about <strong>${pct(g.world_pct)}</strong> of ${who} worldwide${g.country_pct !== undefined ? ` and ${pct(g.country_pct)} in ${cname}` : ""}.`,
            `Xét theo nhóm rộng (${esc(g.broad_label)}), bạn có học vấn cao hơn khoảng <strong>${pct(g.world_pct)}</strong> ${who} trên thế giới${g.country_pct !== undefined ? ` và ${pct(g.country_pct)} ở ${cname}` : ""}.`)}</p>
        ${table([tr("Level", "Trình độ"), tr("World", "Thế giới"), g.country_shares ? cname : ""].filter(Boolean), g.levels.map((label, i) =>
            `<tr class="${label === g.broad_label ? "you" : ""}"><td>${esc(label)}</td><td>${pct(g.world_shares[i])}</td>${g.country_shares ? `<td>${pct(g.country_shares[i])}</td>` : ""}</tr>`))}
        <p class="small text-secondary">${tr(`Barro-Lee estimates for ${g.year}`, `Ước tính Barro-Lee năm ${g.year}`)} ${cite("barro_lee")}; ${tr(
            "only four broad levels are available by age and sex.", "chỉ có bốn nhóm trình độ rộng theo tuổi và giới.")}</p>`;
    } else if (!answers.age) {
        groupHtml = `<p class="small text-secondary">${tr("Tell us your age in the quiz to compare with people your age.",
            "Hãy cho biết tuổi trong bài trắc nghiệm để so với những người cùng tuổi.")}</p>`;
    }
    html.push(section("education", tr("Education", "Học vấn"), `
    <p>${tr(
        `Your highest level is <strong>${esc(lower(edu.label))}</strong>. That's more education than about <strong>${pct(edu.global_pct)}</strong> of the world's adults aged 25 and over.`,
        `Trình độ cao nhất của bạn là <strong>${esc(edu.label)}</strong>, cao hơn khoảng <strong>${pct(edu.global_pct)}</strong> người trưởng thành từ 25 tuổi trở lên trên thế giới.`)}
        ${edu.national_pct !== undefined ? tr(`In ${cname} the figure is ${pct(edu.national_pct)}.`, `Ở ${cname}, con số này là ${pct(edu.national_pct)}.`) : ""}
        ${edu.sex && (edu.world_sex_pct !== undefined || edu.national_sex_pct !== undefined) ? tr(
            `Among ${edu.sex === "F" ? "women" : "men"} aged 25+, the figures are ${pct(edu.world_sex_pct)} worldwide${edu.national_sex_pct !== undefined ? ` and ${pct(edu.national_sex_pct)} in ${cname}` : ""}.`,
            `Trong số ${edu.sex === "F" ? "phụ nữ" : "nam giới"} từ 25 tuổi, các con số là ${pct(edu.world_sex_pct)} trên thế giới${edu.national_sex_pct !== undefined ? ` và ${pct(edu.national_sex_pct)} ở ${cname}` : ""}.`) : ""}
        ${tr(`${pct(edu.same_level_pct)} of adults worldwide share your level and ${pct(edu.higher_pct)} have gone further.`,
             `${pct(edu.same_level_pct)} người trưởng thành trên thế giới có cùng trình độ với bạn và ${pct(edu.higher_pct)} học cao hơn.`)}</p>
    ${table([tr("Level (ISCED 2011)", "Trình độ (ISCED 2011)"), tr("World", "Thế giới"), edu.country_shares ? `${cname}${edu.country_year ? ` (${edu.country_year})` : ""}` : "",
             edu.country_sex_shares ? tr(`${edu.sex === "F" ? "Women" : "Men"} in ${cname}`, `${edu.sex === "F" ? "Phụ nữ" : "Nam giới"} ở ${cname}`) : ""].filter(Boolean), eduRows, "edu-table")}
    <p class="small text-secondary">${tr("World and national attainment of adults 25+", "Trình độ học vấn của người từ 25 tuổi, thế giới và quốc gia")} ${cite("uis_attainment")}${edu.country_source === "Barro-Lee" ? `; ${cname}: ${tr("Barro-Lee 2015, mapped to these levels", "Barro-Lee 2015, quy đổi sang các trình độ này")} ${cite("barro_lee")}` : ""}.
        ${edu.country_mean_years ? tr(`Average years of schooling in ${cname} (ages 25-64, 2015): ${edu.country_mean_years}.`, `Số năm đi học trung bình ở ${cname} (25-64 tuổi, 2015): ${fixed(edu.country_mean_years, 2)}.`) : ""}</p>
    ${groupHtml}
    ${mobilityHtml(r.mobility)}`));

    // ---------------------------------------------------------------- social mobility (within education)
    function mobilityHtml(m) {
        if (!m || (!m.parents && !m.needs_age)) return "";
        const title = `<h3 class="h5 mt-4">${tr("Compared with your parents", "So với bố mẹ bạn")}</h3>`;
        if (m.needs_age) return `${title}<p class="text-secondary">${tr("Give your age group to compare with your parents' generation.", "Hãy cho biết nhóm tuổi để so sánh với thế hệ của bố mẹ bạn.")}</p>`;
        const who = p => (p.parent === "mother" ? tr("Your mother", "Mẹ bạn") : tr("Your father", "Bố bạn"));
        const peers = p => (p.sex === "F" ? tr("women", "phụ nữ") : tr("men", "nam giới"));
        const lines = m.parents.map(p => `<li>${tr(
            `${who(p)} (${esc(lower(p.label))}) was better educated than about <strong>${pct(p.national_pct !== undefined ? p.national_pct : p.world_pct)}</strong> of ${peers(p)} of the same generation ${p.national_pct !== undefined ? `in ${cname}` : "worldwide"}${p.national_pct !== undefined ? ` (${pct(p.world_pct)} worldwide)` : ""}.`,
            `${who(p)} (${esc(p.label.toLowerCase())}) có học vấn cao hơn khoảng <strong>${pct(p.national_pct !== undefined ? p.national_pct : p.world_pct)}</strong> ${peers(p)} cùng thế hệ ${p.national_pct !== undefined ? `ở ${cname}` : "trên thế giới"}${p.national_pct !== undefined ? ` (${pct(p.world_pct)} trên thế giới)` : ""}.`)}</li>`);
        const dir = {up: tr("went further in education than", "học cao hơn"), same: tr("reached the same broad level as", "đạt cùng bậc học với"), down: tr("didn't go as far in education as", "chưa học cao bằng")}[m.direction];
        const parentName = m.parents.length > 1 ? tr("your better-educated parent", "người có học vấn cao hơn trong bố mẹ bạn") : (m.best === "mother" ? tr("your mother", "mẹ bạn") : tr("your father", "bố bạn"));
        let rankText = "";
        if (m.rank_change !== undefined) {
            const own = m.basis === "country" ? m.own_national_pct : m.own_world_pct;
            const where = m.basis === "country" ? tr(`in ${cname}`, `ở ${cname}`) : tr("worldwide", "trên thế giới");
            rankText = tr(` Among people your age ${where}, you rank above about <strong>${pct(own)}</strong>, so relative to your generation you ${m.rank_change > 0 ? `<strong>moved up ${fixed(m.rank_change, 1)} points</strong>` : m.rank_change < 0 ? `<strong>moved down ${fixed(-m.rank_change, 1)} points</strong>` : "held the same position"} compared with ${parentName}.`,
                          ` Trong số những người cùng tuổi ${where}, bạn xếp trên khoảng <strong>${pct(own)}</strong>, nên so với thế hệ của mình bạn ${m.rank_change > 0 ? `<strong>tăng ${fixed(m.rank_change, 1)} điểm</strong>` : m.rank_change < 0 ? `<strong>giảm ${fixed(-m.rank_change, 1)} điểm</strong>` : "giữ nguyên vị trí"} so với ${parentName}.`);
        } else {
            rankText = tr(" You're probably still in education, so we don't rank you against your own generation yet.", " Có lẽ bạn vẫn đang đi học, nên chúng tôi chưa xếp hạng bạn trong thế hệ của mình.");
        }
        return `${title}<ul class="small">${lines.join("")}</ul>
            <p>${tr(`You (${esc(lower(m.own_label))}) ${dir} ${parentName}.`, `Bạn (${esc(m.own_label.toLowerCase())}) ${dir} ${parentName}.`)}${rankText}</p>
            <p class="small text-secondary">${tr(
                `Parents are compared with people of their sex born around ${m.cohort_born}, assuming they were about ${m.parent_gap} when you were born, using Barro-Lee attainment at ages 35-44 in ${m.cohort_year}. Comparing ranks rather than levels allows for the fact that schooling expanded everywhere: going further than your parents is common, moving up relative to your generation is not. Not scored.`,
                `Bố mẹ được so với những người cùng giới sinh khoảng năm ${m.cohort_born}, giả định họ khoảng ${m.parent_gap} tuổi khi bạn ra đời, dựa trên trình độ học vấn ở tuổi 35-44 năm ${m.cohort_year} của Barro-Lee. So sánh thứ hạng thay vì bậc học tính đến việc giáo dục đã mở rộng ở khắp nơi: học cao hơn bố mẹ là phổ biến, còn tăng hạng so với thế hệ mình thì không. Không tính điểm.`)} ${cite("barro_lee")}</p>`;
    }

    // ---------------------------------------------------------------- occupation (within work)
    function occupationHtml(o) {
        if (!o) return "";
        const levelName = {1: tr("1 (simple, routine tasks)", "1 (công việc đơn giản, lặp lại)"), 2: tr("2 (operating machinery, handling information, trades)", "2 (vận hành máy móc, xử lý thông tin, nghề thủ công)"),
                           3: tr("3 (complex technical and practical tasks)", "3 (công việc kỹ thuật và thực hành phức tạp)"), 4: tr("4 (complex problem-solving, usually a degree)", "4 (giải quyết vấn đề phức tạp, thường cần bằng đại học)")};
        const head = [tr("Occupation group", "Nhóm nghề"), tr(`${o.economies} economies`, `${o.economies} nền kinh tế`), o.country_shares ? cname : null].filter(h => h !== null);
        const rows = o.labels.map((label, i) => `<tr class="${i === o.labels.indexOf(o.label) ? "table-active" : ""}"><td>${esc(label.split(" (")[0])}${label === o.label ? ` &larr; ${tr("you", "bạn")}` : ""}</td>
            <td>${pct(o.pooled_shares[i])}</td>${o.country_shares ? `<td>${pct(o.country_shares[i])}</td>` : ""}</tr>`);
        const like = [];
        if (o.sex_country_same !== undefined) like.push(tr(`${pct(o.sex_country_same)} of working ${answers.sex === "F" ? "women" : "men"} in ${cname}`, `${pct(o.sex_country_same)} ${answers.sex === "F" ? "phụ nữ" : "nam giới"} đang làm việc ở ${cname}`));
        if (o.area_country_same !== undefined) like.push(tr(`${pct(o.area_country_same)} of workers in ${answers.area === "urban" ? "urban" : "rural"} ${cname}`, `${pct(o.area_country_same)} lao động ở ${answers.area === "urban" ? "thành thị" : "nông thôn"} ${cname}`));
        return `<h3 class="h5 mt-4">${tr("Your occupation", "Nghề nghiệp của bạn")}</h3>
        <p>${o.skill_level ? tr(`ISCO-08 puts this group at skill level <strong>${levelName[o.skill_level]}</strong>. By skill level, your occupation ranks above about <strong>${pct(o.world_pct)}</strong> of workers in the ${o.economies} economies with survey data${o.national_pct !== undefined ? ` and ${pct(o.national_pct)} in ${cname}` : ""}.`,
                                `ISCO-08 xếp nhóm này ở trình độ kỹ năng <strong>${levelName[o.skill_level]}</strong>. Theo trình độ kỹ năng, nghề của bạn xếp trên khoảng <strong>${pct(o.world_pct)}</strong> lao động ở ${o.economies} nền kinh tế có số liệu khảo sát${o.national_pct !== undefined ? ` và ${pct(o.national_pct)} ở ${cname}` : ""}.`)
                             : tr("The armed forces span several skill levels, so this occupation isn't ranked.", "Lực lượng vũ trang gồm nhiều trình độ kỹ năng, nên nghề này không được xếp hạng.")}
            ${o.country_same !== undefined ? tr(` ${pct(o.country_same)} of workers in ${cname} are in the same group${like.length ? `, as are ${like.join(" and ")}` : ""}.`,
                                                ` ${pct(o.country_same)} lao động ở ${cname} cùng nhóm với bạn${like.length ? `, cũng như ${like.join(" và ")}` : ""}.`)
                                           : tr(` We don't have a usable recent survey of occupations for ${cname}.`, ` Chúng tôi chưa có khảo sát nghề nghiệp gần đây đủ tin cậy cho ${cname}.`)}</p>
        ${table(head, rows)}
        <p class="small text-secondary">${tr(`Shares of employed people aged 15-64 from harmonised household and labour-force surveys${o.year ? ` (${cname}: ${o.year})` : ""}; the ${o.economies} economies cover ${pct(o.employed_covered_pct, 0)} of the world's workers, and their pooled shares are weighted by employment. It is not a world estimate: China has no usable survey.`,
                                             `Tỷ lệ người có việc làm 15-64 tuổi từ các khảo sát hộ gia đình và lực lượng lao động đã chuẩn hóa${o.year ? ` (${cname}: ${o.year})` : ""}; ${o.economies} nền kinh tế này chiếm ${pct(o.employed_covered_pct, 0)} lao động thế giới, tỷ lệ gộp được gia quyền theo số người có việc. Đây không phải ước tính toàn cầu: Trung Quốc không có khảo sát dùng được.`)} ${cite("join")} ${cite("isco_08")}</p>`;
    }

    // ---------------------------------------------------------------- work
    if (work.status) {
        const statusRows = [["employee", tr("Employees (wage and salary)", "Người làm công hưởng lương")], ["employer", tr("Employers", "Chủ sử dụng lao động")],
            ["own_account", tr("Own-account workers", "Lao động tự làm")], ["family_worker", tr("Contributing family workers", "Lao động gia đình")]].map(([k, label]) =>
            `<tr class="${k === work.status ? "you" : ""}"><td>${label}${k === work.status ? ` <span class="badge text-bg-light">${tr("you", "bạn")}</span>` : ""}</td>
                <td>${work.world ? pct(work.world[k]) : "-"}</td><td>${work.country ? pct(work.country[k]) : "-"}</td>
                ${work.sex ? `<td>${work.sex_world ? pct(work.sex_world[k]) : "-"}</td><td>${work.sex_country ? pct(work.sex_country[k]) : "-"}</td>` : ""}</tr>`);
        const sexHead = work.sex ? [tr(`${work.sex === "F" ? "Women" : "Men"}, world`, `${work.sex === "F" ? "Nữ" : "Nam"}, thế giới`),
                                    tr(`${work.sex === "F" ? "Women" : "Men"}, ${cname}`, `${work.sex === "F" ? "Nữ" : "Nam"}, ${cname}`)] : [];
        const sectorRows = [["agriculture", tr("Agriculture", "Nông nghiệp")], ["industry", tr("Industry", "Công nghiệp")], ["services", tr("Services", "Dịch vụ")]].map(([k, label]) =>
            `<tr class="${k === work.sector ? "you" : ""}"><td>${label}${k === work.sector ? ` <span class="badge text-bg-light">${tr("you", "bạn")}</span>` : ""}</td>
                <td>${work.world_sectors ? pct(work.world_sectors[k]) : "-"}</td><td>${work.country_sectors ? pct(work.country_sectors[k]) : "-"}</td>
                ${work.sex ? `<td>${work.sex_world_sectors ? pct(work.sex_world_sectors[k]) : "-"}</td><td>${work.sex_country_sectors ? pct(work.sex_country_sectors[k]) : "-"}</td>` : ""}</tr>`);
        let workText;
        if (work.employed) {
            workText = (work.vulnerable
                ? tr(` The ILO counts own-account and contributing family work as <em>vulnerable employment</em>: less likely to have formal contracts, social protection or steady pay. ${pct(work.world.vulnerable)} of the world's workers are in this position${work.country ? `, and ${pct(work.country.vulnerable)} in ${cname}` : ""}.`,
                     ` ILO xếp lao động tự làm và lao động gia đình vào nhóm <em>việc làm dễ tổn thương</em>: ít có hợp đồng chính thức, bảo trợ xã hội hay thu nhập ổn định. ${pct(work.world.vulnerable)} lao động thế giới ở vị trí này${work.country ? `, và ${pct(work.country.vulnerable)} ở ${cname}` : ""}.`)
                : tr(` Wage and salaried workers and employers are not in what the ILO calls vulnerable employment, unlike ${pct(work.world.vulnerable)} of the world's workers${work.country ? ` (${pct(work.country.vulnerable)} in ${cname})` : ""}.`,
                     ` Người làm công hưởng lương và chủ sử dụng lao động không thuộc nhóm việc làm dễ tổn thương theo ILO, khác với ${pct(work.world.vulnerable)} lao động thế giới${work.country ? ` (${pct(work.country.vulnerable)} ở ${cname})` : ""}.`))
                + (work.occupation && work.occupation.world_pct !== undefined
                    ? tr(` Combining that with your occupation's skill level, your work situation is better than about <strong>${pct(work.global_pct)}</strong> of workers worldwide${work.national_pct !== undefined ? ` and ${pct(work.national_pct)} in ${cname}` : ""}.`,
                         ` Kết hợp với trình độ kỹ năng của nghề nghiệp, tình trạng việc làm của bạn tốt hơn khoảng <strong>${pct(work.global_pct)}</strong> lao động trên thế giới${work.national_pct !== undefined ? ` và ${pct(work.national_pct)} ở ${cname}` : ""}.`)
                    : tr(` On this measure your work situation is better than about <strong>${pct(work.global_pct)}</strong> of workers worldwide${work.national_pct !== undefined ? ` and ${pct(work.national_pct)} in ${cname}` : ""}.`,
                         ` Theo thước đo này, tình trạng việc làm của bạn tốt hơn khoảng <strong>${pct(work.global_pct)}</strong> lao động trên thế giới${work.national_pct !== undefined ? ` và ${pct(work.national_pct)} ở ${cname}` : ""}.`));
        } else if (work.status === "unemployed") {
            workText = tr(` Unemployment is ${pct(work.unemployment.world)} of the world's labour force${work.unemployment.country !== null ? ` and ${pct(work.unemployment.country)} in ${cname}` : ""}.`,
                          ` Tỷ lệ thất nghiệp là ${pct(work.unemployment.world)} lực lượng lao động thế giới${work.unemployment.country !== null ? ` và ${pct(work.unemployment.country)} ở ${cname}` : ""}.`);
        } else {
            workText = tr(` ${pct(work.participation.world)} of people aged 15+ worldwide are in the labour force${work.participation.country !== null ? ` (${pct(work.participation.country)} in ${cname})` : ""}. This dimension isn't scored for people outside the labour force.`,
                          ` ${pct(work.participation.world)} người từ 15 tuổi trên thế giới tham gia lực lượng lao động${work.participation.country !== null ? ` (${pct(work.participation.country)} ở ${cname})` : ""}. Khía cạnh này không chấm điểm cho người ngoài lực lượng lao động.`);
        }
        html.push(section("work", tr("Work", "Công việc"), `
        <p>${tr("You described yourself as:", "Bạn mô tả mình là:")} <strong>${esc(lower(work.label))}</strong>.${workText}
            ${work.sex && work.sex_participation && work.sex_participation.country !== null ? tr(
                ` ${pct(work.sex_participation.country)} of ${work.sex === "F" ? "women" : "men"} aged 15+ in ${cname} are in the labour force (${pct(work.sex_participation.world)} worldwide), and ${pct(work.sex_unemployment.country)} of those are unemployed.`,
                ` ${pct(work.sex_participation.country)} ${work.sex === "F" ? "phụ nữ" : "nam giới"} từ 15 tuổi ở ${cname} tham gia lực lượng lao động (${pct(work.sex_participation.world)} trên thế giới), và ${pct(work.sex_unemployment.country)} trong số đó thất nghiệp.`) : ""}</p>
        <div class="row g-4">
            <div class="col-lg-6"><h3 class="h6">${tr("Workers by status in employment", "Lao động theo vị thế việc làm")}</h3>${table([tr("Status", "Vị thế"), tr("World", "Thế giới"), cname, ...sexHead], statusRows)}</div>
            <div class="col-lg-6"><h3 class="h6">${tr("Workers by sector", "Lao động theo ngành")}</h3>${table([tr("Sector", "Ngành"), tr("World", "Thế giới"), cname, ...sexHead], sectorRows)}</div>
        </div>
        <p class="small text-secondary">${tr(`ILO modelled estimates, ${work.world ? work.world.year : ""}`, `Ước tính mô hình của ILO, ${work.world ? work.world.year : ""}`)} ${cite("ilo_wdi")}. ${tr(
            "Status in employment ranks only two categories (vulnerable or not), so it is coarse on its own.", "Vị thế việc làm chỉ xếp hạng hai nhóm (dễ tổn thương hay không), nên tự nó còn thô.")}</p>
        ${occupationHtml(work.occupation)}`));
    }

    // ---------------------------------------------------------------- living standards
    const mark = has => has === null || has === undefined ? `<span class="text-secondary" title="${tr("Not answered", "Chưa trả lời")}">&ndash;</span>`
        : has ? `<span class="text-success" title="${tr("You have this", "Bạn có")}">&#10003;</span>` : `<span class="text-danger" title="${tr("You lack this", "Bạn không có")}">&#10007;</span>`;
    const areaHead = liv.area ? tr(`${cname}, ${liv.area} areas`, `${cname}, ${liv.area === "urban" ? "thành thị" : "nông thôn"}`) : null;
    html.push(section("living", tr("Living standards at home", "Mức sống trong nhà"), `
    ${liv.answered ? `<p>${tr(
        `Averaged over the ${liv.answered} services you answered about, you're better off than about <strong>${pct(liv.global_pct)}</strong> of people worldwide.`,
        `Tính trung bình trên ${liv.answered} dịch vụ bạn đã trả lời, bạn khá hơn khoảng <strong>${pct(liv.global_pct)}</strong> người trên thế giới.`)}
        ${liv.lower_bound_pct ? tr(`At the very least, <strong>${pct(liv.lower_bound_pct)}</strong> of the world lacks something you have.`,
                                   `Ít nhất <strong>${pct(liv.lower_bound_pct)}</strong> dân số thế giới thiếu một thứ mà bạn có.`) : ""}</p>`
        : `<p class="text-secondary">${tr("You skipped this section.", "Bạn đã bỏ qua phần này.")}</p>`}
    ${table(["", tr("Service", "Dịch vụ"), tr("World without it", "Thế giới không có"), liv.region_name ? esc(liv.region_name) : null, cname, areaHead].filter(x => x !== null),
        liv.items.map(i => `<tr><td class="fs-5">${mark(i.has)}</td>
            <td>${esc(i.label)}${i.status ? `<div class="small text-secondary">${tr("Your answer", "Câu trả lời")}: ${esc(i.status)}</div>` : ""}</td>
            <td class="text-nowrap">${pct(i.share_without_pct, 0)} <span class="small text-secondary">(${people(i.people_without)})</span></td>
            ${liv.region_name ? `<td>${pct(i.region_without_pct, 0)}</td>` : ""}
            <td>${pct(i.country_without_pct, 0)}</td>${areaHead ? `<td>${pct(i.area_without_pct, 0)}</td>` : ""}</tr>`))}
    <details><summary class="small">${tr("Notes and sources for each service", "Ghi chú và nguồn cho từng dịch vụ")}</summary><ul class="small mt-2">
        ${liv.items.map(i => `<li><strong>${esc(i.label)}:</strong> ${esc(i.note)} ${cite(i.cite)}${i.wdi ? tr(` World Bank indicator ${esc(i.wdi)}.`, ` Chỉ số Ngân hàng Thế giới ${esc(i.wdi)}.`) : ""}</li>`).join("")}
    </ul></details>
    <p class="small text-secondary">${tr(
        `"Safely managed" water and sanitation also require the water to be free from contamination and waste to be safely treated, which you can't check yourself, so we classify your answers approximately. Country, region and urban/rural figures`,
        `Nước và vệ sinh "được quản lý an toàn" còn đòi hỏi nước không bị nhiễm bẩn và chất thải được xử lý an toàn, điều bạn không tự kiểm tra được, nên câu trả lời được phân loại gần đúng. Số liệu quốc gia, khu vực, thành thị/nông thôn`)} ${cite("wdi")}, ${tr(`mostly for ${refYear}.`, `phần lớn cho năm ${refYear}.`)}</p>`));

    // ---------------------------------------------------------------- MPI
    if (r.mpi.available) {
        const m = r.mpi, mpiFacts = D.facts.mpi;
        const statusText = {
            severe: tr("severely multidimensionally poor (deprived in half or more of the weighted indicators)", "nghèo đa chiều nghiêm trọng (thiếu hụt từ một nửa số chỉ số có trọng số trở lên)"),
            poor: tr("multidimensionally poor (deprived in a third or more of the weighted indicators)", "nghèo đa chiều (thiếu hụt từ một phần ba số chỉ số có trọng số trở lên)"),
            vulnerable: tr("vulnerable to multidimensional poverty (deprived in 20-33% of the weighted indicators)", "có nguy cơ nghèo đa chiều (thiếu hụt 20-33% số chỉ số có trọng số)"),
            not_poor: tr("not multidimensionally poor", "không nghèo đa chiều"),
        }[m.status];
        const dimLabel = {health: tr("Health", "Sức khỏe"), education: tr("Education", "Giáo dục"), living: tr("Living standards", "Mức sống")};
        html.push(section("mpi", tr("Multidimensional Poverty Index", "Chỉ số Nghèo đa chiều"), `
        <p>${tr(
            `Your household's deprivation score is <strong>${pct(m.score)}</strong>, so by the Global MPI's rules you would count as <strong>${statusText}</strong>.`,
            `Điểm thiếu hụt của hộ bạn là <strong>${pct(m.score)}</strong>, nên theo quy tắc của MPI toàn cầu, hộ bạn được xem là <strong>${statusText}</strong>.`)}
            ${m.deprived.length ? tr(`You're deprived in: ${m.deprived.map(esc).join(", ")}.`, `Thiếu hụt về: ${m.deprived.map(esc).join(", ")}.`)
                                : tr("You're not deprived in any indicator you answered.", "Hộ bạn không thiếu hụt ở chỉ số nào đã trả lời.")}
            ${tr(`The 2026 Global MPI counts ${people(mpiFacts.people)} people as multidimensionally poor in ${mpiFacts.countries} countries (${people(mpiFacts.children)} of them children)`,
                 `MPI toàn cầu 2026 ghi nhận ${people(mpiFacts.people)} người nghèo đa chiều ở ${mpiFacts.countries} quốc gia (trong đó ${people(mpiFacts.children)} là trẻ em)`)} ${cite(mpiFacts.cite)}.</p>
        ${table([tr("Dimension", "Khía cạnh"), tr("Indicator", "Chỉ số"), tr("Weight", "Trọng số"), tr("Deprived?", "Thiếu hụt?")], m.indicators.map(i => `<tr><td>${dimLabel[i.dimension]}</td><td>${esc(i.label)}</td>
            <td>${pct(i.weight * 100)}</td><td>${i.deprived ? `<span class="text-danger">${tr("yes", "có")}</span>` : `<span class="text-success">${tr("no", "không")}</span>`}</td></tr>`))}
        <p class="small text-secondary">${tr("Indicators, cutoffs and weights follow the Global MPI", "Chỉ số, ngưỡng và trọng số theo MPI toàn cầu")} ${cite("ophi_mpi")}. ${tr(
            `Each dimension weighs a third, split equally among the indicators you answered; ${m.dimensions_used.length < 3 ? "a dimension you skipped was dropped and the others re-weighted; " : ""}nutrition is self-reported here, whereas surveys measure it.`,
            `Mỗi khía cạnh chiếm một phần ba, chia đều cho các chỉ số bạn đã trả lời; ${m.dimensions_used.length < 3 ? "khía cạnh bị bỏ qua được loại ra và các khía cạnh còn lại được tính lại trọng số; " : ""}dinh dưỡng ở đây là tự khai, còn các cuộc khảo sát thì đo trực tiếp.`)}</p>
        ${r.crowding ? `<p>${r.crowding.overcrowded
            ? tr("<strong>Your home is overcrowded</strong> by the UN-Habitat standard", "<strong>Nhà bạn chật chội</strong> theo tiêu chuẩn của UN-Habitat")
            : tr("Your home is not overcrowded by the UN-Habitat standard", "Nhà bạn không chật chội theo tiêu chuẩn của UN-Habitat")}
            (${tr(`${fixed(r.crowding.per_room, 1)} people per sleeping room; more than 3 counts as overcrowded`, `${fixed(r.crowding.per_room, 1)} người mỗi phòng ngủ; trên 3 người là chật chội`)}) ${cite("un_habitat")}.</p>` : ""}`));
    }

    // ---------------------------------------------------------------- security
    const food = D.facts.food, findex = D.facts.findex;
    const fiesName = {secure: tr("food security", "an ninh lương thực"), mild: tr("mild food insecurity", "mất an ninh lương thực nhẹ"),
                      moderate: tr("moderate food insecurity", "mất an ninh lương thực vừa"), severe: tr("severe food insecurity", "mất an ninh lương thực nghiêm trọng")};
    let foodHtml;
    if (sec.fies_raw !== undefined) {
        const fw = sec.food_world, fc = sec.food_country;
        foodHtml = `<p>${tr(`You answered yes to <strong>${sec.fies_raw} of 8</strong> questions on the Food Insecurity Experience Scale`,
                            `Bạn trả lời "có" với <strong>${sec.fies_raw} trên 8</strong> câu của Thang đo Trải nghiệm Mất an ninh Lương thực`)}
            ${cite("fies")}, ${tr("which roughly corresponds to", "tương ứng khoảng với")} <strong>${fiesName[sec.fies_level]}</strong> ${cite("fies_raw_score")}.
            ${sec.fies_pct !== undefined ? tr(`That's more food-secure than about <strong>${pct(sec.fies_pct)}</strong> of people worldwide${sec.fies_national_pct !== undefined ? ` and ${pct(sec.fies_national_pct)} in ${cname}` : ""}.`,
                                              `Tức là an ninh lương thực hơn khoảng <strong>${pct(sec.fies_pct)}</strong> người trên thế giới${sec.fies_national_pct !== undefined ? ` và ${pct(sec.fies_national_pct)} ở ${cname}` : ""}.`) : ""}</p>
            ${table(["", tr("World", "Thế giới"), cname], [
                [tr("Severe food insecurity", "Mất an ninh lương thực nghiêm trọng"), fw && fw.severe * 100, fc && fc.severe * 100],
                [tr("Moderate (not severe)", "Mức vừa (không nghiêm trọng)"), fw && fw.moderate * 100, fc && fc.moderate * 100],
                [tr("Food secure or mildly insecure", "An ninh hoặc mất an ninh nhẹ"), fw && fw.secure * 100, fc && fc.secure * 100],
            ].map(([label, w, c]) => `<tr><td>${label}</td><td>${pct(w)}</td><td>${pct(c)}</td></tr>`))}
            <p class="small text-secondary">${tr(`FAO estimates for ${fw ? fw.year : ""}`, `Ước tính của FAO năm ${fw ? fw.year : ""}`)} ${cite("fao_wdi")}. ${tr(
                `The latest SOFI report puts moderate or severe food insecurity at ${pct(food.moderate_or_severe_share * 100)} in ${food.year}`,
                `Báo cáo SOFI mới nhất ghi nhận tỷ lệ mất an ninh lương thực vừa hoặc nghiêm trọng là ${pct(food.moderate_or_severe_share * 100)} năm ${food.year}`)} ${cite(food.cite)}.</p>`;
    } else if (sec.fies_answered) {
        foodHtml = `<p class="text-secondary">${tr(`You answered ${sec.fies_answered} of the 8 food questions; all 8 are needed for a score.`,
                                                   `Bạn đã trả lời ${sec.fies_answered} trên 8 câu về lương thực; cần đủ 8 câu để tính điểm.`)}</p>`;
    } else {
        foodHtml = `<p class="text-secondary">${tr("Not answered.", "Chưa trả lời.")}</p>`;
    }
    const bank = [];
    if (sec.account !== undefined) bank.push(`${sec.account ? tr("You have an account.", "Bạn có tài khoản.") : tr("You don't have an account.", "Bạn không có tài khoản.")}
        ${tr(`${pct(sec.account_world, 0)} of adults worldwide have one${sec.account_country !== null ? `, and ${pct(sec.account_country, 0)} in ${cname}` : ""}.`,
             `${pct(sec.account_world, 0)} người trưởng thành trên thế giới có tài khoản${sec.account_country !== null ? `, và ${pct(sec.account_country, 0)} ở ${cname}` : ""}.`)}`);
    if (sec.saved !== undefined) bank.push(`${sec.saved ? tr("You saved money in the past year.", "Bạn đã tiết kiệm được tiền trong năm qua.") : tr("You didn't save money in the past year.", "Bạn không tiết kiệm được tiền trong năm qua.")}
        ${tr(`For comparison, ${pct(findex.saved_in_account_share_lmic * 100, 0)} of adults in low- and middle-income economies saved in a financial account in 2024.`,
             `Để so sánh, ${pct(findex.saved_in_account_share_lmic * 100, 0)} người trưởng thành ở các nền kinh tế thu nhập thấp và trung bình đã tiết kiệm qua tài khoản năm 2024.`)}`);
    html.push(section("security", tr("Financial security", "An ninh tài chính"), `
    ${sec.global_pct !== undefined ? `<p>${tr(`Combining basic needs, food security and emergency money, you're more financially secure than about <strong>${pct(sec.global_pct)}</strong> of people worldwide.`,
                                              `Gộp nhu cầu cơ bản, an ninh lương thực và khả năng xoay tiền khẩn cấp, bạn an toàn về tài chính hơn khoảng <strong>${pct(sec.global_pct)}</strong> người trên thế giới.`)}</p>` : ""}
    <div class="row g-4">
        <div class="col-lg-6"><h3 class="h5">${tr("Basic needs", "Nhu cầu cơ bản")}</h3>
            ${sec.gallup_group ? `<p>${tr(`You're in Gallup's <strong>${esc(lower(sec.gallup_label))}</strong> group:`, `Bạn thuộc nhóm <strong>${esc(sec.gallup_label)}</strong> của Gallup:`)} ${esc(lower(sec.gallup_definition))}
                ${tr(`${pct(sec.gallup_share_pct, 0)} of the world's adults are in this group. You're more secure than about <strong>${pct(sec.gallup_pct)}</strong> of adults.`,
                     `${pct(sec.gallup_share_pct, 0)} người trưởng thành trên thế giới thuộc nhóm này. Bạn an toàn hơn khoảng <strong>${pct(sec.gallup_pct)}</strong> người trưởng thành.`)}
                ${sec.gallup_group === "high" ? tr(`You're one of the roughly ${people(D.facts.gallup_people_high)} people Gallup found struggling with no safety net.`,
                                                   `Bạn là một trong khoảng ${people(D.facts.gallup_people_high)} người mà Gallup thấy đang chật vật mà không có chỗ dựa.`) : ""}
                ${cite("gallup_2020")} ${cite("upi_gallup_2020")}</p>` : `<p class="text-secondary">${tr("Not answered.", "Chưa trả lời.")}</p>`}
            <h3 class="h5 mt-4">${tr("Banking and saving", "Tài khoản và tiết kiệm")}</h3>
            ${bank.length ? `<ul class="small">${bank.map(b => `<li>${b}</li>`).join("")}</ul>` : `<p class="text-secondary">${tr("Not answered.", "Chưa trả lời.")}</p>`}
            ${sec.account_groups && sec.account_groups.length ? `<h4 class="h6 mt-3">${tr("Account ownership among people like you", "Tỷ lệ có tài khoản ở những người giống bạn")}</h4>
                ${table([tr("Group", "Nhóm"), tr("World", "Thế giới"), cname], sec.account_groups.map(g =>
                    `<tr><td>${esc(g.label)}</td><td>${pct(g.world, 0)}</td><td>${pct(g.country, 0)}</td></tr>`))}` : ""}
            <p class="small">${cite(findex.cite)}</p>
        </div>
        <div class="col-lg-6"><h3 class="h5">${tr("Food security", "An ninh lương thực")}</h3>${foodHtml}</div>
    </div>
    ${resilienceHtml()}`));

    // ---------------------------------------------------------------- financial resilience (Findex)
    function resilienceHtml() {
        const em = sec.emergency, cv = sec.cover_expenses, src = sec.emergency_source, wr = sec.worry;
        if (!em && !cv && !src && !wr) return "";
        const amount = SES.emergencyAmount(r.country.iso3);
        const dist = (x, title) => table([title, tr("World", "Thế giới"), cname], x.labels.map((label, i) =>
            `<tr class="${label === x.label ? "table-active" : ""}"><td>${esc(label)}${label === x.label ? ` &larr; ${tr("you", "bạn")}` : ""}</td>
                <td>${pct(x.world_shares[i])}</td><td>${x.country_shares ? pct(x.country_shares[i]) : "-"}</td></tr>`));
        const parts = [];
        if (em) parts.push(`<div class="col-lg-6"><h4 class="h6">${tr("Emergency money within 30 days", "Xoay tiền khẩn cấp trong 30 ngày")}</h4>
            <p class="small">${tr(`Findex asks whether people could raise one-twentieth of their country's yearly income per person${amount ? ` (about ${fixed(amount.amount, 0)} ${esc(amount.currency)} in ${cname})` : ""} within a month.
                You answered <strong>${esc(lower(em.label))}</strong>: more resilient than about <strong>${pct(em.world_pct)}</strong> of adults worldwide${em.national_pct !== undefined ? ` and ${pct(em.national_pct)} in ${cname}` : ""}.`,
                `Findex hỏi liệu mọi người có thể xoay được một phần hai mươi thu nhập bình quân đầu người một năm của nước mình${amount ? ` (khoảng ${fixed(amount.amount, 0)} ${esc(amount.currency)} ở ${cname})` : ""} trong một tháng không.
                Bạn trả lời <strong>${esc(em.label.toLowerCase())}</strong>: vững vàng hơn khoảng <strong>${pct(em.world_pct)}</strong> người trưởng thành trên thế giới${em.national_pct !== undefined ? ` và ${pct(em.national_pct)} ở ${cname}` : ""}.`)}</p>
            ${dist(em, tr("Answer", "Câu trả lời"))}</div>`);
        if (cv) parts.push(`<div class="col-lg-6"><h4 class="h6">${tr("Covering expenses after losing your main income", "Trang trải khi mất nguồn thu nhập chính")}</h4>
            <p class="small">${tr(`You could cover expenses for <strong>${esc(lower(cv.label))}</strong>: longer than about ${pct(cv.world_pct)} of adults in the ${cv.world_economies} economies where Findex asks this (mostly low- and middle-income)${cv.national_pct !== undefined ? `, and ${pct(cv.national_pct)} in ${cname}` : ""}.`,
                `Bạn có thể trang trải trong <strong>${esc(cv.label.toLowerCase())}</strong>: lâu hơn khoảng ${pct(cv.world_pct)} người trưởng thành ở ${cv.world_economies} nền kinh tế được Findex hỏi câu này (chủ yếu thu nhập thấp và trung bình)${cv.national_pct !== undefined ? `, và ${pct(cv.national_pct)} ở ${cname}` : ""}.`)}</p>
            ${dist(cv, tr("How long", "Bao lâu"))}</div>`);
        if (src) parts.push(`<div class="col-lg-6"><h4 class="h6">${tr("Main source of emergency money", "Nguồn tiền khẩn cấp chính")}</h4>
            <p class="small">${tr(`Among adults who could raise the money, ${src.world_same !== undefined ? pct(src.world_same) : "-"} worldwide would mostly rely on ${esc(lower(src.label))}${src.country_same !== undefined ? `, and ${pct(src.country_same)} in ${cname}` : ""}.`,
                `Trong số người trưởng thành có thể xoay được tiền, ${src.world_same !== undefined ? pct(src.world_same) : "-"} trên thế giới chủ yếu dựa vào ${esc(src.label.toLowerCase())}${src.country_same !== undefined ? `, và ${pct(src.country_same)} ở ${cname}` : ""}.`)}</p>
            ${dist(src, tr("Source", "Nguồn"))}</div>`);
        if (wr) parts.push(`<div class="col-lg-6"><h4 class="h6">${tr("Biggest financial worry", "Nỗi lo tài chính lớn nhất")}</h4>
            <p class="small">${wr.world_same !== undefined ? tr(`${pct(wr.world_same)} of adults in the surveyed economies who name a worry share yours${wr.country_same !== undefined ? `, and ${pct(wr.country_same)} in ${cname}` : ""}.`,
                `${pct(wr.world_same)} người trưởng thành ở các nền kinh tế được khảo sát có cùng nỗi lo với bạn${wr.country_same !== undefined ? `, và ${pct(wr.country_same)} ở ${cname}` : ""}.`)
                : tr("None of these worries you most.", "Không vấn đề nào trong số này khiến bạn lo nhất.")}</p>
            ${dist(wr, tr("Worry", "Nỗi lo"))}</div>`);
        const year = (em && em.year) || (cv && cv.year);
        return `<h3 class="h5 mt-4">${tr("Financial resilience", "Khả năng chống chịu tài chính")}</h3>
            <div class="row g-4">${parts.join("")}</div>
            <p class="small text-secondary">${tr(`Global Findex${year ? ` (${cname}: ${year})` : ""}; world shares are weighted by each economy's adult population. Emergency money counts toward your financial-security score; the other three are context.`,
                `Global Findex${year ? ` (${cname}: ${year})` : ""}; tỷ lệ thế giới được gia quyền theo dân số trưởng thành của từng nền kinh tế. Khả năng xoay tiền khẩn cấp được tính vào điểm an ninh tài chính; ba mục còn lại chỉ để tham khảo.`)} ${cite("findex_2025")}</p>`;
    }

    // ---------------------------------------------------------------- social protection
    const sp = r.social_protection;
    if (sp.received || sp.country) {
        const typeName = {
            insurance: tr("social insurance", "bảo hiểm xã hội"),
            assistance: tr("social assistance", "trợ giúp xã hội"),
            labour_market: tr("labour market programmes", "chương trình thị trường lao động"),
        };
        const fifths = [tr("Poorest fifth", "20% nghèo nhất"), tr("Second fifth", "20% thứ hai"), tr("Middle fifth", "20% ở giữa"),
                        tr("Fourth fifth", "20% thứ tư"), tr("Richest fifth", "20% giàu nhất")];
        const youText = !sp.received ? tr("You didn't answer this question.", "Bạn chưa trả lời câu này.")
            : sp.received.length === 0 ? tr("Your household receives none of these public programmes.", "Hộ bạn không nhận chương trình công nào trong số này.")
            : tr(`Your household receives ${sp.types.map(t => `<strong>${typeName[t]}</strong>`).join(" and ")}.`,
                 `Hộ bạn nhận ${sp.types.map(t => `<strong>${typeName[t]}</strong>`).join(" và ")}.`);
        const rows = sp.country ? [
            ["any", tr("Any social protection or labour programme", "Bất kỳ chương trình an sinh hoặc lao động nào")],
            ["assistance", tr("Social assistance (cash transfers, social pensions, in-kind help)", "Trợ giúp xã hội (trợ cấp tiền mặt, lương hưu xã hội, hỗ trợ hiện vật)")],
            ["insurance", tr("Social insurance (contributory pensions and benefits)", "Bảo hiểm xã hội (lương hưu và trợ cấp có đóng góp)")],
            ["labour_market", tr("Labour market programmes", "Chương trình thị trường lao động")],
        ].filter(([k]) => sp.country[k] !== undefined).map(([k, label]) => {
            const you = !sp.received ? "" : k === "any" ? (sp.received.length ? "&#10003;" : "&#10007;") : (sp.types.includes(k) ? "&#10003;" : "&#10007;");
            return `<tr><td>${label}</td><td>${pct(sp.country[k])}</td><td>${you}</td></tr>`;
        }) : [];
        html.push(section("protection", tr("Social protection", "An sinh xã hội"), `
        <p>${youText} ${tr(
            `Worldwide, ${pct(sp.ilo.covered_share * 100)} of people were covered by at least one social protection cash benefit in ${sp.ilo.year}, leaving ${people(sp.ilo.uncovered_people)} with none`,
            `Trên thế giới, ${pct(sp.ilo.covered_share * 100)} dân số được ít nhất một khoản trợ cấp an sinh xã hội bằng tiền năm ${sp.ilo.year}, còn ${people(sp.ilo.uncovered_people)} người không có gì`)} ${cite(sp.ilo.cite)}.</p>
        ${sp.country ? `<p class="small text-secondary">${tr(
            `Share of ${cname}'s population living in a household that receives each kind of programme (household survey, ${sp.year}).`,
            `Tỷ lệ dân số ${cname} sống trong hộ nhận từng loại chương trình (khảo sát hộ gia đình, ${sp.year}).`)}</p>
        ${table([tr("Programme", "Chương trình"), cname, tr("Your household", "Hộ bạn")], rows)}` : `<p class="text-secondary">${tr(`ASPIRE has no survey data on programme coverage for ${cname}.`, `ASPIRE không có số liệu khảo sát về độ bao phủ chương trình ở ${cname}.`)}</p>`}
        ${sp.world_any !== null || sp.group_any !== null || sp.region_any !== null ? `<p class="small">${[
            sp.world_any !== null ? tr(`World: ${pct(sp.world_any)} (${sp.world_year})`, `Thế giới: ${pct(sp.world_any)} (${sp.world_year})`) : "",
            sp.region_any !== null ? `${esc(sp.region_name)}: ${pct(sp.region_any)}` : "",
            sp.group_any !== null ? `${esc(sp.group_name)}: ${pct(sp.group_any)}` : "",
        ].filter(Boolean).join(" &middot; ")} ${tr("(any programme; ASPIRE aggregates cover mainly low- and middle-income economies)", "(bất kỳ chương trình nào; số liệu gộp ASPIRE chủ yếu gồm các nền kinh tế thu nhập thấp và trung bình)")}</p>` : ""}
        ${sp.quintiles ? `<h3 class="h5 mt-3">${tr(`Coverage by income fifth in ${cname}`, `Độ bao phủ theo nhóm thu nhập ở ${cname}`)}</h3>
            ${table([tr("Income fifth", "Nhóm thu nhập"), sp.quintiles.assistance ? tr("Social assistance", "Trợ giúp xã hội") : null,
                     sp.quintiles.insurance ? tr("Social insurance", "Bảo hiểm xã hội") : null].filter(h => h !== null),
                fifths.map((label, i) => `<tr class="${sp.quintile === i + 1 ? "table-active" : ""}"><td>${label}${sp.quintile === i + 1 ? ` &larr; ${tr("your income", "thu nhập của bạn")}` : ""}</td>
                    ${sp.quintiles.assistance ? `<td>${pct(sp.quintiles.assistance[i])}</td>` : ""}${sp.quintiles.insurance ? `<td>${pct(sp.quintiles.insurance[i])}</td>` : ""}</tr>`))}
            <p class="small text-secondary">${tr(
                "Fifths are ranked by welfare before transfers, so a household lifted out of the poorest fifth by its benefits still counts there. Social assistance is meant to reach the poorest; social insurance usually follows formal jobs, so it tends to rise with income.",
                "Các nhóm được xếp theo mức sống trước khi nhận trợ cấp, nên hộ thoát khỏi nhóm nghèo nhất nhờ trợ cấp vẫn được tính vào đó. Trợ giúp xã hội nhắm vào người nghèo nhất; bảo hiểm xã hội thường đi theo việc làm chính thức nên tăng theo thu nhập.")}</p>` : ""}
        <p class="small">${cite("aspire")} ${tr("Not part of your SES index: receiving support reflects both need and access.", "Không tính vào chỉ số SES: nhận hỗ trợ phản ánh cả nhu cầu lẫn khả năng tiếp cận.")}</p>`));
    }

    // ---------------------------------------------------------------- wealth
    if (r.wealth.band) {
        const w = r.wealth;
        html.push(section("wealth", tr("Wealth", "Tài sản"), `
        <p>${tr(`A net worth of ${esc(lower(w.band))} puts you between the ${pct(w.range[0])} and ${pct(w.range[1])} marks of the world's adults (midpoint ${pct(w.global_pct)}).`,
                `Tài sản ròng ${esc(w.band.toLowerCase())} đặt bạn trong khoảng từ mốc ${pct(w.range[0])} đến ${pct(w.range[1])} người trưởng thành trên thế giới (điểm giữa ${pct(w.global_pct)}).`)} ${cite("ubs_2026")}</p>
        <div class="pyramid">${w.pyramid.slice().reverse().map(b => `<div class="pyramid-row ${b.you ? "you" : ""}">
            <div class="pyramid-bar" style="width: ${Math.max(b.pct * 1.6, 4)}%">${pct(b.pct)}</div>
            <span>${esc(b.label)}${b.you ? ` &larr; ${tr("you", "bạn")}` : ""}</span></div>`).join("")}</div>`));
    }

    // ---------------------------------------------------------------- country at a glance
    const loc = r.location;
    // You and the typical person in your country: median income, median education, most common work status.
    const typicalRows = [];
    if (r.country.median_ppp) typicalRows.push([tr("Income per person per day", "Thu nhập mỗi người mỗi ngày"), money(inc.ppp_per_day), money(r.country.median_ppp),
        inc.ppp_per_day >= r.country.median_ppp ? tr(`${fixed(inc.ppp_per_day / r.country.median_ppp, 1)}&times; the median`, `gấp ${fixed(inc.ppp_per_day / r.country.median_ppp, 1)} lần trung vị`)
                                                 : tr(`${pct(100 * inc.ppp_per_day / r.country.median_ppp, 0)} of the median`, `bằng ${pct(100 * inc.ppp_per_day / r.country.median_ppp, 0)} trung vị`)]);
    if (edu.country_shares) {
        let cum = 0;
        const median = edu.country_shares.findIndex(x => (cum += x) >= 50);
        typicalRows.push([tr("Highest education (adults 25+)", "Học vấn cao nhất (từ 25 tuổi)"), esc(edu.label), esc(edu.levels[median]),
            edu.level > median ? tr("higher", "cao hơn") : edu.level === median ? tr("the same", "như nhau") : tr("lower", "thấp hơn")]);
    }
    if (work.status && work.country) {
        const names = {employee: tr("Employee", "Người làm công"), employer: tr("Employer", "Chủ sử dụng lao động"),
                       own_account: tr("Own-account worker", "Lao động tự làm"), family_worker: tr("Contributing family worker", "Lao động gia đình")};
        const common = Object.keys(names).reduce((a, b) => (work.country[b] > work.country[a] ? b : a));
        typicalRows.push([tr("Most common work status", "Vị thế việc làm phổ biến nhất"), esc(work.label.split(":")[0]),
            `${names[common]} (${pct(work.country[common], 0)})`, work.status === common ? tr("the same", "như nhau") : tr("different", "khác")]);
    }
    const typicalHtml = typicalRows.length ? `<h3 class="h5">${tr(`You and the typical person in ${cname}`, `Bạn và người điển hình ở ${cname}`)}</h3>
        ${table(["", tr("You", "Bạn"), tr(`Typical in ${cname}`, `Điển hình ở ${cname}`), ""], typicalRows.map(row => `<tr>${row.map(c => `<td>${c}</td>`).join("")}</tr>`))}
        <p class="small text-secondary">${tr("Typical means the median for income and education, and the most common category for work.",
                                             "Điển hình là trung vị đối với thu nhập và học vấn, và nhóm phổ biến nhất đối với việc làm.")}</p>` : "";
    // How reliable the national numbers are: the World Bank's statistical performance score.
    const spi = country.wdi && country.wdi["IQ.SPI.OVRL"];
    const spiAll = D.countries.map(c => c.wdi && c.wdi["IQ.SPI.OVRL"] && c.wdi["IQ.SPI.OVRL"][1]).filter(Boolean).sort((a, b) => a - b);
    const rankNote = `<p class="small text-secondary">${tr(`"Better than" is the share of the world's population living in economies that do worse on that indicator, where lower is better for mortality, pollution, inequality and similar measures. Indicators that aren't better or worse in themselves are not ranked.`,
        `"Hơn" là tỷ lệ dân số thế giới sống ở các nền kinh tế kém hơn về chỉ số đó; với tử vong, ô nhiễm, bất bình đẳng và các chỉ số tương tự thì thấp hơn là tốt hơn. Các chỉ số không mang nghĩa tốt hay xấu thì không được xếp hạng.`)}</p>`;
    const spiHtml = spi ? `<p class="small">${tr(
        `<strong>How reliable are ${cname}'s numbers?</strong> Its statistical system scores ${fixed(spi[1], 0)} out of 100 on the World Bank's Statistical Performance Indicators (${spi[0]}), against a median of ${fixed(spiAll[Math.floor(spiAll.length / 2)], 0)} across ${spiAll.length} economies. Lower scores generally mean a weaker statistical system, with fewer or older surveys, so treat national comparisons with more caution.`,
        `<strong>Số liệu của ${cname} đáng tin đến đâu?</strong> Hệ thống thống kê của nước này đạt ${fixed(spi[1], 0)}/100 theo Chỉ số Hiệu quả Thống kê của Ngân hàng Thế giới (${spi[0]}), so với trung vị ${fixed(spiAll[Math.floor(spiAll.length / 2)], 0)} của ${spiAll.length} nền kinh tế. Điểm thấp hơn thường nghĩa là hệ thống thống kê yếu hơn, với ít khảo sát hơn hoặc khảo sát cũ hơn, nên hãy thận trọng hơn với các so sánh trong nước.`)} ${cite("wdi")}</p>` : "";
    // Prices: the IMF's inflation rate for this year and the rise since 2021.
    const pr = country.prices;
    const lastYear = pr && Math.max(...Object.keys(pr.price_index).map(Number));
    const priceHtml = pr && pr.current_inflation !== undefined ? `<p class="small">${tr(
        `<strong>Prices:</strong> consumer prices in ${cname} are rising about ${pct(pr.current_inflation * 100)} a year (IMF, ${lastYear}) and are ${pct((pr.price_index[lastYear] - 1) * 100, 0)} higher than in 2021. An income that doesn't grow loses about ${pct(100 * (1 - 1 / (1 + pr.current_inflation)))} of its buying power a year.`,
        `<strong>Giá cả:</strong> giá tiêu dùng ở ${cname} đang tăng khoảng ${pct(pr.current_inflation * 100)} mỗi năm (IMF, ${lastYear}) và cao hơn ${pct((pr.price_index[lastYear] - 1) * 100, 0)} so với năm 2021. Một khoản thu nhập không tăng sẽ mất khoảng ${pct(100 * (1 - 1 / (1 + pr.current_inflation)))} sức mua mỗi năm.`)} ${cite("imf_weo")}</p>` : "";
    html.push(section("country", tr(`${cname} at a glance`, `Tổng quan về ${cname}`), `
    ${typicalHtml}
    ${spiHtml}
    ${priceHtml}
    <p>${loc.income_group ? tr(`The World Bank classifies ${cname} as <strong>${esc(lower(loc.income_group))}</strong>. `,
                               `Ngân hàng Thế giới xếp ${cname} vào nhóm <strong>${esc(loc.income_group.toLowerCase())}</strong>. `) : ""}
        ${loc.gdp_per_capita_usd !== undefined ? tr(`GDP per person was ${money(loc.gdp_per_capita_usd, 0)} in ${loc.gdp_year} (market exchange rates); ${pct(loc.share_in_poorer_countries_pct)} of the world lives in countries with a lower GDP per person.`,
                                                    `GDP bình quân đầu người là ${money(loc.gdp_per_capita_usd, 0)} năm ${loc.gdp_year} (theo tỷ giá thị trường); ${pct(loc.share_in_poorer_countries_pct)} dân số thế giới sống ở các nước có GDP bình quân thấp hơn.`) : ""}
        ${loc.median ? tr(`Half of ${cname}'s people live on less than ${money(loc.median)} a day.`, `Một nửa dân số ${cname} sống bằng dưới ${money(loc.median)} mỗi ngày.`) : ""}</p>
    ${loc.poverty ? table([tr("Poverty line", "Chuẩn nghèo"), `${cname}, ${refYear}`, tr("World", "Thế giới")], loc.poverty.map((pv, i) =>
        `<tr><td>${money(pv.line)} ${tr("a day", "mỗi ngày")}</td><td>${pct(pv.pct)}</td><td>${pct(inc.lines[i].share_below)}</td></tr>`)) : ""}
    ${table([tr("Indicator", "Chỉ số"), cname, loc.region_name ? esc(loc.region_name) : null, tr("World", "Thế giới"),
             `<abbr title="${tr("Share of the world's population living in economies that do worse on this indicator", "Tỷ lệ dân số thế giới sống ở các nền kinh tế kém hơn về chỉ số này")}">${tr("Better than", "Hơn")}</abbr>`].filter(x => x !== null), (() => {
        // Group the indicators so the long table scans easily.
        const groups = [
            [tr("Economy and inequality", "Kinh tế và bất bình đẳng"), /^(NY\.|SI\.|GD_WBL)/],
            [tr("Work", "Việc làm"), /^SL\./],
            [tr("Health", "Sức khỏe"), /^(SP\.DYN|SH\.|SN\.)/],
            [tr("Education and skills", "Giáo dục và kỹ năng"), /^(SE\.|HD\.)/],
            [tr("Living conditions and safety", "Điều kiện sống và an toàn"), /./],
        ];
        const cols = loc.region_name ? 5 : 4;
        const used = new Set();
        return groups.flatMap(([title, re]) => {
            const rows = loc.glance.filter(g => !used.has(g.code) && re.test(g.code));
            rows.forEach(g => used.add(g.code));
            if (!rows.length) return [];
            return [`<tr class="glance-group"><th colspan="${cols}">${title}</th></tr>`].concat(rows.map(g =>
                `<tr><td>${esc(g.label)} <span class="small text-secondary">(${g.year})</span></td><td>${fmtGlance(g.value, g.fmt)}</td>
                ${loc.region_name ? `<td>${fmtGlance(g.region, g.fmt)}</td>` : ""}<td>${fmtGlance(g.world, g.fmt)}</td>
                <td>${g.better_than_pct === null ? "" : pct(g.better_than_pct, 0)}</td></tr>`));
        });
    })())}
    ${rankNote}
    <p class="small text-secondary">${tr("World Development Indicators", "Bộ chỉ số Phát triển Thế giới")} ${cite("wdi")}. ${tr(
        `GDP per person isn't part of your SES index: your income is already adjusted for prices in ${cname} and compared globally, so counting the country again would double-count it.`,
        `GDP bình quân đầu người không nằm trong chỉ số SES: thu nhập của bạn đã được điều chỉnh theo giá cả ở ${cname} và so sánh toàn cầu, nên tính thêm quốc gia sẽ là tính trùng.`)}</p>`));

    // Data freshness: when the data were built and from which main releases.
    const pipVersion = String(D.global.income.pip_version || "");
    const pipDate = pipVersion.length >= 8 ? new Date(Date.UTC(+pipVersion.slice(0, 4), +pipVersion.slice(4, 6) - 1, 1)) : null;
    const monthYear = d => d.toLocaleDateString(locale, {month: "long", year: "numeric", timeZone: "UTC"});
    html.push(`<p class="small text-secondary text-center mt-5 mb-0">${tr(
        `Data as of ${esc(D.global.built)}: World Bank PIP${pipDate ? ` (${monthYear(pipDate)} release)` : ""}, ${esc(D.global.prices.source)}, World Development Indicators and the other sources listed on the <a href="${assetBase}sources.html">sources page</a>. A monthly job checks for newer releases.`,
        `Số liệu tính đến ${esc(D.global.built)}: PIP của Ngân hàng Thế giới${pipDate ? ` (bản ${monthYear(pipDate)})` : ""}, ${esc(D.global.prices.source)}, Bộ chỉ số Phát triển Thế giới và các nguồn khác trong <a href="${assetBase}sources.html">trang nguồn</a> (tiếng Anh). Một tác vụ hằng tháng kiểm tra các bản số liệu mới hơn.`)}</p>`);
    html.push(`<hr class="my-5"><div class="text-center d-flex flex-wrap gap-2 justify-content-center">
        <a class="btn btn-light" href="${base}quiz.html" id="edit-answers">${tr("Change my answers", "Sửa câu trả lời")}</a>
        <a class="btn btn-outline-light" href="${base}methodology.html">${tr("How this was calculated", "Cách tính")}</a>
    </div></div>`);
    root.innerHTML = html.join("\n");
    html.length = 0;

    // "Change my answers" opens the quiz with these answers filled in (saved only in this browser).
    root.querySelectorAll("#edit-answers, .prefill-quiz").forEach(link => link.addEventListener("click", () => {
        try { localStorage.setItem("socialranking-quiz-v1", JSON.stringify({answers: form, step: 0, furthest: 99})); } catch (e) { /* no storage */ }
    }));

    // Compare with another results link: score its answers here and show both side by side.
    document.getElementById("compare-go").addEventListener("click", () => {
        const out = document.getElementById("compare-out");
        const text = document.getElementById("compare-url").value.trim();
        const hash = text.includes("#") ? text.slice(text.indexOf("#") + 1) : text;
        let other;
        try {
            other = SES.score(SES.parseAnswers(Object.fromEntries(new URLSearchParams(hash))));
        } catch (e) {
            out.innerHTML = `<p class="text-warning small">${tr("That doesn't look like a complete results link. Copy it from the results page's address bar or its \"Copy a link\" button.",
                                                               "Đường dẫn này có vẻ không phải là một đường dẫn kết quả đầy đủ. Hãy sao chép từ thanh địa chỉ của trang kết quả hoặc nút \"Sao chép đường dẫn\".")}</p>`;
            return;
        }
        const theirs = Object.fromEntries(other.dimensions.map(d => [d.key, d]));
        const keys = [...new Set([...r.dimensions.map(d => d.key), ...other.dimensions.map(d => d.key)])];
        const label = k => (r.dimensions.find(d => d.key === k) || theirs[k]).label;
        const mine = Object.fromEntries(r.dimensions.map(d => [d.key, d]));
        const diff = (a, b) => (a === undefined || b === undefined ? "" : `${a - b > 0 ? "+" : ""}${fixed(a - b, 1)}`);
        const rows = [
            [tr("Country", "Quốc gia"), cname, esc(other.country.name), ""],
            [tr("Income per person per day (2021 int. $)", "Thu nhập mỗi người mỗi ngày (đô la quốc tế 2021)"), money(inc.ppp_per_day), money(other.income.ppp_per_day), ""],
            ...keys.map(k => [esc(label(k)), mine[k] ? pct(mine[k].pct) : "-", theirs[k] ? pct(theirs[k].pct) : "-", diff(mine[k] && mine[k].pct, theirs[k] && theirs[k].pct)]),
            [`<strong>${tr("SES index", "Chỉ số SES")}</strong>`, `<strong>${fixed(r.ses_index, 1)}</strong>`, `<strong>${fixed(other.ses_index, 1)}</strong>`, diff(r.ses_index, other.ses_index)],
        ];
        out.innerHTML = table(["", tr("You (this page)", "Bạn (trang này)"), tr("The other link", "Đường dẫn kia"), tr("Difference", "Chênh lệch")],
            rows.map(row => `<tr>${row.map(c => `<td>${c}</td>`).join("")}</tr>`))
            + `<p class="small text-secondary">${tr("World percentiles; dimensions only one of you answered show a dash.", "Bách phân vị thế giới; khía cạnh chỉ một người trả lời được hiển thị bằng dấu gạch.")}</p>`;
    });

    // Highlight the section being read in the section bar, and offer a way back to the top.
    const navLinks = Array.from(root.querySelectorAll(".result-nav a"));
    const navBar = root.querySelector(".result-nav .container");
    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(entries => {
            for (const entry of entries) {
                if (!entry.isIntersecting) continue;
                navLinks.forEach(a => {
                    const on = a.getAttribute("href") === `#${entry.target.id}`;
                    a.classList.toggle("active", on);
                    if (on && navBar) navBar.scrollTo({left: a.offsetLeft - navBar.clientWidth / 2 + a.clientWidth / 2, behavior: "smooth"});
                });
            }
        }, {rootMargin: "-130px 0px -65% 0px"});
        navLinks.forEach(a => { const t = document.getElementById(a.getAttribute("href").slice(1)); if (t) observer.observe(t); });
    }
    const toTop = document.createElement("button");
    toTop.type = "button";
    toTop.className = "btn btn-light to-top";
    toTop.hidden = true;
    toTop.setAttribute("aria-label", tr("Back to top", "Lên đầu trang"));
    toTop.innerHTML = "&uarr;";
    toTop.addEventListener("click", () => window.scrollTo({top: 0, behavior: "smooth"}));
    document.body.appendChild(toTop);
    window.addEventListener("scroll", () => { toTop.hidden = window.scrollY < 900; }, {passive: true});

    root.addEventListener("click", e => {
        const link = e.target.closest('a[href^="#"]');
        if (!link) return;
        const target = document.getElementById(link.getAttribute("href").slice(1));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({behavior: "smooth", block: "start"});
        }
    });

    // ---------------------------------------------------------------- what-if simulator
    const slider = document.getElementById("whatif");
    const whatifOut = document.getElementById("whatif-out");
    function updateWhatif() {
        const mult = Math.pow(2, Number(slider.value));
        const x = inc.ppp_per_day * mult;
        const rank = SES.rankIncome(country, x);
        whatifOut.innerHTML = `<span>${tr("Income", "Thu nhập")} &times;${fixed(mult, mult < 1 ? 2 : 1)}: <strong>${money(x)}</strong> ${tr("a day", "mỗi ngày")}</span>
            <span>${tr("World", "Thế giới")}: <strong>${pct(rank.global_pct)}</strong></span>
            ${rank.national_pct !== null ? `<span>${cname}: <strong>${pct(rank.national_pct)}</strong></span>` : ""}`;
    }
    slider.addEventListener("input", updateWhatif);
    const elsewhere = document.getElementById("elsewhere");
    const updateElsewhere = () => {
        const size = inc.mode === "exact" ? answers.household_size : 1;
        const period = inc.mode === "exact" ? answers.income_period : "month";
        const e = SES.equivalentIncome(elsewhere.value, inc.ppp_per_day, size, period);
        document.getElementById("elsewhere-out").innerHTML = e ? tr(
            `<strong>${fixed(e.amount, 0)} ${esc(e.currency || "")}</strong> ${period === "year" ? "a year" : "a month"}${e.national_pct !== null ? `, richer than <strong>${pct(e.national_pct)}</strong> of people in ${esc(e.name)}` : ""}.`,
            `<strong>${fixed(e.amount, 0)} ${esc(e.currency || "")}</strong> ${period === "year" ? "mỗi năm" : "mỗi tháng"}${e.national_pct !== null ? `, khá giả hơn <strong>${pct(e.national_pct)}</strong> dân số ${esc(e.name)}` : ""}.`) : "";
    };
    elsewhere.addEventListener("change", updateElsewhere);
    updateElsewhere();
    updateWhatif();

    // ---------------------------------------------------------------- copy link / image
    const copyButton = document.getElementById("copy-link");
    // Phones and tablets get the system share sheet; elsewhere the link is copied.
    const canShare = navigator.share && window.matchMedia("(pointer: coarse)").matches;
    if (canShare) copyButton.textContent = tr("Share these results", "Chia sẻ kết quả");
    copyButton.addEventListener("click", () => {
        const status = document.getElementById("copy-status");
        if (canShare) {
            navigator.share({title: document.title, text: tr(`I'm richer than ${pct(inc.global_pct)} of the world. Where do you stand?`,
                                                             `Tôi khá giả hơn ${pct(inc.global_pct)} dân số thế giới. Còn bạn thì sao?`), url: shareUrl})
                .catch(() => {});
            return;
        }
        navigator.clipboard.writeText(shareUrl)
            .then(() => { status.textContent = tr("Link copied. It contains your answers.", "Đã sao chép. Đường dẫn chứa câu trả lời của bạn."); })
            .catch(() => { status.textContent = tr("Copy the address from your browser's address bar.", "Hãy sao chép địa chỉ trên thanh địa chỉ của trình duyệt."); });
    });
    document.getElementById("save-image").addEventListener("click", () => {
        const c = document.createElement("canvas");
        const W = 1200, H = 630;
        c.width = W; c.height = H;
        const g = c.getContext("2d");
        const grad = g.createLinearGradient(0, 0, 0, H);
        grad.addColorStop(0, "#0b1d33"); grad.addColorStop(1, "#000000");
        g.fillStyle = grad; g.fillRect(0, 0, W, H);
        g.fillStyle = "#9fb4c9"; g.font = "28px system-ui, sans-serif";
        g.fillText(tr("Where I stand in the world", "Tôi đứng ở đâu trên thế giới"), 60, 80);
        g.fillStyle = "#ffffff"; g.font = "bold 64px system-ui, sans-serif";
        g.fillText(tr(`Richer than ${pct(inc.global_pct)} of people`, `Khá giả hơn ${pct(inc.global_pct)} dân số`), 60, 165);
        g.font = "30px system-ui, sans-serif"; g.fillStyle = "#cbd5e1";
        g.fillText(`${inc.national_pct !== undefined ? tr(`${r.country.name}: richer than ${pct(inc.national_pct)} · `, `${r.country.name}: khá giả hơn ${pct(inc.national_pct)} · `) : ""}${tr("SES index", "Chỉ số SES")} ${fixed(r.ses_index, 1)}/100`, 60, 220);
        const step = Math.min(52, (H - 340) / r.dimensions.length);
        r.dimensions.forEach((d, i) => {
            const y = 270 + i * step;
            g.fillStyle = "#e2e8f0"; g.font = "26px system-ui, sans-serif";
            g.fillText(d.label, 60, y + 22);
            g.fillStyle = "rgba(255,255,255,0.12)"; g.fillRect(360, y, 660, 26);
            g.fillStyle = "#7dd3fc"; g.fillRect(360, y, 6.6 * d.pct, 26);
            g.fillStyle = "#ffffff"; g.fillText(pct(d.pct), 1040, y + 22);
        });
        g.fillStyle = "#64748b"; g.font = "20px system-ui, sans-serif";
        g.fillText("World Bank PIP & WDI, IMF, UNESCO, ILO, FAO, Gallup, UBS · acosmiccake.github.io/socialranking", 60, H - 30);
        const a = document.createElement("a");
        a.download = tr("where-i-stand.png", "vi-tri-cua-toi.png");
        a.href = c.toDataURL("image/png");
        a.click();
    });

    // ---------------------------------------------------------------- data downloads
    function download(name, type, text) {
        const a = document.createElement("a");
        a.download = name;
        a.href = URL.createObjectURL(new Blob([text], {type}));
        a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    }
    // One row per measure: section, measure, your value, world, your country. Percentiles are the
    // share of people below you (people level with you count as half).
    function summaryRows() {
        const rows = [["section", "measure", "you", "world", "country"]];
        const add = (section, measure, you, world = "", country = "") => {
            if (you !== undefined && you !== null) rows.push([section, measure, you, world ?? "", country ?? ""]);
        };
        add("summary", "SES index (0-100)", r.ses_index);
        for (const d of r.dimensions) add("summary", `${d.key} percentile`, "", d.pct, d.national_pct);
        add("income", "income per person per day (2021 int. $)", inc.ppp_per_day.toFixed(2), inc.world_median, r.country.median_ppp);
        add("income", "percentile", "", inc.global_pct, inc.national_pct);
        if (inc.sensitivity) {
            add("income", "percentile at -20% income", "", inc.sensitivity.global[0], inc.sensitivity.national && inc.sensitivity.national[0]);
            add("income", "percentile at +20% income", "", inc.sensitivity.global[1], inc.sensitivity.national && inc.sensitivity.national[1]);
        }
        for (const t of inc.thresholds) add("income", `${t.scope} ${t.pct}th percentile (2021 int. $/day)`, t.ppp_per_day.toFixed(2));
        for (const l of inc.lines) add("income", `share below $${l.line.toFixed(2)}/day`, l.above ? "above" : "below", l.share_below, l.country_share_below);
        if (inc.healthy_diet.cost_2021ppp !== undefined) {
            add("income", "healthy diet cost (2021 int. $/day)", inc.healthy_diet.cost_2021ppp.toFixed(2));
            add("income", "healthy diet affordable (world, country: % who can't afford)", inc.healthy_diet.affordable ? "yes" : "no",
                inc.healthy_diet.world && Math.round(inc.healthy_diet.world.unaffordable_share * 1000) / 10, inc.healthy_diet.unaffordable_pct);
        }
        add("education", edu.label, "", edu.global_pct, edu.national_pct);
        if (r.mobility.rank_change !== undefined) add("education", "rank change vs better-ranked parent (points)", r.mobility.rank_change);
        if (work.status) add("work", `status: ${work.status}`, "", work.status_pct ?? work.global_pct, work.status_national_pct ?? work.national_pct);
        if (work.occupation) add("work", `occupation: ${work.occupation.key} (skill level ${work.occupation.skill_level ?? "-"})`, "", work.occupation.world_pct, work.occupation.national_pct);
        if (liv.global_pct !== undefined) add("living", "living standards", "", liv.global_pct, liv.national_pct);
        if (r.mpi.available) add("living", "MPI deprivation score (%)", r.mpi.score);
        if (sec.gallup_group) add("security", `Gallup vulnerability: ${sec.gallup_group}`, "", sec.gallup_pct);
        if (sec.fies_level) add("security", `FIES: ${sec.fies_level} (${sec.fies_raw}/8)`, "", sec.fies_pct, sec.fies_national_pct);
        if (sec.emergency) add("security", `emergency money: ${sec.emergency.key}`, "", sec.emergency.world_pct, sec.emergency.national_pct);
        if (sec.cover_expenses) add("security", `cover expenses: ${sec.cover_expenses.key}`, "", sec.cover_expenses.world_pct, sec.cover_expenses.national_pct);
        if (r.wealth.band) add("wealth", r.wealth.band, "", r.wealth.global_pct);
        const sp = r.social_protection;
        if (sp.received) add("social protection", "programme types received", sp.types.join(" + ") || "none", sp.world_any, sp.country && sp.country.any);
        return rows;
    }
    const csvCell = v => { const t = String(v); return /[",\n]/.test(t) ? `"${t.replace(/"/g, '""')}"` : t; };
    document.getElementById("save-csv").addEventListener("click", () => {
        download(tr("where-i-stand.csv", "vi-tri-cua-toi.csv"), "text/csv;charset=utf-8",
                 "\ufeff" + summaryRows().map(row => row.map(csvCell).join(",")).join("\r\n"));
    });
    document.getElementById("print-page").addEventListener("click", () => {
        // Open collapsed details so they print too.
        root.querySelectorAll("details").forEach(d => { d.open = true; });
        window.print();
    });
    document.getElementById("save-json").addEventListener("click", () => {
        const payload = {generated: new Date().toISOString(), data_built: D.global.built, answers, results: r};
        download(tr("where-i-stand.json", "vi-tri-cua-toi.json"), "application/json", JSON.stringify(payload, null, 1));
    });

    // ---------------------------------------------------------------- charts
    if (typeof Chart !== "undefined") {
        const d = inc.chart;
        const toPoints = ys => d.x.map((x, i) => ({x, y: ys[i]}));
        const datasets = [{
            label: tr("World", "Thế giới"), data: toPoints(d.world), borderColor: "#7dd3fc",
            backgroundColor: "rgba(125, 211, 252, 0.15)", fill: true, pointRadius: 0, tension: 0.2,
        }];
        if (d.country) {
            datasets.push({label: r.country.name, data: toPoints(d.country), borderColor: "#fbbf24", pointRadius: 0, borderDash: [6, 4], tension: 0.2});
        }
        datasets.push({
            label: tr("You", "Bạn"), type: "scatter", pointRadius: 7, pointBackgroundColor: "#ffffff", pointBorderColor: "#000000",
            data: [{x: d.you, y: d.you_world}].concat(d.you_country !== null ? [{x: d.you, y: d.you_country}] : []),
        });
        const axis = text => ({display: true, text, color: "#ccc"});
        const grid = {color: "rgba(255,255,255,0.08)"};
        new Chart(document.getElementById("incomeChart"), {
            type: "line",
            data: {datasets},
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    x: {type: "logarithmic", min: 0.5, max: 1000, title: axis(tr("Income per person per day (2021 int. $)", "Thu nhập mỗi người mỗi ngày (đô la quốc tế 2021)")), grid,
                        ticks: {color: "#ccc", callback: v => [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000].includes(v) ? `$${v}` : ""}},
                    y: {min: 0, max: 100, title: axis(tr("% of people living on less", "% số người sống bằng ít hơn")), grid, ticks: {color: "#ccc", callback: v => `${v}%`}},
                },
                plugins: {
                    legend: {labels: {color: "#eee"}},
                    tooltip: {callbacks: {label: c => tr(`${c.dataset.label}: ${fixed(c.parsed.y, 1)}% live on less than $${fixed(c.parsed.x, 2)}/day`,
                                                         `${c.dataset.label}: ${fixed(c.parsed.y, 1)}% sống bằng dưới $${fixed(c.parsed.x, 2)}/ngày`)}},
                },
            },
        });
        const nh = inc.national_history;
        if (nh) {
            new Chart(document.getElementById("countryHistoryChart"), {
                data: {
                    labels: nh.years,
                    datasets: [
                        {type: "line", label: tr(`${r.country.name} median ($/day)`, `Trung vị ${r.country.name} ($/ngày)`), data: nh.median,
                         borderColor: "#fbbf24", pointRadius: 0, yAxisID: "y"},
                        {type: "line", label: tr("You ($/day)", "Bạn ($/ngày)"), data: nh.years.map(() => Math.round(inc.ppp_per_day * 100) / 100),
                         borderColor: "#ffffff", borderDash: [4, 4], pointRadius: 0, yAxisID: "y"},
                        {type: "bar", label: tr("Below $3.00 a day (%)", "Dưới 3,00 đô la/ngày (%)"), data: nh.below_3,
                         backgroundColor: "rgba(248, 113, 113, 0.35)", yAxisID: "y2"},
                    ],
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: {
                        y: {type: "logarithmic", position: "left", grid, ticks: {color: "#ccc", callback: v => [1, 2, 5, 10, 20, 50, 100].includes(v) ? `$${v}` : ""}},
                        y2: {min: 0, max: 100, position: "right", grid: {display: false}, ticks: {color: "#f87171", callback: v => `${v}%`}},
                        x: {ticks: {color: "#ccc", maxTicksLimit: 12}, grid},
                    },
                    plugins: {legend: {labels: {color: "#eee"}}},
                },
            });
        }
        new Chart(document.getElementById("historyChart"), {
            type: "bar",
            data: {
                labels: inc.history.map(h => h.estimate_type === "nowcast" ? `${h.year} (${tr("nowcast", "ước tính")})` : String(h.year)),
                datasets: [{label: tr("You'd be richer than", "Bạn khá giả hơn"), data: inc.history.map(h => h.pct), backgroundColor: "#7dd3fc"}],
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {y: {min: 0, max: 100, grid, ticks: {color: "#ccc", callback: v => `${v}%`}}, x: {ticks: {color: "#ccc"}, grid}},
                plugins: {legend: {display: false}, tooltip: {callbacks: {label: c => tr(`Richer than ${fixed(c.parsed.y, 1)}% of the world`, `Khá giả hơn ${fixed(c.parsed.y, 1)}% thế giới`)}}},
            },
        });
    }

    // ---------------------------------------------------------------- world map
    drawMap();

    async function drawMap() {
        const svg = document.getElementById("worldMap");
        if (!svg || typeof d3 === "undefined" || typeof topojson === "undefined") {
            if (svg) svg.closest(".map-box").hidden = true;
            return;
        }
        try {
            const res = await fetch("https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json", {
                integrity: "sha384-yOCJ+8ShBm8UDqtAVtAvxTDDf4gXo5edxl/YG0FmVC5OTmqVLl7utuVGBDEeZWHf",
            });
            const topo = await res.json();
            const features = topojson.feature(topo, topo.objects.countries).features;
            const byM49 = Object.fromEntries(every.countries.filter(c => c.m49).map(c => [c.m49, c]));
            const kosovo = every.countries.find(c => c.iso3 === "XKX");
            const lookup = f => byM49[f.id] || (f.properties.name === "Kosovo" ? kosovo : null);
            const W = 960, H = 480;
            const projection = d3.geoNaturalEarth1().fitSize([W, H], {type: "Sphere"});
            const path = d3.geoPath(projection);
            const color = d3.scaleSequential(d3.interpolateViridis).domain([0, 100]);
            const tip = document.getElementById("mapTip");
            const s = d3.select(svg).attr("viewBox", `0 0 ${W} ${H}`);
            s.append("path").attr("d", path({type: "Sphere"})).attr("fill", "#0d1b2a");
            s.selectAll("path.country").data(features).join("path")
                .attr("class", "country")
                .attr("d", path)
                .attr("fill", f => { const c = lookup(f); return c ? color(c.pct) : "#333"; })
                .attr("stroke", f => (lookup(f) || {}).iso3 === r.country.iso3 ? "#ffffff" : "#111")
                .attr("stroke-width", f => (lookup(f) || {}).iso3 === r.country.iso3 ? 1.5 : 0.3)
                .on("mousemove", (event, f) => {
                    const c = lookup(f);
                    tip.hidden = false;
                    tip.textContent = c ? tr(`${c.name}: richer than ${pct(c.pct)}`, `${c.name}: khá giả hơn ${pct(c.pct)}`)
                                        : tr(`${f.properties.name}: no data`, `${f.properties.name}: không có số liệu`);
                    const box = svg.getBoundingClientRect();
                    tip.style.left = `${event.clientX - box.left + 12}px`;
                    tip.style.top = `${event.clientY - box.top + 12}px`;
                })
                .on("mouseleave", () => { tip.hidden = true; });
            document.querySelector(".map-scale").style.background =
                `linear-gradient(90deg, ${[0, 25, 50, 75, 100].map(v => color(v)).join(",")})`;
        } catch (e) {
            svg.closest(".map-box").hidden = true;
        }
    }
})();

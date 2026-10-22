// Multi-step quiz. Validates with the same rules as the scorer (SES.parseAnswers),
// then opens the results page with the answers in the URL fragment, which
// browsers never send to the server.
(function () {
    const form = document.getElementById("quiz");
    if (!form) return;

    const steps = Array.from(form.querySelectorAll(".step"));
    const back = document.getElementById("back");
    const next = document.getElementById("next");
    const progress = document.getElementById("progress");
    const country = document.getElementById("country");
    const currencyLabel = document.getElementById("currency-label");
    const localCurrency = currencyLabel.textContent;
    const unavailable = document.getElementById("exact-unavailable");
    const summary = document.getElementById("error-summary");
    const chips = document.getElementById("step-chips");
    const stepLabel = document.getElementById("step-label");
    const answeredLabel = document.getElementById("answered-label");
    const timeLeft = document.getElementById("time-left");
    const resultsNow = document.getElementById("results-now");
    const nextLabel = document.getElementById("next-label");
    const titles = steps.map(s => s.querySelector("legend").textContent.replace(/^\d+\.\s*/, ""));
    const fill = (el, values) => el.dataset.template.replace(/\{(\w+)\}/g, (_, k) => values[k]);
    // Answers are kept in this browser only, so a reload or a closed tab doesn't lose them.
    const STORE = "socialranking-quiz-v1";
    let current = 0, furthest = 0;

    function store(value) {
        try {
            if (value === null) localStorage.removeItem(STORE);
            else localStorage.setItem(STORE, JSON.stringify(value));
        } catch (e) { /* storage unavailable: carry on without saving */ }
    }

    function restore() {
        let saved;
        try { saved = JSON.parse(localStorage.getItem(STORE) || "null"); } catch (e) { saved = null; }
        if (!saved || !saved.answers || !Object.keys(saved.answers).length) return false;
        for (const [name, value] of Object.entries(saved.answers)) {
            const inputs = form.querySelectorAll(`[name="${CSS.escape(name)}"]`);
            const values = String(value).split(",");
            inputs.forEach(input => {
                if (input.type === "radio" || input.type === "checkbox") input.checked = values.includes(input.value);
                else input.value = value;
            });
        }
        furthest = Math.min(saved.furthest || 0, steps.length - 1);
        return saved.step || 0;
    }

    function save() {
        store({answers: answers(), step: current, furthest});
    }

    function renderChips() {
        chips.innerHTML = titles.map((t, i) => `<button type="button" class="step-chip${i === current ? " current" : ""}${i < current || i <= furthest ? " done" : ""}"
            data-step="${i}" ${i > furthest ? "disabled" : ""} ${i === current ? 'aria-current="step"' : ""}>${i + 1}. ${t}</button>`).join("");
        const active = chips.querySelector(".current");
        if (active) chips.scrollLeft = active.offsetLeft - chips.clientWidth / 2 + active.clientWidth / 2;
    }

    function updateCounts() {
        const a = answers();
        const done = Object.values(a).filter(v => v !== "").length;
        answeredLabel.textContent = fill(answeredLabel, {n: done});
        // Roughly 12 seconds per visible question still ahead.
        const ahead = steps.slice(current + 1).reduce((n, s) =>
            n + Array.from(s.querySelectorAll(".question")).filter(q => !q.hidden).length, 0);
        const minutes = Math.round(ahead * 12 / 60);
        timeLeft.textContent = " · " + (minutes >= 1 ? fill(timeLeft, {n: minutes}) : timeLeft.dataset.done);
        // Once everything required is answered, results are one click away.
        resultsNow.hidden = current === steps.length - 1 || Object.keys(validationErrors()).length > 0;
    }

    function answers() {
        const out = {};
        for (const [k, v] of new FormData(form).entries()) {
            // Checkbox groups are sent as one comma-separated value.
            out[k] = k in out ? `${out[k]},${v}` : v;
        }
        // Drop answers to questions hidden by a show_if condition.
        form.querySelectorAll("[data-show-if]").forEach(el => {
            if (el.hidden) el.querySelectorAll("[name]").forEach(i => delete out[i.name]);
        });
        return out;
    }

    function value(name) {
        return answers()[name] || "";
    }

    function updateConditional() {
        form.querySelectorAll("[data-show-if]").forEach(el => {
            const [name, expected] = el.dataset.showIf.split("=");
            const checked = form.querySelector(`input[name="${name}"]:checked`);
            el.hidden = !checked || !expected.split("|").includes(checked.value);
        });
    }

    function updateCountry() {
        const opt = country.selectedOptions[0];
        if (!opt || !opt.value) return;
        currencyLabel.textContent = opt.dataset.currency
            ? `${opt.dataset.currency} (${opt.dataset.currencyName})` : localCurrency;
        const exact = form.querySelector('input[name="income_mode"][value="exact"]');
        const band = form.querySelector('input[name="income_mode"][value="band"]');
        const hint = document.getElementById("welfare-hint");
        if (hint) {
            const welfare = opt.dataset.welfare;
            hint.hidden = !welfare;
            hint.textContent = welfare === "consumption" ? hint.dataset.consumption : hint.dataset.income;
            // Suggest the basis the country's survey uses, unless the user already chose.
            const basis = form.querySelector(`input[name="income_basis"][value="${welfare}"]`);
            if (basis && !form.querySelector('input[name="income_basis"]:checked')) basis.checked = true;
        }
        const amount = document.getElementById("emergency-amount");
        if (amount) {
            const a = SES.emergencyAmount(opt.value);
            amount.hidden = !a;
            if (a) amount.textContent = amount.dataset.template.replace("{amount}",
                `${a.amount.toLocaleString({vi: "vi-VN", es: "es-ES"}[document.documentElement.lang] || "en-US")} ${a.currency}`);
        }
        const allowed = opt.dataset.exact === "yes";
        exact.disabled = !allowed;
        unavailable.hidden = allowed;
        if (!allowed && exact.checked) band.checked = true;
        updateConditional();
    }

    function validationErrors() {
        try {
            SES.parseAnswers(answers());
            return {};
        } catch (e) {
            if (e instanceof SES.ValidationError) return e.errors;
            throw e;
        }
    }

    function showErrors(errors, onlyStep) {
        form.querySelectorAll("[data-error-for]").forEach(el => {
            const step = el.closest(".step");
            const msg = (!onlyStep || step === onlyStep) ? errors[el.dataset.errorFor] : undefined;
            el.textContent = msg || "";
            el.hidden = !msg;
            el.closest(".question").classList.toggle("needs-answer", Boolean(msg));
        });
        const first = form.querySelector(".needs-answer");
        if (first) first.scrollIntoView({behavior: "smooth", block: "center"});
        return Boolean(first);
    }

    function show(i) {
        current = Math.max(0, Math.min(i, steps.length - 1));
        furthest = Math.max(furthest, current);
        steps.forEach((s, k) => s.hidden = k !== current);
        back.disabled = current === 0;
        next.hidden = current === steps.length - 1;
        progress.style.width = `${Math.round(100 * current / (steps.length - 1))}%`;
        stepLabel.textContent = fill(stepLabel, {n: current + 1, total: steps.length});
        nextLabel.textContent = current < steps.length - 1 ? fill(nextLabel, {section: titles[current + 1]}) : "";
        renderChips();
        updateCounts();
        save();
        window.scrollTo({top: 0, behavior: "smooth"});
    }

    chips.addEventListener("click", e => {
        const chip = e.target.closest(".step-chip");
        if (!chip || chip.disabled) return;
        const target = Number(chip.dataset.step);
        // Moving forward still checks the steps in between.
        for (let k = current; k < target; k++) {
            if (showErrors(validationErrors(), steps[k])) { show(k); showErrors(validationErrors(), steps[k]); return; }
        }
        show(target);
    });
    document.getElementById("start-over").addEventListener("click", () => {
        store(null);
        form.reset();
        furthest = 0;
        document.getElementById("restored").hidden = true;
        updateCountry();
        updateConditional();
        show(0);
    });

    next.addEventListener("click", () => {
        summary.hidden = true;
        if (!showErrors(validationErrors(), steps[current])) show(current + 1);
    });
    back.addEventListener("click", () => show(current - 1));
    form.addEventListener("change", e => {
        // "None of these" excludes the other boxes in its group, and vice versa.
        const t = e.target;
        if (t.type === "checkbox" && t.checked) {
            form.querySelectorAll(`input[name="${t.name}"]`).forEach(other => {
                if (other !== t && (t.value === "none" || other.value === "none")) other.checked = false;
            });
        }
        updateConditional();
        updateCounts();
        save();
    });
    form.addEventListener("input", () => { updateCounts(); save(); });
    country.addEventListener("change", updateCountry);
    form.addEventListener("keydown", e => {
        if (e.key === "Enter" && e.target.tagName === "INPUT" && current < steps.length - 1) {
            e.preventDefault();
            next.click();
        }
    });
    form.addEventListener("submit", e => {
        e.preventDefault();
        const errors = validationErrors();
        if (Object.keys(errors).length) {
            const firstStep = steps.find(s => Object.keys(errors).some(id => s.querySelector(`[data-error-for="${id}"]`)));
            show(steps.indexOf(firstStep));
            summary.hidden = false;
            showErrors(errors, firstStep);
            return;
        }
        const params = new URLSearchParams(answers());
        window.location.href = `${form.getAttribute("action")}#${params.toString()}`;
    });

    // Country search: filter the list as you type, and suggest the country of the browser's locale.
    const filter = document.getElementById("country-filter");
    const allOptions = Array.from(country.options).slice(1);
    const norm = t => t.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    filter.addEventListener("input", () => {
        const q = norm(filter.value.trim());
        allOptions.forEach(o => { o.hidden = Boolean(q) && !norm(o.textContent).includes(q) && o.value.toLowerCase() !== q; });
        const matches = allOptions.filter(o => !o.hidden);
        if (matches.length === 1 && country.value !== matches[0].value) {
            country.value = matches[0].value;
            country.dispatchEvent(new Event("change", {bubbles: true}));
        }
    });
    const suggest = document.getElementById("country-suggest");
    const region = (navigator.languages || [navigator.language || ""]).map(l => (l.split("-")[1] || "").toUpperCase()).find(Boolean);
    const guess = region && allOptions.find(o => o.dataset.iso2 === region);
    function updateSuggest() {
        suggest.hidden = !guess || country.value === guess.value;
        if (guess) suggest.textContent = suggest.dataset.template.replace("{country}", guess.textContent);
    }
    suggest.addEventListener("click", () => {
        country.value = guess.value;
        country.dispatchEvent(new Event("change", {bubbles: true}));
    });
    country.addEventListener("change", updateSuggest);

    const resumeAt = restore();
    if (resumeAt !== false) document.getElementById("restored").hidden = false;
    updateCountry();
    updateConditional();
    updateSuggest();
    show(resumeAt || 0);
})();

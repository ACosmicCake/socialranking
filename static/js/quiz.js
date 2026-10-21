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
    let current = 0;

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
                `${a.amount.toLocaleString(document.documentElement.lang === "vi" ? "vi-VN" : "en-US")} ${a.currency}`);
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
        steps.forEach((s, k) => s.hidden = k !== current);
        back.disabled = current === 0;
        next.hidden = current === steps.length - 1;
        progress.style.width = `${Math.round(100 * current / (steps.length - 1))}%`;
        window.scrollTo({top: 0, behavior: "smooth"});
    }

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
    });
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

    updateCountry();
    updateConditional();
    show(0);
})();

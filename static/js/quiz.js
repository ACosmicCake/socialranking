// Multi-step quiz. Without JavaScript every section is shown on one page.
(function () {
    const form = document.getElementById("quiz");
    if (!form) return;
    document.documentElement.classList.add("js");

    const steps = Array.from(form.querySelectorAll(".step"));
    const back = document.getElementById("back");
    const next = document.getElementById("next");
    const progress = document.getElementById("progress");
    const country = document.getElementById("country");
    const currencyLabel = document.getElementById("currency-label");
    const unavailable = document.getElementById("exact-unavailable");
    let current = 0;

    function value(name) {
        const checked = form.querySelector(`input[name="${name}"]:checked`);
        if (checked) return checked.value;
        const field = form.elements[name];
        return field && field.value !== undefined ? field.value : "";
    }

    function updateConditional() {
        form.querySelectorAll("[data-show-if]").forEach(el => {
            const [name, expected] = el.dataset.showIf.split("=");
            el.hidden = value(name) !== expected;
        });
    }

    function updateCountry() {
        const opt = country.selectedOptions[0];
        if (!opt || !opt.value) return;
        currencyLabel.textContent = opt.dataset.currency
            ? `${opt.dataset.currency} (${opt.dataset.currencyName})` : "local currency";
        const exact = form.querySelector('input[name="income_mode"][value="exact"]');
        const band = form.querySelector('input[name="income_mode"][value="band"]');
        const allowed = opt.dataset.exact === "yes";
        exact.disabled = !allowed;
        unavailable.hidden = allowed;
        if (!allowed && exact.checked) band.checked = true;
        updateConditional();
    }

    // Only the essentials are required; everything else can be skipped.
    function stepErrors(step) {
        const missing = [];
        const need = (name, ok) => { if (!ok) missing.push(name); };
        if (step.querySelector("#country")) need("country", value("country"));
        if (step.querySelector('[name="income_mode"]')) {
            const mode = value("income_mode");
            need("income_mode", mode);
            if (mode === "exact") {
                const amount = Number(value("income_amount").replace(/[,\s_]/g, ""));
                need("income_amount", value("income_amount").trim() !== "" && amount >= 0);
                need("income_period", value("income_period"));
                const size = Number(value("household_size"));
                need("household_size", Number.isInteger(size) && size >= 1 && size <= 50);
            } else if (mode === "band") {
                need("income_band", value("income_band"));
            }
        }
        if (step.querySelector('[name="education"]')) need("education", value("education"));
        return missing;
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
        const missing = stepErrors(steps[current]);
        form.querySelectorAll(".needs-answer").forEach(el => el.classList.remove("needs-answer"));
        if (missing.length) {
            missing.forEach(name => {
                const q = document.getElementById(`q-${name}`);
                if (q) q.classList.add("needs-answer");
            });
            const first = document.getElementById(`q-${missing[0]}`);
            if (first) first.scrollIntoView({behavior: "smooth", block: "center"});
            return;
        }
        show(current + 1);
    });
    back.addEventListener("click", () => show(current - 1));
    form.addEventListener("change", updateConditional);
    country.addEventListener("change", updateCountry);
    form.addEventListener("keydown", e => {
        if (e.key === "Enter" && e.target.tagName === "INPUT" && current < steps.length - 1) {
            e.preventDefault();
            next.click();
        }
    });

    updateCountry();
    updateConditional();
    // After a server-side validation error, open the first step with a problem.
    const firstError = form.querySelector(".is-invalid, .invalid-feedback");
    show(firstError ? steps.indexOf(firstError.closest(".step")) : 0);
})();

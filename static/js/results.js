// Draws the cumulative income distribution with the user's position.
(function () {
    const el = document.getElementById("chart-data");
    const canvas = document.getElementById("incomeChart");
    if (!el || !canvas || typeof Chart === "undefined") return;
    const d = JSON.parse(el.textContent);
    const toPoints = ys => d.x.map((x, i) => ({x, y: ys[i]}));
    const datasets = [{
        label: "World",
        data: toPoints(d.world),
        borderColor: "#7dd3fc",
        backgroundColor: "rgba(125, 211, 252, 0.15)",
        fill: true,
        pointRadius: 0,
        tension: 0.2,
    }];
    if (d.country) {
        datasets.push({
            label: "Your country",
            data: toPoints(d.country),
            borderColor: "#fbbf24",
            pointRadius: 0,
            borderDash: [6, 4],
            tension: 0.2,
        });
    }
    datasets.push({
        label: "You",
        data: [{x: d.you, y: d.you_world}].concat(d.you_country !== null ? [{x: d.you, y: d.you_country}] : []),
        type: "scatter",
        pointRadius: 7,
        pointBackgroundColor: "#ffffff",
        pointBorderColor: "#000000",
    });
    new Chart(canvas, {
        type: "line",
        data: {datasets},
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: "logarithmic",
                    min: 0.5, max: 1000,
                    title: {display: true, text: "Income per person per day (2017 int. $)", color: "#ccc"},
                    ticks: {color: "#ccc", callback: v => [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000].includes(v) ? `$${v}` : ""},
                    grid: {color: "rgba(255,255,255,0.08)"},
                },
                y: {
                    min: 0, max: 100,
                    title: {display: true, text: "% of people living on less", color: "#ccc"},
                    ticks: {color: "#ccc", callback: v => `${v}%`},
                    grid: {color: "rgba(255,255,255,0.08)"},
                },
            },
            plugins: {
                legend: {labels: {color: "#eee"}},
                tooltip: {callbacks: {label: c => `${c.dataset.label}: ${c.parsed.y.toFixed(1)}% live on less than $${c.parsed.x.toFixed(2)}/day`}},
            },
        },
    });
})();

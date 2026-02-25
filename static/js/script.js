let allPokemon = [];
const p1Select = document.getElementById('p1-select');
const p2Select = document.getElementById('p2-select');
const startBtn = document.getElementById('start-btn');
const randomBtn = document.getElementById('random-btn');
const logEl = document.getElementById('log');

const TYPE_COLORS = {
    "fire": "#ff3c00", "water": "#00bfff", "grass": "#38ff7a", "electric": "#ffd900",
    "psychic": "#ff00cc", "ghost": "#8a2be2", "dragon": "#6a5acd", "dark": "#4b0082",
    "fairy": "#ff9edb", "steel": "#9aa0a6", "fighting": "#ff4500", "poison": "#a020f0",
    "ground": "#c19a6b", "rock": "#b8860b", "ice": "#7fffd4", "bug": "#7fff00",
    "flying": "#87cefa", "normal": "#aaaaaa"
};

let dynamicStyleEl = null;

// Initialization
async function init() {
    const res = await fetch('/api/pokemon');
    allPokemon = await res.json();

    populateSelect(p1Select, "Pikachu");
    populateSelect(p2Select, "Charizard");

    updateUI();

    p1Select.addEventListener('change', updateUI);
    p2Select.addEventListener('change', updateUI);
    startBtn.addEventListener('click', startBattle);
    randomBtn.addEventListener('click', randomBattle);

    await fetchLeaderboard();
}

async function randomBattle() {
    if (allPokemon.length === 0) return;
    randomBtn.disabled = true;
    startBtn.disabled = true;
    const p1 = allPokemon[Math.floor(Math.random() * allPokemon.length)];
    const p2 = allPokemon[Math.floor(Math.random() * allPokemon.length)];
    p1Select.value = p1.name;
    p2Select.value = p2.name;
    await updateUI();

    // Slight artificial delay before auto-starting
    setTimeout(startBattle, 500);
}

function populateSelect(select, defaultVal) {
    allPokemon.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.name;
        opt.textContent = p.name;
        if (p.name === defaultVal) opt.selected = true;
        select.appendChild(opt);
    });
}

async function updateUI() {
    const p1 = allPokemon.find(p => p.name === p1Select.value);
    const p2 = allPokemon.find(p => p.name === p2Select.value);

    renderPokemon('p1', p1);
    renderPokemon('p2', p2);

    // Fetch Prediction
    const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ p1: p1.name, p2: p2.name })
    });
    const data = await res.json();

    document.getElementById('p1-prob').textContent = (data.p1_prob * 100).toFixed(1) + "%";
    document.getElementById('p2-prob').textContent = (data.p2_prob * 100).toFixed(1) + "%";

    const p1Color = TYPE_COLORS[p1.type1] || "#00F5FF";
    const p2Color = TYPE_COLORS[p2.type1] || "#FF3CAC";
    injectDynamicTheme(p1Color, p2Color);
}

function injectDynamicTheme(color1, color2) {
    if (dynamicStyleEl) {
        dynamicStyleEl.remove();
    }
    dynamicStyleEl = document.createElement('style');
    dynamicStyleEl.textContent = `
    body::before {
        background: radial-gradient(circle at left, ${color1}22 0%, #050816 60%),
                    radial-gradient(circle at right, ${color2}22 0%, #050816 60%) !important;
        transition: background 0.5s ease;
    }
    #p1-card {
        border: 2px solid ${color1} !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.8), 0 0 25px ${color1}66 !important;
    }
    #p2-card {
        border: 2px solid ${color2} !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.8), 0 0 25px ${color2}66 !important;
    }
    #start-btn {
        background: linear-gradient(135deg, ${color1}, ${color2}) !important;
        color: black !important;
    }
    `;
    document.head.appendChild(dynamicStyleEl);
}

function applyVictoryTheme(color) {
    if (dynamicStyleEl) {
        dynamicStyleEl.remove();
    }
    dynamicStyleEl = document.createElement('style');
    dynamicStyleEl.textContent = `
    body::before {
        background: radial-gradient(circle at center, ${color}55 0%, #050816 70%) !important;
        transition: background 1s ease;
    }
    .pokemon-card {
        box-shadow: 0 0 40px ${color} !important;
    }
    `;
    document.head.appendChild(dynamicStyleEl);
}

function renderPokemon(id, data) {
    document.getElementById(`${id}-name`).textContent = data.name;
    document.getElementById(`${id}-sprite`).src = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${data.pokedex_number}.png`;

    // Stats and HP
    document.getElementById(`${id}-hp-max`).textContent = data.hp;
    document.getElementById(`${id}-hp-val`).textContent = data.hp;
    const hpBar = document.getElementById(`${id}-hp-bar`);
    hpBar.style.width = "100%";
    hpBar.classList.remove('low');

    const statsContainer = document.getElementById(`${id}-stats`);
    const stats = ["attack", "defense", "sp_attack", "sp_defense", "speed"];
    statsContainer.innerHTML = stats.map(s => `
        <div class="stat-row">
            <span>${s.replace('_', ' ').toUpperCase()}</span>
            <span>${data[s]}</span>
        </div>
    `).join('') + `
        <div class="stat-row" style="color:var(--secondary);">
            <span>HEIGHT</span>
            <span>${data.height_m.toFixed(1)}m</span>
        </div>
        <div class="stat-row" style="color:var(--secondary);">
            <span>WEIGHT</span>
            <span>${data.weight_kg.toFixed(1)}kg</span>
        </div>
        <div class="stat-row" style="color:var(--secondary);">
            <span>BMI</span>
            <span>${data.bmi.toFixed(1)}</span>
        </div>
    `;

    const typesContainer = document.getElementById(`${id}-types`);
    typesContainer.innerHTML = `<span class="type-badge type-${data.type1}">${data.type1}</span>`;
    if (data.type2 !== "none") {
        typesContainer.innerHTML += `<span class="type-badge type-${data.type2}">${data.type2}</span>`;
    }
}

async function startBattle() {
    startBtn.disabled = true;
    logEl.innerHTML = '<div class="log-entry">Initializing battle...</div>';

    const p1Name = p1Select.value;
    const p2Name = p2Select.value;

    try {
        const res = await fetch('/api/battle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ p1: p1Name, p2: p2Name })
        });
        const data = await res.json();

        await animateBattle(data);

    } catch (e) {
        addLog("Error starting battle. Is the server running?");
        console.error(e);
    } finally {
        startBtn.disabled = false;
        randomBtn.disabled = false;
    }
}

async function animateBattle(data) {
    const p1Max = data.p1_stats.hp;
    const p2Max = data.p2_stats.hp;
    const p1Card = document.getElementById('p1-card');
    const p2Card = document.getElementById('p2-card');

    document.getElementById('p1-hp-max').textContent = p1Max.toFixed(0);
    document.getElementById('p2-hp-max').textContent = p2Max.toFixed(0);

    p1Card.classList.remove('winner-glow');
    p2Card.classList.remove('winner-glow');

    for (const round of data.history) {
        for (const msg of round.log) {
            const isCrit = msg.includes("Critical hit!");
            let formattedMsg = msg
                .replace("Super effective!", '<span class="log-super">Super effective!</span>')
                .replace("Not very effective...", '<span class="log-not-very">Not very effective...</span>')
                .replace("Critical hit!", '<span class="log-crit">Critical hit!</span>')
                .replace(/(\(\d+\.\d+ damage\))/, '<span class="log-damage">$1</span>');

            addLog(`<strong>[Round ${round.round}]</strong> ${formattedMsg}`);

            // Update HP
            updateHP('p1', round.p1_hp, p1Max);
            updateHP('p2', round.p2_hp, p2Max);

            // Damage shake, sparks, and screen shake
            const dmgMatch = msg.match(/\((\d+\.\d+) damage\)/);
            if (dmgMatch) {
                const isP1Attacking = msg.startsWith(p1Select.value);
                const attackerId = isP1Attacking ? 'p1' : 'p2';
                const targetId = isP1Attacking ? 'p2' : 'p1';

                if (isCrit) {
                    triggerScreenShake();
                } else {
                    triggerAttackParticles(targetId, attackerId);
                }
                showDamage(targetId, dmgMatch[1]);
            }

            await sleep(600);
        }
    }

    if (data.winner === 1) {
        p1Card.classList.add('winner-glow');
        applyVictoryTheme(TYPE_COLORS[p1Select.value ? allPokemon.find(p => p.name === p1Select.value).type1 : 'normal']);
        addLog(`🏆 ${p1Select.value} IS THE WINNER!`);
    } else {
        p2Card.classList.add('winner-glow');
        applyVictoryTheme(TYPE_COLORS[p2Select.value ? allPokemon.find(p => p.name === p2Select.value).type1 : 'normal']);
        addLog(`🏆 ${p2Select.value} IS THE WINNER!`);
    }

    await fetchLeaderboard();
}

function updateHP(id, current, max) {
    const bar = document.getElementById(`${id}-hp-bar`);
    const val = document.getElementById(`${id}-hp-val`);
    const percent = (current / max) * 100;

    bar.style.width = Math.max(0, percent) + "%";
    val.textContent = Math.max(0, current).toFixed(1);

    if (percent < 30) bar.classList.add('low');
    else bar.classList.remove('low');
}

function triggerScreenShake() {
    const body = document.body;
    body.classList.add('screen-shake', 'crit-flash');
    setTimeout(() => {
        body.classList.remove('screen-shake', 'crit-flash');
    }, 450);
}

function triggerAttackParticles(targetId, attackerId) {
    const targetCard = document.getElementById(`${targetId}-card`);
    const attackerCard = document.getElementById(`${attackerId}-card`);

    // Attacker Glow
    attackerCard.classList.add('attacker-aura');
    setTimeout(() => attackerCard.classList.remove('attacker-aura'), 500);

    // Sparks
    const sparkContainer = document.createElement('div');
    sparkContainer.className = 'spark-container';

    for (let i = 0; i < 10; i++) {
        const spark = document.createElement('div');
        spark.className = 'spark';
        const leftPos = Math.floor(Math.random() * 80) + 10;
        const topPos = Math.floor(Math.random() * 50) + 40;
        const size = Math.floor(Math.random() * 6) + 6;
        const delay = Math.random() * 0.2;

        spark.style.left = `${leftPos}%`;
        spark.style.top = `${topPos}%`;
        spark.style.width = `${size}px`;
        spark.style.height = `${size}px`;
        spark.style.animationDelay = `${delay}s`;

        sparkContainer.appendChild(spark);
    }

    targetCard.appendChild(sparkContainer);

    // Cleanup sparks
    setTimeout(() => {
        if (targetCard.contains(sparkContainer)) {
            targetCard.removeChild(sparkContainer);
        }
    }, 1000);
}

function addLog(htmlMsg) {
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.innerHTML = htmlMsg;
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;
}

function showDamage(id, amount) {
    const card = document.getElementById(`${id}-card`);
    card.style.animation = 'none';
    void card.offsetWidth; // trigger reflow
    card.style.animation = 'shake 0.2s ease-in-out';

    // Show floating number
    const floatEl = document.createElement('div');
    floatEl.className = 'damage-float active';
    floatEl.textContent = `-${amount}`;
    floatEl.style.top = '40%';
    floatEl.style.left = '50%';
    floatEl.style.transform = 'translate(-50%, -50%)';
    card.appendChild(floatEl);

    // Remove after animation finishes
    setTimeout(() => {
        if (card.contains(floatEl)) {
            card.removeChild(floatEl);
        }
    }, 1000);
}

// Add shake animation to CSS dynamically or it's missing in my style.css
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0% { transform: translate(1px, 1px) rotate(0deg); }
        20% { transform: translate(-3px, 0px) rotate(-1deg); }
        40% { transform: translate(3px, 2px) rotate(1deg); }
        60% { transform: translate(-1px, -1px) rotate(1deg); }
        80% { transform: translate(-3px, 1px) rotate(0deg); }
        100% { transform: translate(1px, -2px) rotate(-1deg); }
    }
`;
document.head.appendChild(style);

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchLeaderboard() {
    try {
        const res = await fetch('/api/leaderboard');
        const lbData = await res.json();
        renderLeaderboard(lbData);
    } catch (e) {
        console.error("Error fetching leaderboard", e);
    }
}

function renderLeaderboard(lbData) {
    const tbody = document.getElementById('leaderboard-body');
    const champSpan = document.querySelector('#champion-text span');

    tbody.innerHTML = '';

    if (!lbData || lbData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No battles yet...</td></tr>';
        return;
    }

    champSpan.textContent = lbData[0].name;

    lbData.forEach((row, index) => {
        const rank = index + 1;
        const tr = document.createElement('tr');

        // Rank styling
        let rankHtml = `<td>${rank}</td>`;
        if (rank === 1) rankHtml = `<td class="rank-1">🥇 1</td>`;
        else if (rank === 2) rankHtml = `<td class="rank-2">🥈 2</td>`;
        else if (rank === 3) rankHtml = `<td class="rank-3">🥉 3</td>`;

        // Win rate styling
        let wrColorClass = "win-rate-low";
        if (row.win_rate >= 0.6) wrColorClass = "win-rate-high";
        else if (row.win_rate >= 0.4) wrColorClass = "win-rate-med";

        tr.innerHTML = `
            ${rankHtml}
            <td style="font-weight:bold;">${row.name}</td>
            <td style="color:#4ade80;">${row.wins}</td>
            <td style="color:#ef4444;">${row.losses}</td>
            <td class="${wrColorClass}">${(row.win_rate * 100).toFixed(1)}%</td>
        `;
        tbody.appendChild(tr);
    });
}

init();

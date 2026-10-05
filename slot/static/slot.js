const reels = window.SLOT_DATA.reels;
const positions = [...window.SLOT_DATA.initialPositions];
const timers = [null, null, null];
const stopped = [true, true, true];
const roundSlides = [null, null, null];

let gameActive = false;
let startPending = false;

const PAY_LINE_CELLS = {
    "上段": [[0, 0], [1, 0], [2, 0]],
    "中段": [[0, 1], [1, 1], [2, 1]],
    "下段": [[0, 2], [1, 2], [2, 2]],
    "右下がり": [[0, 0], [1, 1], [2, 2]],
    "右上がり": [[0, 2], [1, 1], [2, 0]],
    "左中段": [[0, 1]]
};

const startButton = document.getElementById("start-button");
const resetButton = document.getElementById("reset-button");
const stopButtons = [...document.querySelectorAll(".stop-button")];
const message = document.getElementById("message");

function symbolHtml(symbol) {
    const images = {
        "7": "/static/images/7図柄.png",
        "ベル": "/static/images/ベル図柄.png",
        "チェリー": "/static/images/チェリー図柄.png",
        "スイカ": "/static/images/スイカ図柄.png",
        "リプレイ": "/static/images/リプレイ図柄.png",
        "BAR": "/static/images/bar図柄.png"
    };

    if (!images[symbol]) return symbol;

    return `<img class="slot-symbol-image" src="${images[symbol]}" alt="${symbol}">`;
}

function renderReel(reelIndex) {
    const reel = reels[reelIndex];
    const center = positions[reelIndex];
    const upper = (center - 1 + reel.length) % reel.length;
    const lower = (center + 1) % reel.length;

    document.getElementById(`symbol-${reelIndex}-0`).innerHTML = symbolHtml(reel[upper]);
    document.getElementById(`symbol-${reelIndex}-1`).innerHTML = symbolHtml(reel[center]);
    document.getElementById(`symbol-${reelIndex}-2`).innerHTML = symbolHtml(reel[lower]);
}

function renderAllReels() {
    for (let i = 0; i < 3; i++) renderReel(i);
}

function clearWinHighlights() {
    document.querySelectorAll(".symbol").forEach(cell => {
        cell.classList.remove("win-highlight", "big-highlight");
    });
}

function highlightWins(wins) {
    clearWinHighlights();

    wins.forEach(win => {
        const cells = PAY_LINE_CELLS[win.line] || [];

        cells.forEach(([reelIndex, row]) => {
            const cell = document.getElementById(`symbol-${reelIndex}-${row}`);

            if (!cell) return;

            cell.classList.add(
                win.symbol === "7" ? "big-highlight" : "win-highlight"
            );
        });
    });
}

function updateState(state) {
    document.getElementById("credit").textContent = state.credit;
    document.getElementById("mode").textContent = state.mode;
    
    const chanceLamp = document.getElementById("chance-lamp");

    if (state.bonus_lamp_on) {
        chanceLamp.classList.add("on");
    } else {
        chanceLamp.classList.remove("on");
    }

    const bonus = document.getElementById("bonus-state");
    const replay = document.getElementById("replay-state");
    const bigProgress = document.getElementById("big-progress");

    bonus.hidden = !state.bonus_lamp_on;
    replay.hidden = !state.replay_pending;
    bigProgress.hidden = state.mode !== "BIG BONUS";
    document.getElementById("big-payout").textContent = state.big_payout;

    startButton.disabled = !state.can_start;
}


function renderSlides() {
    const text = roundSlides.map(value => value === null ? "-" : value).join(" / ");
    document.getElementById("debug-slides").textContent = text;
}

function updateDebug(debug) {
    if (debug) {
        document.getElementById("debug-role").textContent = debug.role;
        document.getElementById("debug-random").textContent = debug.random_value;
        document.getElementById("debug-bet").textContent = debug.bet;
    }
    renderSlides();
}

function startAnimation(reelIndex) {
    stopped[reelIndex] = false;
    timers[reelIndex] = setInterval(() => {
        positions[reelIndex] = (positions[reelIndex] + 1) % reels[reelIndex].length;
        renderReel(reelIndex);
    }, 80);
}

function stopAnimation(reelIndex) {
    if (timers[reelIndex] !== null) {
        clearInterval(timers[reelIndex]);
        timers[reelIndex] = null;
    }
    stopped[reelIndex] = true;
}

function stopAllAnimations() {
    for (let i = 0; i < 3; i++) stopAnimation(i);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function animateSingleSlide(reelIndex, slide, stopPosition) {
    for (let step = 0; step < slide; step++) {
        await sleep(130);
        positions[reelIndex] = (positions[reelIndex] + 1) % reels[reelIndex].length;
        renderReel(reelIndex);
    }

    positions[reelIndex] = stopPosition;
    renderReel(reelIndex);
}

function disableAllStops() {
    stopButtons.forEach(button => button.disabled = true);
}

function enableRemainingStops() {
    stopButtons.forEach((button, index) => {
        button.disabled = stopped[index];
    });
}

async function startGame() {
    if (gameActive || startPending) return;

    startPending = true;
    startButton.disabled = true;
    resetButton.disabled = true;
    stopButtons.forEach(button => button.disabled = true);
    roundSlides.fill(null);
    renderSlides();
    message.textContent = "Pythonで内部抽選中…";

    try {
        const response = await fetch("/api/start", {method: "POST"});
        const data = await response.json();

        if (!response.ok || !data.ok) {
            startPending = false;
            message.textContent = data.message || "STARTに失敗しました。";
            startButton.disabled = false;
            resetButton.disabled = false;
            return;
        }

        updateState(data.state);
        updateDebug(data.debug);
        message.textContent = data.message;
        gameActive = true;
        startPending = false;
        
        for (let i = 0; i < 3; i++) startAnimation(i);
        enableRemainingStops();
    } catch (error) {
        startPending = false;
        console.error(error);
        message.textContent = "サーバーとの通信に失敗しました。";
        startButton.disabled = false;
        resetButton.disabled = false;
    }
}

async function stopReel(reelIndex) {
    if (stopped[reelIndex] || stopButtons[reelIndex].disabled) return;

    // ボタンを押した瞬間の中央位置を記録し、表示上はいったん止める。
    const pressedPosition = positions[reelIndex];
    stopAnimation(reelIndex);
    disableAllStops();

    try {
        const response = await fetch("/api/stop", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                reel_index: reelIndex,
                position: pressedPosition
            })
        });

        const data = await response.json();

        if (!response.ok || !data.ok) {
            message.textContent = data.message || "STOPに失敗しました。";
            startAnimation(reelIndex);
            enableRemainingStops();
            return;
        }

        roundSlides[reelIndex] = data.slide;
        renderSlides();

        // Pythonが決めた0～4コマ分だけ、その場で滑って停止する。
        await animateSingleSlide(reelIndex, data.slide, data.stop_position);
        message.textContent = data.message;

        if (!data.complete) {
            enableRemainingStops();
            return;
        }
        gameActive = false;
        // 右リール停止でゲーム確定。
        updateState(data.state);
        updateDebug(data.debug);
        message.textContent = data.message;
        highlightWins(data.wins || []);
        stopButtons.forEach(button => button.disabled = true);
        resetButton.disabled = false;
        startButton.disabled = !data.state.can_start;
    } catch (error) {
        console.error(error);
        message.textContent = "サーバーとの通信に失敗しました。";
        startAnimation(reelIndex);
        enableRemainingStops();
    }
}

async function resetGame() {
    gameActive = false;
    startPending = false;

    clearWinHighlights();
    stopAllAnimations();
    stopButtons.forEach(button => button.disabled = true);
    startButton.disabled = true;
    resetButton.disabled = true;

    try {
        const response = await fetch("/api/reset", {method: "POST"});
        const data = await response.json();

        if (!response.ok || !data.ok) {
            message.textContent = data.message || "RESETに失敗しました。";
            return;
        }

        for (let i = 0; i < 3; i++) positions[i] = data.positions[i];
        roundSlides.fill(null);
        renderAllReels();
        updateState(data.state);
        document.getElementById("debug-role").textContent = "-";
        document.getElementById("debug-random").textContent = "-";
        document.getElementById("debug-bet").textContent = "-";
        renderSlides();
        message.textContent = data.message;
        resetButton.disabled = false;
    } catch (error) {
        console.error(error);
        message.textContent = "サーバーとの通信に失敗しました。";
        resetButton.disabled = false;
    }
}

startButton.addEventListener("click", startGame);
resetButton.addEventListener("click", resetGame);

stopButtons.forEach(button => {
    button.addEventListener("click", () => {
        stopReel(Number(button.dataset.reel));
    });
});

renderAllReels();

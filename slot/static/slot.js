const reels = window.SLOT_DATA.reels;
const positions = [...window.SLOT_DATA.initialPositions];
const timers = [null, null, null];
const stopped = [true, true, true];
const roundSlides = [null, null, null];

const startButton = document.getElementById("start-button");
const resetButton = document.getElementById("reset-button");
const stopButtons = [...document.querySelectorAll(".stop-button")];
const message = document.getElementById("message");

function renderReel(reelIndex) {
    const reel = reels[reelIndex];
    const center = positions[reelIndex];
    const upper = (center - 1 + reel.length) % reel.length;
    const lower = (center + 1) % reel.length;

    document.getElementById(`symbol-${reelIndex}-0`).textContent = reel[upper];
    document.getElementById(`symbol-${reelIndex}-1`).textContent = reel[center];
    document.getElementById(`symbol-${reelIndex}-2`).textContent = reel[lower];
}

function renderAllReels() {
    for (let i = 0; i < 3; i++) renderReel(i);
}

function updateState(state) {
    document.getElementById("credit").textContent = state.credit;
    document.getElementById("mode").textContent = state.mode;

    const bonus = document.getElementById("bonus-state");
    const replay = document.getElementById("replay-state");
    const bigProgress = document.getElementById("big-progress");

    bonus.hidden = !state.big_pending;
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

function enableOnlyStop(reelIndex) {
    stopButtons.forEach((button, index) => {
        button.disabled = index !== reelIndex;
    });
}

async function startGame() {
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
            message.textContent = data.message || "STARTに失敗しました。";
            startButton.disabled = false;
            resetButton.disabled = false;
            return;
        }

        updateState(data.state);
        updateDebug(data.debug);
        message.textContent = data.message;

        // 3本とも回転するが、STOPは左から順番に押す。
        for (let i = 0; i < 3; i++) startAnimation(i);
        enableOnlyStop(data.next_reel ?? 0);
    } catch (error) {
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
    stopButtons[reelIndex].disabled = true;

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
            // 通信・順序エラーなら、そのリールの回転を再開する。
            startAnimation(reelIndex);
            enableOnlyStop(reelIndex);
            return;
        }

        roundSlides[reelIndex] = data.slide;
        renderSlides();

        // Pythonが決めた0～4コマ分だけ、その場で滑って停止する。
        await animateSingleSlide(reelIndex, data.slide, data.stop_position);
        message.textContent = data.message;

        if (!data.complete) {
            enableOnlyStop(data.next_reel);
            return;
        }

        // 右リール停止でゲーム確定。
        updateState(data.state);
        updateDebug(data.debug);
        message.textContent = data.message;
        stopButtons.forEach(button => button.disabled = true);
        resetButton.disabled = false;
        startButton.disabled = !data.state.can_start;
    } catch (error) {
        console.error(error);
        message.textContent = "サーバーとの通信に失敗しました。";
        startAnimation(reelIndex);
        enableOnlyStop(reelIndex);
    }
}

async function resetGame() {
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

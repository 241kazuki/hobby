import random
from dataclasses import dataclass
from enum import Enum
from itertools import product
from functools import lru_cache

# ==========================================
# 基本設定
# ==========================================

INITIAL_CREDIT = 50
BET_AMOUNT = 3
BIG_BET_AMOUNT = 1
BIG_TARGET_PAYOUT = 100

# ==========================================
# リール配列
# ==========================================

REEL_1 = [
    "7", "スイカ", "ベル", "リプレイ", "チェリー",
    "ベル", "ベル", "リプレイ", "BAR", "ベル",
    "リプレイ", "BAR", "スイカ", "7", "ベル",
    "リプレイ", "スイカ", "チェリー", "ベル", "リプレイ",
    "リプレイ"
]

REEL_2 = [
    "リプレイ", "チェリー", "ベル", "7", "リプレイ",
    "リプレイ", "ベル", "スイカ", "リプレイ", "ベル",
    "ベル", "BAR", "リプレイ", "7", "ベル",
    "スイカ", "リプレイ", "チェリー", "ベル", "スイカ",
    "BAR"
]

REEL_3 = [
    "チェリー", "ベル", "スイカ", "リプレイ", "チェリー",
    "ベル", "ベル", "リプレイ", "ベル", "BAR",
    "7", "スイカ", "リプレイ", "ベル", "BAR",
    "リプレイ", "スイカ", "リプレイ", "ベル", "7",
    "リプレイ"
]

REELS = [REEL_1, REEL_2, REEL_3]

# ==========================================
# 役・ゲーム状態
# ==========================================

class Role(Enum):
    BIG = "BIG"
    BELL = "ベル"
    CHERRY = "チェリー"
    WATERMELON = "スイカ"
    REPLAY = "リプレイ"
    MISS = "ハズレ"


class GameState(Enum):
    NORMAL = "通常"
    BIG = "BIG BONUS"


LOTTERY_TABLE = [
    (100, Role.BIG),
    (1500, Role.BELL),
    (1000, Role.CHERRY),
    (500, Role.WATERMELON),
    (2000, Role.REPLAY),
    (4900, Role.MISS)
]

BIG_LOTTERY_TABLE = [
    (7000, Role.BELL),
    (1000, Role.CHERRY),
    (1500, Role.REPLAY),
    (500, Role.MISS)
]

PAYOUT_TABLE = {
    "7": 0,
    "ベル": 10,
    "チェリー": 5,
    "スイカ": 8,
    "リプレイ": 0
}

PAY_LINES = {
    "上段": [(0, 0), (1, 0), (2, 0)],
    "中段": [(0, 1), (1, 1), (2, 1)],
    "下段": [(0, 2), (1, 2), (2, 2)],
    "右下がり": [(0, 0), (1, 1), (2, 2)],
    "右上がり": [(0, 2), (1, 1), (2, 0)]
}

# ==========================================
# 状態データ
# ==========================================

@dataclass
class SlotState:
    credit: int = INITIAL_CREDIT
    replay_pending: bool = False
    state: GameState = GameState.NORMAL
    big_payout: int = 0
    big_pending: bool = False


@dataclass
class RoundContext:
    state_before: GameState
    bet: int
    random_value: int
    role: Role
    new_big_hit: bool
    replay_game: bool


@dataclass
class RoundResult:
    current_positions: list
    stopped_positions: list
    slides: list
    control_success: bool
    screen: list
    wins: list
    total_payout: int
    replay_hit: bool
    big_hit: bool
    big_started: bool
    big_carried: bool
    big_ended: bool

# ==========================================
# 抽選・表示用データ生成
# ==========================================

def lottery(state):
    table = BIG_LOTTERY_TABLE if state == GameState.BIG else LOTTERY_TABLE
    random_value = random.randrange(10000)
    border = 0
    for probability, role in table:
        border += probability
        if random_value < border:
            return random_value, role
    return random_value, Role.MISS


def role_to_symbol(role):
    if role == Role.BIG:
        return "7"
    if role == Role.BELL:
        return "ベル"
    if role == Role.CHERRY:
        return "チェリー"
    if role == Role.WATERMELON:
        return "スイカ"
    if role == Role.REPLAY:
        return "リプレイ"
    return None


def get_visible_symbols(reel, position):
    return [
        reel[(position - 1) % len(reel)],
        reel[position],
        reel[(position + 1) % len(reel)]
    ]


def create_screen(stopped_positions):
    return [
        get_visible_symbols(REELS[i], stopped_positions[i])
        for i in range(3)
    ]


def check_paylines(screen):
    total_payout = 0
    wins = []

    # チェリーは左リール中段だけで成立
    if screen[0][1] == "チェリー":
        payout = PAYOUT_TABLE["チェリー"]
        total_payout += payout
        wins.append(("左中段", "チェリー", payout))

    for line_name, positions in PAY_LINES.items():
        symbols = [screen[reel_number][row] for reel_number, row in positions]

        if (
            symbols[0] == symbols[1] == symbols[2]
            and symbols[0] in PAYOUT_TABLE
            and symbols[0] != "チェリー"
        ):
            symbol = symbols[0]
            payout = PAYOUT_TABLE[symbol]
            total_payout += payout
            wins.append((line_name, symbol, payout))

    return wins, total_payout

# ==========================================
# 引き込み・蹴り制御
# ==========================================

def choose_stop_positions(current_positions, role):
    target_symbol = role_to_symbol(role)
    target_candidates = []
    safe_candidates = []

    for slides in product(range(5), repeat=3):
        stopped_positions = [
            (current_positions[i] + slides[i]) % len(REELS[i])
            for i in range(3)
        ]
        screen = create_screen(stopped_positions)
        wins, _ = check_paylines(screen)
        candidate = (sum(slides), max(slides), slides, stopped_positions)

        if not wins:
            safe_candidates.append(candidate)

        if role == Role.MISS:
            continue

        target_wins = [win for win in wins if win[1] == target_symbol]
        other_wins = [win for win in wins if win[1] != target_symbol]
        if target_wins and not other_wins:
            target_candidates.append(candidate)

    if role == Role.MISS and safe_candidates:
        best = min(safe_candidates, key=lambda x: (x[0], x[1], x[2]))
        return best[3], list(best[2]), True

    if role != Role.MISS:
        if target_candidates:
            best = min(target_candidates, key=lambda x: (x[0], x[1], x[2]))
            return best[3], list(best[2]), True
        if safe_candidates:
            best = min(safe_candidates, key=lambda x: (x[0], x[1], x[2]))
            return best[3], list(best[2]), False

    return current_positions, [0, 0, 0], False


# ==========================================
# 逐次停止制御
# ==========================================

def _visible_symbol(reel_index, stop_position, row):
    visible = get_visible_symbols(REELS[reel_index], stop_position)
    return visible[row]


def _compatible_target_lines(partial_positions, target_symbol):
    count = 0

    for positions in PAY_LINES.values():
        compatible = True

        for reel_index, row in positions:
            stop_position = partial_positions[reel_index]

            if stop_position is None:
                continue

            if _visible_symbol(reel_index, stop_position, row) != target_symbol:
                compatible = False
                break

        if compatible:
            count += 1

    return count

def _compatible_role(partial_positions, role):
    if role == Role.CHERRY:
        if partial_positions[0] is None:
            return 1

        return (
            1
            if _visible_symbol(0, partial_positions[0], 1) == "チェリー"
            else 0
        )

    return _compatible_target_lines(
        partial_positions,
        role_to_symbol(role)
    )

def _partial_pair_risk(partial_positions, target_symbol=None):
    risk = 0

    for positions in PAY_LINES.values():
        symbols = []

        for reel_index, row in positions:
            stop_position = partial_positions[reel_index]

            if stop_position is None:
                continue

            symbols.append(
                _visible_symbol(reel_index, stop_position, row)
            )

        if len(symbols) >= 2 and len(set(symbols)) == 1:
            symbol = symbols[0]

            if (
                symbol in PAYOUT_TABLE
                and symbol != "チェリー"
                and symbol != target_symbol
            ):
                risk += 1

    return risk


@lru_cache(maxsize=None)
def _future_final_coverage(role, partial_positions, remaining_reel):
    target_symbol = role_to_symbol(role)
    safe_coverage = 0
    target_coverage = 0

    for pressed_position in range(len(REELS[remaining_reel])):
        has_safe = False
        has_target = False

        for slide in range(5):
            stop_position = (
                pressed_position + slide
            ) % len(REELS[remaining_reel])

            full_positions = list(partial_positions)
            full_positions[remaining_reel] = stop_position

            screen = create_screen(full_positions)
            wins, _ = check_paylines(screen)

            if role == Role.MISS:
                if not wins:
                    has_safe = True
                    break
                continue

            target_wins = [
                win for win in wins
                if win[1] == target_symbol
            ]

            other_wins = [
                win for win in wins
                if win[1] != target_symbol
            ]

            if target_wins and not other_wins:
                has_target = True
                has_safe = True
                break

            if not wins:
                has_safe = True

        if has_safe:
            safe_coverage += 1

        if has_target:
            target_coverage += 1

    return safe_coverage, target_coverage

def _choose_cherry_stop(reel_index, pressed_position, stopped_positions):
    # チェリーは左リールのみ
    if reel_index != 0:
        return _choose_sequential_stop_cached(
            Role.CHERRY,
            reel_index,
            pressed_position,
            tuple(stopped_positions)
        )

    for slide in range(5):
        stop_position = (pressed_position + slide) % len(REELS[0])

        if REELS[0][stop_position] == "チェリー":
            return stop_position, slide, True

    return pressed_position, 0, False

def _choose_guaranteed_center_stop(role, reel_index, pressed_position):
    target_symbol = role_to_symbol(role)

    for slide in range(5):
        stop_position = (
            pressed_position + slide
        ) % len(REELS[reel_index])

        if REELS[reel_index][stop_position] == target_symbol:
            return stop_position, slide, True

    return pressed_position, 0, False

def _choose_big_stop(reel_index, pressed_position, stopped_positions):
    stopped_reels = [
        i for i, position in enumerate(stopped_positions)
        if position is not None
    ]

    # それまでのリールが中段7なら、中段7揃いを維持する
    center_seven = all(
        REELS[i][stopped_positions[i]] == "7"
        for i in stopped_reels
    )

    if center_seven:
        for slide in range(5):
            stop_position = (
                pressed_position + slide
            ) % len(REELS[reel_index])

            if REELS[reel_index][stop_position] != "7":
                continue

            partial = list(stopped_positions)
            partial[reel_index] = stop_position

            if None not in partial:
                wins, _ = check_paylines(create_screen(partial))
                target = [win for win in wins if win[1] == "7"]
                others = [win for win in wins if win[1] != "7"]

                if target and not others:
                    return stop_position, slide, True
                break

            return stop_position, slide, True

    return _choose_sequential_stop_cached(
        Role.BIG,
        reel_index,
        pressed_position,
        tuple(stopped_positions)
    )

def choose_sequential_stop(role, reel_index, pressed_position, stopped_positions):
    if role in (Role.BELL, Role.REPLAY):
        return _choose_guaranteed_center_stop(
            role, reel_index, pressed_position
        )

    if role == Role.BIG:
        return _choose_big_stop(
            reel_index, pressed_position, stopped_positions
        )
    if role == Role.CHERRY:
        return _choose_cherry_stop(
            reel_index, pressed_position, stopped_positions
        )
    return _choose_sequential_stop_cached(
        role, reel_index, pressed_position, tuple(stopped_positions)
    )
    


@lru_cache(maxsize=None)
def _choose_sequential_stop_cached(
    role,
    reel_index,
    pressed_position,
    stopped_positions
):
    if reel_index not in (0, 1, 2):
        raise ValueError("リール番号が不正です。")

    if len(stopped_positions) != 3:
        raise ValueError("stopped_positionsは3要素必要です。")

    if stopped_positions[reel_index] is not None:
        raise ValueError("このリールはすでに停止しています。")

    target_symbol = role_to_symbol(role)
    candidates = []

    for slide in range(5):
        stop_position = (
            pressed_position + slide
        ) % len(REELS[reel_index])
        # チェリー以外では左中段チェリーを誤って停止させない
        if (
            reel_index == 0
            and role != Role.CHERRY
            and REELS[0][stop_position] == "チェリー"
        ):
            continue
        partial = list(stopped_positions)
        partial[reel_index] = stop_position

        remaining = [
            i for i, position in enumerate(partial)
            if position is None
        ]

        # 最後のリール
        if not remaining:
            screen = create_screen(partial)
            wins, _ = check_paylines(screen)

            if role == Role.MISS:
                if not wins:
                    candidates.append(
                        ((0,), slide, stop_position, True)
                    )
                continue

            target_wins = [
                win for win in wins
                if win[1] == target_symbol
            ]

            other_wins = [
                win for win in wins
                if win[1] != target_symbol
            ]

            if target_wins and not other_wins:
                candidates.append(
                    ((0,), slide, stop_position, True)
                )

            elif not wins:
                candidates.append(
                    ((1,), slide, stop_position, False)
                )

            continue

        compatible = (
            0
            if role == Role.MISS
            else _compatible_role(partial, role)
        )

        risk = _partial_pair_risk(
            partial,
            None if role == Role.MISS else target_symbol
        )

        # 2本目停止
        if len(remaining) == 1:
            safe_coverage, target_coverage = (
                _future_final_coverage(
                    role,
                    tuple(partial),
                    remaining[0]
                )
            )

            if role == Role.MISS:
                score = (
                    -safe_coverage,
                    risk
                )
                success = safe_coverage > 0

            else:
                score = (
                    -safe_coverage,
                    -target_coverage,
                    -compatible,
                    risk
                )
                success = target_coverage > 0

            candidates.append(
                (
                    score,
                    slide,
                    stop_position,
                    success
                )
            )

            continue

        # 1本目停止
        if role == Role.MISS:
            score = (risk,)
            success = True

        else:
            score = (
                -compatible,
                risk
            )
            success = compatible > 0

        candidates.append(
            (
                score,
                slide,
                stop_position,
                success
            )
        )

    if not candidates:
        return pressed_position, 0, False

    best = min(
        candidates,
        key=lambda x: (
            x[0],
            x[1]
        )
    )
    _, slide, stop_position, success = best
    return stop_position, slide, success

# ==========================================
# 1ゲームの状態遷移
# ==========================================

def required_bet(slot_state):
    return BIG_BET_AMOUNT if slot_state.state == GameState.BIG else BET_AMOUNT


def can_start_game(slot_state):
    return slot_state.replay_pending or slot_state.credit >= required_bet(slot_state)


def begin_game(slot_state):
    if not can_start_game(slot_state):
        raise ValueError("CREDITが不足しています。")

    state_before = slot_state.state
    replay_game = slot_state.replay_pending

    if replay_game:
        bet = 0
        slot_state.replay_pending = False
    else:
        bet = required_bet(slot_state)
        slot_state.credit -= bet

    new_big_hit = False

    if slot_state.state == GameState.NORMAL and slot_state.big_pending:
        random_value = -1
        role = Role.BIG
    else:
        random_value, role = lottery(slot_state.state)
        if slot_state.state == GameState.NORMAL and role == Role.BIG:
            slot_state.big_pending = True
            new_big_hit = True

    return RoundContext(
        state_before=state_before,
        bet=bet,
        random_value=random_value,
        role=role,
        new_big_hit=new_big_hit,
        replay_game=replay_game
    )


def resolve_stopped_game(
    slot_state,
    round_context,
    current_positions,
    stopped_positions,
    slides,
    control_success
):
    """逐次停止済みの3リールを入賞判定し、CREDITや状態を更新する。"""
    screen = create_screen(stopped_positions)
    wins, total_payout = check_paylines(screen)

    slot_state.credit += total_payout

    replay_hit = any(symbol == "リプレイ" for _, symbol, _ in wins)
    if replay_hit:
        slot_state.replay_pending = True

    big_hit = any(symbol == "7" for _, symbol, _ in wins)
    big_started = False
    big_carried = False
    big_ended = False

    if (
        round_context.state_before == GameState.NORMAL
        and slot_state.big_pending
        and big_hit
    ):
        slot_state.state = GameState.BIG
        slot_state.big_pending = False
        slot_state.big_payout = 0
        slot_state.replay_pending = False
        big_started = True

    elif (
        round_context.state_before == GameState.NORMAL
        and slot_state.big_pending
        and not big_hit
    ):
        big_carried = True

    elif round_context.state_before == GameState.BIG:
        slot_state.big_payout += total_payout
        if slot_state.big_payout >= BIG_TARGET_PAYOUT:
            slot_state.state = GameState.NORMAL
            slot_state.big_payout = 0
            slot_state.replay_pending = False
            big_ended = True

    return RoundResult(
        current_positions=list(current_positions),
        stopped_positions=list(stopped_positions),
        slides=list(slides),
        control_success=control_success,
        screen=screen,
        wins=wins,
        total_payout=total_payout,
        replay_hit=replay_hit,
        big_hit=big_hit,
        big_started=big_started,
        big_carried=big_carried,
        big_ended=big_ended
    )


def resolve_game(slot_state, round_context, current_positions):
    """従来の3リール一括制御。デバッグやターミナル版との互換用。"""
    stopped_positions, slides, control_success = choose_stop_positions(
        current_positions,
        round_context.role
    )
    return resolve_stopped_game(
        slot_state,
        round_context,
        current_positions,
        stopped_positions,
        slides,
        control_success
    )


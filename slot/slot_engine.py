import random
from dataclasses import dataclass
from enum import Enum
from itertools import product

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
    "7", "リプレイ", "ベル", "チェリー", "ベル",
    "BAR", "リプレイ", "ベル", "チェリー", "リプレイ",
    "ベル", "7", "ベル", "チェリー", "ベル",
    "BAR", "リプレイ", "リプレイ", "チェリー", "リプレイ",
    "ベル"
]

REEL_2 = [
    "ベル", "BAR", "チェリー", "7", "リプレイ",
    "ベル", "リプレイ", "ベル", "リプレイ", "チェリー",
    "7", "リプレイ", "ベル", "ベル", "リプレイ",
    "BAR", "チェリー", "ベル", "リプレイ", "ベル",
    "リプレイ"
]

REEL_3 = [
    "リプレイ", "ベル", "リプレイ", "7", "ベル",
    "チェリー", "BAR", "リプレイ", "ベル", "ベル",
    "チェリー", "リプレイ", "7", "ベル", "リプレイ",
    "チェリー", "リプレイ", "ベル", "BAR", "ベル",
    "チェリー"
]

REELS = [REEL_1, REEL_2, REEL_3]

# ==========================================
# 役・ゲーム状態
# ==========================================

class Role(Enum):
    BIG = "BIG"
    BELL = "ベル"
    CHERRY = "チェリー"
    REPLAY = "リプレイ"
    MISS = "ハズレ"


class GameState(Enum):
    NORMAL = "通常"
    BIG = "BIG BONUS"


LOTTERY_TABLE = [
    (100, Role.BIG),
    (1500, Role.BELL),
    (1000, Role.CHERRY),
    (2000, Role.REPLAY),
    (5400, Role.MISS)
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

    for line_name, positions in PAY_LINES.items():
        symbols = [screen[reel_number][row] for reel_number, row in positions]
        if symbols[0] == symbols[1] == symbols[2] and symbols[0] in PAYOUT_TABLE:
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
    """停止済みリールがtarget_symbolでつながっている有効ライン数を返す。"""
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


def _partial_pair_risk(partial_positions, target_symbol=None):
    """停止済み2リール以上で同一役が並んでいるライン数を数える。"""
    risk = 0
    for positions in PAY_LINES.values():
        symbols = []
        for reel_index, row in positions:
            stop_position = partial_positions[reel_index]
            if stop_position is None:
                continue
            symbols.append(_visible_symbol(reel_index, stop_position, row))

        if len(symbols) >= 2 and len(set(symbols)) == 1:
            symbol = symbols[0]
            if symbol in PAYOUT_TABLE and symbol != target_symbol:
                risk += 1
    return risk


def choose_sequential_stop(role, reel_index, pressed_position, stopped_positions):
    """
    1本分のSTOP位置を0～4コマで決める。

    左・中リールでは将来の有効ラインをできるだけ残し、
    右リールでは最終的な入賞／蹴りを確定する。
    """
    if reel_index not in (0, 1, 2):
        raise ValueError("リール番号が不正です。")

    if len(stopped_positions) != 3:
        raise ValueError("stopped_positionsは3要素必要です。")

    target_symbol = role_to_symbol(role)
    candidates = []

    for slide in range(5):
        stop_position = (pressed_position + slide) % len(REELS[reel_index])
        partial = list(stopped_positions)
        partial[reel_index] = stop_position

        # 右リールでは3本すべて停止するため、最終結果を直接判定する。
        if reel_index == 2:
            screen = create_screen(partial)
            wins, _ = check_paylines(screen)

            if role == Role.MISS:
                if not wins:
                    candidates.append((0, slide, stop_position, True))
                continue

            target_wins = [win for win in wins if win[1] == target_symbol]
            other_wins = [win for win in wins if win[1] != target_symbol]

            if target_wins and not other_wins:
                candidates.append((0, slide, stop_position, True))
            elif not wins:
                # 当選役を引き込めない場合の安全なハズレ目。
                candidates.append((1, slide, stop_position, False))
            continue

        # 左・中リールでは、最終ラインを作りやすい停止位置を優先する。
        if role == Role.MISS:
            risk = _partial_pair_risk(partial)
            candidates.append((risk, slide, stop_position, True))
        else:
            compatible = _compatible_target_lines(partial, target_symbol)
            risk = _partial_pair_risk(partial, target_symbol)
            # compatibleが多いほど優先。次に別役のテンパイを避け、滑りを短くする。
            candidates.append((-compatible, risk, slide, stop_position, compatible > 0))

    if not candidates:
        return pressed_position, 0, False

    if reel_index == 2:
        best = min(candidates, key=lambda x: (x[0], x[1]))
        _, slide, stop_position, success = best
        return stop_position, slide, success

    if role == Role.MISS:
        best = min(candidates, key=lambda x: (x[0], x[1]))
        _, slide, stop_position, success = best
        return stop_position, slide, success

    best = min(candidates, key=lambda x: (x[0], x[1], x[2]))
    _, _, slide, stop_position, success = best
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


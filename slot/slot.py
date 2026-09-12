import random
from enum import Enum
from itertools import product


# ==========================================
# 基本設定
# ==========================================

INITIAL_CREDIT = 50
BET_AMOUNT = 3


# ==========================================
# STEP 1：リール配列
# ==========================================

REEL_1 = [
    "7", "ベル", "リプレイ", "チェリー", "ベル",
    "BAR", "リプレイ", "ベル", "チェリー", "リプレイ",
    "ベル", "7", "リプレイ", "ベル", "チェリー",
    "BAR", "ベル", "リプレイ", "ベル", "リプレイ",
    "チェリー"
]

REEL_2 = [
    "ベル", "リプレイ", "7", "ベル", "チェリー",
    "リプレイ", "BAR", "ベル", "リプレイ", "チェリー",
    "ベル", "リプレイ", "7", "ベル", "リプレイ",
    "BAR", "チェリー", "ベル", "リプレイ", "ベル",
    "リプレイ"
]

REEL_3 = [
    "リプレイ", "ベル", "チェリー", "7", "ベル",
    "リプレイ", "BAR", "ベル", "チェリー", "リプレイ",
    "ベル", "リプレイ", "7", "ベル", "チェリー",
    "BAR", "リプレイ", "ベル", "リプレイ", "ベル",
    "チェリー"
]

REELS = [
    REEL_1,
    REEL_2,
    REEL_3
]


# ==========================================
# STEP 2：役
# ==========================================

class Role(Enum):
    BIG = "BIG"
    BELL = "ベル"
    CHERRY = "チェリー"
    REPLAY = "リプレイ"
    MISS = "ハズレ"


LOTTERY_TABLE = [
    (100, Role.BIG),
    (1500, Role.BELL),
    (1000, Role.CHERRY),
    (2000, Role.REPLAY),
    (5400, Role.MISS)
]


# ==========================================
# STEP 3：内部抽選
# ==========================================

def lottery():

    random_value = random.randrange(10000)

    border = 0

    for probability, role in LOTTERY_TABLE:

        border += probability

        if random_value < border:
            return random_value, role

    return random_value, Role.MISS


# ==========================================
# 当選役 → 図柄
# ==========================================

def role_to_symbol(role):

    if role == Role.BIG:
        return "7"

    elif role == Role.BELL:
        return "ベル"

    elif role == Role.CHERRY:
        return "チェリー"

    elif role == Role.REPLAY:
        return "リプレイ"

    return None


# ==========================================
# 3段表示
# ==========================================

def get_visible_symbols(reel, position):

    upper = reel[
        (position - 1) % len(reel)
    ]

    center = reel[
        position
    ]

    lower = reel[
        (position + 1) % len(reel)
    ]

    return [
        upper,
        center,
        lower
    ]


# ==========================================
# 3×3画面作成
# ==========================================

def create_screen(stopped_positions):

    screen = []

    for reel_number in range(3):

        visible = get_visible_symbols(
            REELS[reel_number],
            stopped_positions[reel_number]
        )

        screen.append(visible)

    return screen


# ==========================================
# 画面表示
# ==========================================

def show_screen(screen):

    print()
    print("====================================")
    print("          リール停止結果")
    print("====================================")

    print(
        f"  {screen[0][0]:8}"
        f"{screen[1][0]:8}"
        f"{screen[2][0]:8}"
    )

    print(
        f"> {screen[0][1]:8}"
        f"{screen[1][1]:8}"
        f"{screen[2][1]:8} <"
    )

    print(
        f"  {screen[0][2]:8}"
        f"{screen[1][2]:8}"
        f"{screen[2][2]:8}"
    )

    print("====================================")


# ==========================================
# STEP 7：払い出し
#
# リプレイは0枚
# 次ゲームを無料にする
# ==========================================

PAYOUT_TABLE = {
    "7": 100,
    "ベル": 10,
    "チェリー": 5,
    "リプレイ": 0
}


# ==========================================
# 入賞ライン
# ==========================================

PAY_LINES = {

    "上段": [
        (0, 0),
        (1, 0),
        (2, 0)
    ],

    "中段": [
        (0, 1),
        (1, 1),
        (2, 1)
    ],

    "下段": [
        (0, 2),
        (1, 2),
        (2, 2)
    ],

    "右下がり": [
        (0, 0),
        (1, 1),
        (2, 2)
    ],

    "右上がり": [
        (0, 2),
        (1, 1),
        (2, 0)
    ]
}


# ==========================================
# 入賞判定
# ==========================================

def check_paylines(screen):

    total_payout = 0
    wins = []

    for line_name, positions in PAY_LINES.items():

        symbols = []

        for reel_number, row in positions:

            symbols.append(
                screen[reel_number][row]
            )

        if (
            symbols[0] == symbols[1]
            and symbols[1] == symbols[2]
        ):

            symbol = symbols[0]

            if symbol in PAYOUT_TABLE:

                payout = PAYOUT_TABLE[
                    symbol
                ]

                total_payout += payout

                wins.append(
                    (
                        line_name,
                        symbol,
                        payout
                    )
                )

    return wins, total_payout


# ==========================================
# STEP 6：引き込み・蹴り制御
# ==========================================

def choose_stop_positions(current_positions, role):

    target_symbol = role_to_symbol(role)

    ideal_candidates = []
    acceptable_candidates = []

    # 0～4コマ
    # 3リールで125通り
    for slides in product(
        range(5),
        repeat=3
    ):

        stopped_positions = []

        for i in range(3):

            position = (
                current_positions[i]
                + slides[i]
            ) % len(REELS[i])

            stopped_positions.append(
                position
            )

        screen = create_screen(
            stopped_positions
        )

        wins, _ = check_paylines(
            screen
        )

        # ----------------------------------
        # ハズレ
        # ----------------------------------

        if role == Role.MISS:

            if len(wins) == 0:

                ideal_candidates.append(
                    (
                        sum(slides),
                        max(slides),
                        slides,
                        stopped_positions
                    )
                )

        # ----------------------------------
        # 当選
        # ----------------------------------

        else:

            target_wins = []
            other_wins = []

            for win in wins:

                line_name, symbol, payout = win

                if symbol == target_symbol:

                    target_wins.append(
                        win
                    )

                else:

                    other_wins.append(
                        win
                    )

            if len(target_wins) > 0:

                candidate = (
                    sum(slides),
                    max(slides),
                    slides,
                    stopped_positions
                )

                acceptable_candidates.append(
                    candidate
                )

                if len(other_wins) == 0:

                    ideal_candidates.append(
                        candidate
                    )

    # ======================================
    # 最適候補選択
    # ======================================

    if len(ideal_candidates) > 0:

        candidates = ideal_candidates

    else:

        candidates = acceptable_candidates

    if len(candidates) > 0:

        candidates.sort(
            key=lambda x: (
                x[0],
                x[1],
                x[2]
            )
        )

        best = candidates[0]

        stopped_positions = best[3]
        slides = list(best[2])

        return (
            stopped_positions,
            slides,
            True
        )

    # 制御できなかった
    return (
        current_positions,
        [0, 0, 0],
        False
    )


# ==========================================
# STEP 7：1ゲーム
# ==========================================

def play_game(credit, replay_pending):

    print()
    print("====================================")

    # ======================================
    # BET処理
    # ======================================

    if replay_pending:

        print("★ REPLAY GAME ★")
        print("BET不要でゲーム開始")

        # 前ゲームのREPLAYを消費
        replay_pending = False

    else:

        credit -= BET_AMOUNT

        print(
            f"{BET_AMOUNT}枚BETしました。"
        )

    print(
        f"CREDIT : {credit}"
    )

    print("====================================")

    # ======================================
    # 内部抽選
    # ======================================

    random_value, role = lottery()

    print()
    print("====================================")
    print("内部抽選")
    print("====================================")

    print(
        f"抽選乱数 : {random_value}"
    )

    print(
        f"当選役   : {role.value}"
    )

    # ======================================
    # STOP入力位置
    #
    # 現在はランダム
    # ======================================

    current_positions = [
        random.randrange(
            len(REELS[0])
        ),

        random.randrange(
            len(REELS[1])
        ),

        random.randrange(
            len(REELS[2])
        )
    ]

    # ======================================
    # リール制御
    # ======================================

    (
        stopped_positions,
        slides,
        control_success
    ) = choose_stop_positions(
        current_positions,
        role
    )

    # ======================================
    # STOP
    # ======================================

    for i in range(3):

        print()
        print("------------------------------------")

        print(
            f"リール {i + 1}"
        )

        print("------------------------------------")

        print(
            f"STOP入力位置 : "
            f"{current_positions[i]}"
        )

        input("EnterでSTOP")

        print(
            f"滑りコマ数   : "
            f"{slides[i]}"
        )

        print(
            f"停止位置     : "
            f"{stopped_positions[i]}"
        )

    # ======================================
    # 画面表示
    # ======================================

    screen = create_screen(
        stopped_positions
    )

    show_screen(
        screen
    )

    # ======================================
    # 入賞判定
    # ======================================

    wins, total_payout = check_paylines(
        screen
    )

    print()
    print("========== 入賞判定 ==========")

    if len(wins) == 0:

        print("入賞なし")

    else:

        for line_name, symbol, payout in wins:

            # REPLAY
            if symbol == "リプレイ":

                print(
                    f"{line_name}ライン"
                    f" → リプレイ揃い"
                    f" → 再遊技"
                )

            # 通常払い出し
            else:

                print(
                    f"{line_name}ライン"
                    f" → {symbol}揃い"
                    f" → {payout}枚"
                )

    # ======================================
    # 払い出し
    # ======================================

    credit += total_payout

    if total_payout > 0:

        print()
        print(
            f"払い出し : "
            f"{total_payout}枚"
        )

    # ======================================
    # リプレイ判定
    # ======================================

    replay_hit = False

    for line_name, symbol, payout in wins:

        if symbol == "リプレイ":

            replay_hit = True

    if replay_hit:

        replay_pending = True

        print()
        print(
            "★ REPLAY ★"
        )

        print(
            "次ゲームはBETなしで遊べます。"
        )

    # ======================================
    # リール制御結果
    # ======================================

    print()
    print("========== リール制御 ==========")

    if role == Role.MISS:

        if len(wins) == 0:

            print(
                "蹴り制御成功："
                "入賞を回避しました。"
            )

        else:

            print(
                "警告：入賞を"
                "回避できませんでした。"
            )

    else:

        target_symbol = role_to_symbol(
            role
        )

        target_hit = False

        for line_name, symbol, payout in wins:

            if symbol == target_symbol:

                target_hit = True

        if target_hit:

            print(
                f"引き込み成功："
                f"{role.value}が成立しました。"
            )

        else:

            print(
                f"{role.value}当選ですが、"
                f"引き込めませんでした。"
            )

            print(
                "→ 取りこぼし"
            )

    # ======================================
    # 最終クレジット
    # ======================================

    print()
    print("====================================")

    print(
        f"CREDIT : {credit}"
    )

    print("====================================")

    return credit, replay_pending


# ==========================================
# メイン
# ==========================================

def main():

    credit = INITIAL_CREDIT

    replay_pending = False

    print("==============================")
    print("      Python SLOT")
    print("==============================")

    print(
        f"初期CREDIT : {credit}"
    )

    while True:

        print()
        print("------------------------------")

        print(
            f"CREDIT : {credit}"
        )

        if replay_pending:

            print(
                "REPLAY：次ゲームBET不要"
            )

        print("------------------------------")

        # ==================================
        # メダル不足
        # ==================================

        if (
            credit < BET_AMOUNT
            and not replay_pending
        ):

            print()
            print(
                "CREDITが不足しています。"
            )

            print(
                "ゲーム終了です。"
            )

            break

        command = input(
            "\nEnterでSTART / qで終了："
        )

        if command.lower() == "q":

            print(
                f"\n最終CREDIT : {credit}"
            )

            print(
                "終了します。"
            )

            break

        credit, replay_pending = play_game(
            credit,
            replay_pending
        )


if __name__ == "__main__":
    main()
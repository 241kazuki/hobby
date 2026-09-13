import random
from enum import Enum
from itertools import product


# ==========================================
# 基本設定
# ==========================================

INITIAL_CREDIT = 50

# 通常ゲーム
BET_AMOUNT = 3

# BIG BONUS
BIG_BET_AMOUNT = 1
BIG_TARGET_PAYOUT = 100

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
    (7000, Role.BELL),      # 70%
    (1000, Role.CHERRY),    # 10%
    (1500, Role.REPLAY),    # 15%
    (500, Role.MISS)        # 5%
]

# ==========================================
# STEP 3：内部抽選
# ==========================================

def lottery(state):


    if state == GameState.BIG:
        table = BIG_LOTTERY_TABLE
    else:
        table = LOTTERY_TABLE

    random_value = random.randrange(10000)

    border = 0

    for probability, role in table:

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
    "7": 0,
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

    target_candidates = []
    safe_candidates = []

    # ======================================
    # 0～4コマ × 3リール
    # 125通りを全探索
    # ======================================

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

        # ==================================
        # 何も揃っていない安全な停止位置
        # ==================================

        if len(wins) == 0:

            safe_candidates.append(
                (
                    sum(slides),
                    max(slides),
                    slides,
                    stopped_positions
                )
            )

        # ==================================
        # ハズレなら
        # 入賞なしだけを採用
        # ==================================

        if role == Role.MISS:
            continue

        # ==================================
        # 当選役の成立確認
        # ==================================

        target_wins = []

        other_wins = []

        for win in wins:

            line_name, symbol, payout = win

            if symbol == target_symbol:
                target_wins.append(win)

            else:
                other_wins.append(win)

        # ==================================
        # 当選役だけ成立している場合のみOK
        #
        # 例：
        # BIG + ベル → NG
        # BIGのみ     → OK
        # ==================================

        if (
            len(target_wins) > 0
            and len(other_wins) == 0
        ):

            target_candidates.append(
                (
                    sum(slides),
                    max(slides),
                    slides,
                    stopped_positions
                )
            )

    # ======================================
    # ハズレ
    # ======================================

    if role == Role.MISS:

        if len(safe_candidates) > 0:

            safe_candidates.sort(
                key=lambda x: (
                    x[0],
                    x[1],
                    x[2]
                )
            )

            best = safe_candidates[0]

            return (
                best[3],
                list(best[2]),
                True
            )

    # ======================================
    # 当選役を成立できる
    # ======================================

    else:

        if len(target_candidates) > 0:

            target_candidates.sort(
                key=lambda x: (
                    x[0],
                    x[1],
                    x[2]
                )
            )

            best = target_candidates[0]

            return (
                best[3],
                list(best[2]),
                True
            )

        # ==================================
        # 当選役を引き込めない場合
        #
        # 別役を成立させず、
        # 安全なハズレ目を選択する
        # ==================================

        if len(safe_candidates) > 0:

            safe_candidates.sort(
                key=lambda x: (
                    x[0],
                    x[1],
                    x[2]
                )
            )

            best = safe_candidates[0]

            return (
                best[3],
                list(best[2]),
                False
            )

    # 基本的にはここには来ない
    return (
        current_positions,
        [0, 0, 0],
        False
    )

# ==========================================
# STEP 7：1ゲーム
# ==========================================

def play_game(
    credit,
    replay_pending,
    state,
    big_payout,
    big_pending
):

    state_before = state

    print()
    print("====================================")

    print(
        f"GAME MODE : {state.value}"
    )

    # ======================================
    # BET
    # ======================================

    if replay_pending:

        print("★ REPLAY GAME ★")
        print("BET不要でゲーム開始")

        replay_pending = False

    else:

        if state == GameState.BIG:
            bet = BIG_BET_AMOUNT

        else:
            bet = BET_AMOUNT

        credit -= bet

        print(
            f"{bet}枚BETしました。"
        )

    print(
        f"CREDIT : {credit}"
    )

    if state == GameState.BIG:

        print(
            f"BIG獲得枚数 : "
            f"{big_payout}"
            f" / {BIG_TARGET_PAYOUT}"
        )

    # BIG成立中表示
    if (
        state == GameState.NORMAL
        and big_pending
    ):

        print()
        print("★ BIG成立中 ★")
        print("7揃い待ち")

    print("====================================")


    # ======================================
    # 内部抽選
    # ======================================

    new_big_hit = False

    # ======================================
    # BIG成立中なら
    # 新しい通常抽選は行わず
    # BIGを持ち越す
    # ======================================

    if (
        state == GameState.NORMAL
        and big_pending
    ):

        random_value = -1
        role = Role.BIG

    else:

        random_value, role = lottery(
            state
        )

        # ==================================
        # 新しくBIG内部当選
        # ==================================

        if (
            state == GameState.NORMAL
            and role == Role.BIG
        ):

            big_pending = True
            new_big_hit = True

    print()
    print("====================================")
    print("内部抽選")
    print("====================================")

    if random_value == -1:

        print(
            "抽選乱数 : 持ち越し"
        )

    else:

        print(
            f"抽選乱数 : {random_value}"
        )

    print(
        f"当選役   : {role.value}"
    )


    # ======================================
    # BIG告知
    # ======================================

    if new_big_hit:

        print()
        print("####################################")
        print("        ★ BONUS 確定 ★")
        print("####################################")
        print()
        print("BIG内部当選！")
        print("7を狙ってください！")

    elif (
        state == GameState.NORMAL
        and big_pending
    ):

        print()
        print("------------------------------------")
        print("        ★ BIG成立中 ★")
        print("------------------------------------")
        print("BIG当選を持ち越しています。")
        print("7を狙ってください。")


    # ======================================
    # STOP入力位置
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
    # 画面作成
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

            if symbol == "7":

                print(
                    f"{line_name}ライン"
                    f" → 7揃い"
                    f" → BIG BONUS"
                )

            elif symbol == "リプレイ":

                print(
                    f"{line_name}ライン"
                    f" → リプレイ揃い"
                    f" → 再遊技"
                )

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
    # REPLAY
    # ======================================

    replay_hit = any(
        symbol == "リプレイ"
        for line_name, symbol, payout
        in wins
    )

    if replay_hit:

        replay_pending = True

        print()
        print("★ REPLAY ★")

        print(
            "次ゲームはBETなしで遊べます。"
        )


    # ======================================
    # 7揃い確認
    # ======================================

    big_hit = any(
        symbol == "7"
        for line_name, symbol, payout
        in wins
    )


    # ======================================
    # BIG BONUS開始
    # ======================================

    if (
        state_before == GameState.NORMAL
        and big_pending
        and big_hit
    ):

        state = GameState.BIG

        big_pending = False

        big_payout = 0

        replay_pending = False

        print()
        print("####################################")
        print("        ★ BIG BONUS ★")
        print("####################################")

        print()
        print(
            "7揃い！"
        )

        print(
            "BIG BONUS開始！"
        )

        print(
            f"{BIG_TARGET_PAYOUT}枚以上の"
            f"払い出しで終了します。"
        )


    # ======================================
    # BIG持ち越し
    # ======================================

    elif (
        state_before == GameState.NORMAL
        and big_pending
        and not big_hit
    ):

        print()
        print("####################################")
        print("        ★ BIG 持ち越し ★")
        print("####################################")

        print()
        print(
            "今回は7を揃えられませんでした。"
        )

        print(
            "BIG当選は次ゲームへ持ち越します。"
        )


    # ======================================
    # BIG BONUS中
    # ======================================

    elif state_before == GameState.BIG:

        big_payout += total_payout

        print()
        print(
            f"BIG獲得枚数 : "
            f"{big_payout}"
            f" / {BIG_TARGET_PAYOUT}"
        )

        if big_payout >= BIG_TARGET_PAYOUT:

            print()
            print("####################################")
            print("        BIG BONUS 終了")
            print("####################################")

            print(
                f"BIG払い出し合計 : "
                f"{big_payout}枚"
            )

            state = GameState.NORMAL

            big_payout = 0

            replay_pending = False

            print(
                "通常ゲームへ戻ります。"
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
                "警告："
                "意図しない入賞があります。"
            )

    else:

        target_symbol = role_to_symbol(
            role
        )

        target_hit = any(
            symbol == target_symbol
            for line_name, symbol, payout
            in wins
        )

        other_hit = any(
            symbol != target_symbol
            for line_name, symbol, payout
            in wins
        )

        if (
            target_hit
            and not other_hit
        ):

            print(
                f"引き込み成功："
                f"{role.value}が成立しました。"
            )

        elif not target_hit:

            print(
                f"{role.value}当選ですが、"
                f"4コマ以内に引き込めませんでした。"
            )

            if role == Role.BIG:

                print(
                    "→ BIG当選は持ち越し"
                )

            else:

                print(
                    "→ 取りこぼし"
                )

        else:

            print(
                "警告：別役が同時成立しています。"
            )


    # ======================================
    # 最終状態
    # ======================================

    print()
    print("====================================")

    print(
        f"CREDIT : {credit}"
    )

    print(
        f"MODE   : {state.value}"
    )

    if big_pending:

        print(
            "BONUS  : BIG成立中"
        )

    if state == GameState.BIG:

        print(
            f"BIG    : "
            f"{big_payout}"
            f" / {BIG_TARGET_PAYOUT}"
        )

    print("====================================")


    return (
        credit,
        replay_pending,
        state,
        big_payout,
        big_pending
    )



# ==========================================
# メイン
# ==========================================

def main():

    credit = INITIAL_CREDIT

    replay_pending = False

    state = GameState.NORMAL

    big_payout = 0

    # BIG内部当選持ち越しフラグ
    big_pending = False

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

        print(
            f"MODE   : {state.value}"
        )

        # ==================================
        # BIG成立中表示
        # ==================================

        if big_pending:

            print(
                "BONUS  : ★ BIG成立中 ★"
            )

        if state == GameState.BIG:

            print(
                f"BIG    : "
                f"{big_payout}"
                f" / {BIG_TARGET_PAYOUT}"
            )

        if replay_pending:

            print(
                "REPLAY：次ゲームBET不要"
            )

        print("------------------------------")


        # ==================================
        # 必要BET
        # ==================================

        if state == GameState.BIG:

            required_bet = BIG_BET_AMOUNT

        else:

            required_bet = BET_AMOUNT


        # ==================================
        # CREDIT不足
        # ==================================

        if (
            credit < required_bet
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


        (
            credit,
            replay_pending,
            state,
            big_payout,
            big_pending
        ) = play_game(
            credit,
            replay_pending,
            state,
            big_payout,
            big_pending
        )


if __name__ == "__main__":
    main()

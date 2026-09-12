import random
from enum import Enum


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

REELS = [REEL_1, REEL_2, REEL_3]


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
# STEP 4：リール制御
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


def find_stop_position(reel, current_position, role):

    target_symbol = role_to_symbol(role)

    # ハズレの場合はそのまま停止
    if target_symbol is None:
        return current_position, 0

    # 0～4コマ先を検索
    for slide in range(5):

        position = (current_position + slide) % len(reel)

        if reel[position] == target_symbol:
            return position, slide

    # 4コマ以内に当選図柄がなければそのまま停止
    return current_position, 0


# ==========================================
# リール表示
# ==========================================

def show_reel_window(reel, position):

    above = reel[(position - 1) % len(reel)]
    center = reel[position]
    below = reel[(position + 1) % len(reel)]

    print(f"  {above}")
    print(f"> {center} <")
    print(f"  {below}")


# ==========================================
# 1ゲーム
# ==========================================

def play_game():

    random_value, role = lottery()

    print()
    print("==============================")
    print("内部抽選")
    print("==============================")

    print(f"抽選乱数 : {random_value}")
    print(f"当選役   : {role.value}")

    print()

    stopped_positions = []

    for reel_number, reel in enumerate(REELS):

        # STOPを押した瞬間を仮にランダムで決定
        current_position = random.randrange(len(reel))

        print("------------------------------")
        print(f"リール {reel_number + 1}")
        print("------------------------------")

        print("STOPを押した位置")
        print(f"位置 : {current_position}")

        show_reel_window(reel, current_position)

        input("\nEnterでSTOP")

        stop_position, slide = find_stop_position(
            reel,
            current_position,
            role
        )

        stopped_positions.append(stop_position)

        print()
        print(f"滑りコマ数 : {slide}")
        print(f"停止位置   : {stop_position}")

        show_reel_window(
            reel,
            stop_position
        )

        print()

    print("==============================")
    print("最終停止結果")
    print("==============================")

    for i, position in enumerate(stopped_positions):

        symbol = REELS[i][position]

        print(
            f"リール{i + 1} : "
            f"{symbol} "
            f"(位置 {position})"
        )


# ==========================================
# メイン
# ==========================================

def main():

    print("==============================")
    print("      Python SLOT")
    print("==============================")

    while True:

        command = input(
            "\nEnterでSTART / qで終了："
        )

        if command.lower() == "q":
            break

        play_game()


if __name__ == "__main__":
    main()
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
# STEP 2：内部抽選で使用する役
# ==========================================

# クラス管理することで後々使いやすくする（引き込む制御など）
class Role(Enum):
    BIG = "BIG"
    BELL = "ベル"
    CHERRY = "チェリー"
    REPLAY = "リプレイ"
    MISS = "ハズレ"


# 10000分率で確率を設定
#
# BIG       100 / 10000 = 1%
# ベル     1500 / 10000 = 15%
# チェリー 1000 / 10000 = 10%
# リプレイ 2000 / 10000 = 20%
# ハズレ   5400 / 10000 = 54%

LOTTERY_TABLE = [
    (100, Role.BIG),
    (1500, Role.BELL),
    (1000, Role.CHERRY),
    (2000, Role.REPLAY),
    (5400, Role.MISS)
]


# ==========================================
# STEP 3：内部抽選 → 当選役決定
# ==========================================

def lottery():
    # 0～9999の乱数を生成
    random_value = random.randrange(10000)

    border = 0

    for probability, role in LOTTERY_TABLE:
        border += probability

        if random_value < border:
            return random_value, role

    # 基本的にはここには到達しない
    return random_value, Role.MISS


# ==========================================
# リール配列確認用
# ==========================================

def show_reels():
    print("=== リール配列 ===")

    for reel_number, reel in enumerate(REELS, start=1):
        print(f"\nリール{reel_number}")

        for position, symbol in enumerate(reel):
            print(f"{position:2}: {symbol}")


# ==========================================
# メイン処理
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
            print("終了します。")
            break

        random_value, role = lottery()

        print()
        print("----- 内部抽選結果 -----")
        print(f"抽選乱数 : {random_value}")
        print(f"当選役   : {role.value}")

        if role == Role.BIG:
            print("★ BIG BONUS 当選！")

        elif role == Role.BELL:
            print("ベルが成立しました。")

        elif role == Role.CHERRY:
            print("チェリーが成立しました。")

        elif role == Role.REPLAY:
            print("リプレイが成立しました。")

        else:
            print("内部抽選はハズレです。")

def test_lottery(game_count=10000):# デバッグ用（1万回転）

    results = {
        Role.BIG: 0,
        Role.BELL: 0,
        Role.CHERRY: 0,
        Role.REPLAY: 0,
        Role.MISS: 0
    }

    for _ in range(game_count):
        _, role = lottery()
        results[role] += 1

    print(f"\n=== {game_count}ゲーム抽選結果 ===")

    for role, count in results.items():

        percentage = count / game_count * 100

        print(
            f"{role.value:8} "
            f"{count:5}回 "
            f"({percentage:.2f}%)"
        )

if __name__ == "__main__":
    #test_lottery(10000)　#　デバッグ
    main()
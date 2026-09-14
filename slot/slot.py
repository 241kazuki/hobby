import random

from slot_engine import (
    BIG_TARGET_PAYOUT,
    REELS,
    GameState,
    Role,
    SlotState,
    begin_game,
    can_start_game,
    resolve_game,
    role_to_symbol,
)


def show_screen(screen):
    print()
    print("====================================")
    print("          リール停止結果")
    print("====================================")
    print(f"  {screen[0][0]:8}{screen[1][0]:8}{screen[2][0]:8}")
    print(f"> {screen[0][1]:8}{screen[1][1]:8}{screen[2][1]:8} <")
    print(f"  {screen[0][2]:8}{screen[1][2]:8}{screen[2][2]:8}")
    print("====================================")


def show_control_result(role, wins):
    print()
    print("========== リール制御 ==========")

    if role == Role.MISS:
        if not wins:
            print("蹴り制御成功：入賞を回避しました。")
        else:
            print("警告：意図しない入賞があります。")
        return

    target_symbol = role_to_symbol(role)
    target_hit = any(symbol == target_symbol for _, symbol, _ in wins)
    other_hit = any(symbol != target_symbol for _, symbol, _ in wins)

    if target_hit and not other_hit:
        print(f"引き込み成功：{role.value}が成立しました。")
    elif not target_hit:
        print(f"{role.value}当選ですが、4コマ以内に引き込めませんでした。")
        print("→ BIG当選は持ち越し" if role == Role.BIG else "→ 取りこぼし")
    else:
        print("警告：別役が同時成立しています。")


def play_game(slot_state):
    print()
    print("====================================")
    print(f"GAME MODE : {slot_state.state.value}")

    round_context = begin_game(slot_state)

    if round_context.replay_game:
        print("★ REPLAY GAME ★")
        print("BET不要でゲーム開始")
    else:
        print(f"{round_context.bet}枚BETしました。")

    print(f"CREDIT : {slot_state.credit}")
    if slot_state.state == GameState.BIG:
        print(f"BIG獲得枚数 : {slot_state.big_payout} / {BIG_TARGET_PAYOUT}")
    if round_context.state_before == GameState.NORMAL and slot_state.big_pending and not round_context.new_big_hit:
        print("\n★ BIG成立中 ★")
        print("7揃い待ち")
    print("====================================")

    print()
    print("====================================")
    print("内部抽選")
    print("====================================")
    print("抽選乱数 : 持ち越し" if round_context.random_value == -1 else f"抽選乱数 : {round_context.random_value}")
    print(f"当選役   : {round_context.role.value}")

    if round_context.new_big_hit:
        print("\n####################################")
        print("        ★ BONUS 確定 ★")
        print("####################################")
        print("\nBIG内部当選！")
        print("7を狙ってください！")
    elif round_context.state_before == GameState.NORMAL and slot_state.big_pending:
        print("\n------------------------------------")
        print("        ★ BIG成立中 ★")
        print("------------------------------------")
        print("BIG当選を持ち越しています。")
        print("7を狙ってください。")

    current_positions = [random.randrange(len(reel)) for reel in REELS]
    result = resolve_game(slot_state, round_context, current_positions)

    for i in range(3):
        print("\n------------------------------------")
        print(f"リール {i + 1}")
        print("------------------------------------")
        print(f"STOP入力位置 : {result.current_positions[i]}")
        input("EnterでSTOP")
        print(f"滑りコマ数   : {result.slides[i]}")
        print(f"停止位置     : {result.stopped_positions[i]}")

    show_screen(result.screen)

    print("\n========== 入賞判定 ==========")
    if not result.wins:
        print("入賞なし")
    else:
        for line_name, symbol, payout in result.wins:
            if symbol == "7":
                print(f"{line_name}ライン → 7揃い → BIG BONUS")
            elif symbol == "リプレイ":
                print(f"{line_name}ライン → リプレイ揃い → 再遊技")
            else:
                print(f"{line_name}ライン → {symbol}揃い → {payout}枚")

    if result.total_payout > 0:
        print(f"\n払い出し : {result.total_payout}枚")

    if result.replay_hit:
        print("\n★ REPLAY ★")
        print("次ゲームはBETなしで遊べます。")

    if result.big_started:
        print("\n####################################")
        print("        ★ BIG BONUS ★")
        print("####################################")
        print("\n7揃い！")
        print("BIG BONUS開始！")
        print(f"{BIG_TARGET_PAYOUT}枚以上の払い出しで終了します。")
    elif result.big_carried:
        print("\n####################################")
        print("        ★ BIG 持ち越し ★")
        print("####################################")
        print("\n今回は7を揃えられませんでした。")
        print("BIG当選は次ゲームへ持ち越します。")
    elif round_context.state_before == GameState.BIG:
        if result.big_ended:
            print("\n####################################")
            print("        BIG BONUS 終了")
            print("####################################")
            print("通常ゲームへ戻ります。")
        else:
            print(f"\nBIG獲得枚数 : {slot_state.big_payout} / {BIG_TARGET_PAYOUT}")

    show_control_result(round_context.role, result.wins)

    print("\n====================================")
    print(f"CREDIT : {slot_state.credit}")
    print(f"MODE   : {slot_state.state.value}")
    if slot_state.big_pending:
        print("BONUS  : BIG成立中")
    if slot_state.state == GameState.BIG:
        print(f"BIG    : {slot_state.big_payout} / {BIG_TARGET_PAYOUT}")
    print("====================================")


def main():
    slot_state = SlotState()

    print("==============================")
    print("      Python SLOT")
    print("==============================")
    print(f"初期CREDIT : {slot_state.credit}")

    while True:
        print("\n------------------------------")
        print(f"CREDIT : {slot_state.credit}")
        print(f"MODE   : {slot_state.state.value}")
        if slot_state.big_pending:
            print("BONUS  : ★ BIG成立中 ★")
        if slot_state.state == GameState.BIG:
            print(f"BIG    : {slot_state.big_payout} / {BIG_TARGET_PAYOUT}")
        if slot_state.replay_pending:
            print("REPLAY：次ゲームBET不要")
        print("------------------------------")

        if not can_start_game(slot_state):
            print("\nCREDITが不足しています。")
            print("ゲーム終了です。")
            break

        command = input("\nEnterでSTART / qで終了：")
        if command.lower() == "q":
            print(f"\n最終CREDIT : {slot_state.credit}")
            print("終了します。")
            break

        play_game(slot_state)


if __name__ == "__main__":
    main()

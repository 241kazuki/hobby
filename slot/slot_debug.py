from itertools import product
from unittest.mock import patch

import slot_engine as slot


def test_basic_settings():
    print("====================================")
    print("        DEBUG TEST START")
    print("====================================")

    print("\n[1] リール配列チェック")
    for i, reel in enumerate(slot.REELS, start=1):
        print(f"REEL {i} : {len(reel)}コマ")
        assert len(reel) == 21
    print("OK")

    print("\n[2] 通常抽選テーブル")
    normal_total = sum(probability for probability, _ in slot.LOTTERY_TABLE)
    print(f"合計 : {normal_total}")
    assert normal_total == 10000
    print("OK")

    print("\n[3] BIG抽選テーブル")
    big_total = sum(probability for probability, _ in slot.BIG_LOTTERY_TABLE)
    print(f"合計 : {big_total}")
    assert big_total == 10000
    print("OK")


def test_reel_control():
    print("\n[4] リール制御全探索")
    print("21 × 21 × 21 = 9261通り")

    roles = [slot.Role.BIG, slot.Role.BELL, slot.Role.CHERRY, slot.Role.REPLAY, slot.Role.MISS]

    for role in roles:
        total = success = simultaneous = unsafe = 0

        for positions in product(range(21), repeat=3):
            total += 1
            stopped_positions, slides, control_success = slot.choose_stop_positions(list(positions), role)

            assert all(0 <= slide <= 4 for slide in slides)
            for i, stop_position in enumerate(stopped_positions):
                assert 0 <= stop_position < len(slot.REELS[i])

            screen = slot.create_screen(stopped_positions)
            wins, _ = slot.check_paylines(screen)

            if role == slot.Role.MISS:
                if wins:
                    unsafe += 1
                else:
                    success += 1
                continue

            target_symbol = slot.role_to_symbol(role)
            target_wins = [win for win in wins if win[1] == target_symbol]
            other_wins = [win for win in wins if win[1] != target_symbol]

            if control_success:
                assert target_wins
                assert not other_wins
                success += 1
            else:
                assert not wins

            if target_wins and other_wins:
                simultaneous += 1

        percentage = success / total * 100
        print(f"\n{role.value:8} : {success:4} / {total} ({percentage:.2f}%)")

        if role == slot.Role.MISS:
            print(f"意図しない入賞 : {unsafe}")
            assert unsafe == 0
        else:
            print(f"別役同時成立   : {simultaneous}")
            assert simultaneous == 0


def find_big_positions(want_success):
    for positions in product(range(21), repeat=3):
        _, _, control_success = slot.choose_stop_positions(list(positions), slot.Role.BIG)
        if control_success == want_success:
            return list(positions)
    raise AssertionError(f"BIG control case not found: success={want_success}")


def test_big_carryover():
    print("\n[5] BIG持ち越し・状態遷移テスト")

    miss_positions = find_big_positions(False)
    hit_positions = find_big_positions(True)
    state = slot.SlotState()

    with patch.object(slot, "lottery", return_value=(42, slot.Role.BIG)):
        first_round = slot.begin_game(state)

    first_result = slot.resolve_game(state, first_round, miss_positions)

    assert first_round.new_big_hit is True
    assert state.state == slot.GameState.NORMAL
    assert state.big_pending is True
    assert first_result.big_carried is True
    assert first_result.big_started is False

    print(f"取りこぼしテスト位置                   : {miss_positions}")
    print("BIG内部当選 → 取りこぼし → 持ち越し : OK")

    second_round = slot.begin_game(state)
    second_result = slot.resolve_game(state, second_round, hit_positions)

    assert second_round.random_value == -1
    assert second_round.role == slot.Role.BIG
    assert state.state == slot.GameState.BIG
    assert state.big_pending is False
    assert second_result.big_started is True

    print(f"7揃いテスト位置                       : {hit_positions}")
    print("持ち越しBIG → 7揃い → BIG BONUS      : OK")


def main():
    test_basic_settings()
    test_reel_control()
    test_big_carryover()

    print("\n====================================")
    print("         ALL TESTS PASSED")
    print("====================================")


if __name__ == "__main__":
    main()

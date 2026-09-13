import io
from contextlib import redirect_stdout
from itertools import product
from unittest.mock import patch

import slot


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
    normal_total = sum(
        probability
        for probability, _ in slot.LOTTERY_TABLE
    )
    print(f"合計 : {normal_total}")
    assert normal_total == 10000
    print("OK")

    print("\n[3] BIG抽選テーブル")
    big_total = sum(
        probability
        for probability, _ in slot.BIG_LOTTERY_TABLE
    )
    print(f"合計 : {big_total}")
    assert big_total == 10000
    print("OK")


def test_reel_control():
    print("\n[4] リール制御全探索")
    print("21 × 21 × 21 = 9261通り")

    roles = [
        slot.Role.BIG,
        slot.Role.BELL,
        slot.Role.CHERRY,
        slot.Role.REPLAY,
        slot.Role.MISS,
    ]

    for role in roles:
        total = 0
        success = 0
        simultaneous = 0
        unsafe = 0

        for positions in product(range(21), repeat=3):
            total += 1

            stopped_positions, slides, control_success = (
                slot.choose_stop_positions(
                    list(positions),
                    role
                )
            )

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
            target_wins = [
                win for win in wins
                if win[1] == target_symbol
            ]
            other_wins = [
                win for win in wins
                if win[1] != target_symbol
            ]

            # 制御成功時に別役が同時成立してはいけない
            if control_success:
                assert target_wins
                assert not other_wins
                success += 1
            else:
                # 引き込めなかった場合は安全なハズレ目であること
                assert not wins

            if target_wins and other_wins:
                simultaneous += 1

        percentage = success / total * 100

        print()
        print(
            f"{role.value:8} : "
            f"{success:4} / {total} "
            f"({percentage:.2f}%)"
        )

        if role == slot.Role.MISS:
            print(f"意図しない入賞 : {unsafe}")
            assert unsafe == 0
        else:
            print(f"別役同時成立   : {simultaneous}")
            assert simultaneous == 0


def test_big_carryover():
    print("\n[5] BIG持ち越し・告知テスト")

    # BIGを引いたが、[0, 0, 3] では7を引き込めないケース
    with patch.object(
        slot,
        "lottery",
        return_value=(42, slot.Role.BIG)
    ):
        with patch.object(
            slot.random,
            "randrange",
            side_effect=[0, 0, 3]
        ):
            with patch(
                "builtins.input",
                return_value=""
            ):
                output = io.StringIO()

                with redirect_stdout(output):
                    result = slot.play_game(
                        credit=50,
                        replay_pending=False,
                        state=slot.GameState.NORMAL,
                        big_payout=0,
                        big_pending=False,
                    )

    credit, replay, state, big_payout, big_pending = result
    text = output.getvalue()

    assert state == slot.GameState.NORMAL
    assert big_pending is True
    assert "BONUS 確定" in text
    assert "BIG 持ち越し" in text

    print("BIG内部当選 → 取りこぼし → 持ち越し : OK")
    print("BONUS確定告知                         : OK")

    # 次ゲームはBIGを再抽選せず、持ち越したBIGを使用。
    # [0, 0, 0] は現在の配列で7を引き込める。
    with patch.object(
        slot.random,
        "randrange",
        side_effect=[0, 0, 0]
    ):
        with patch(
            "builtins.input",
            return_value=""
        ):
            output = io.StringIO()

            with redirect_stdout(output):
                result = slot.play_game(
                    credit=credit,
                    replay_pending=replay,
                    state=state,
                    big_payout=big_payout,
                    big_pending=big_pending,
                )

    _, _, state, _, big_pending = result
    text = output.getvalue()

    assert state == slot.GameState.BIG
    assert big_pending is False
    assert "BIG成立中" in text
    assert "BIG BONUS" in text

    print("BIG成立中告知                         : OK")
    print("持ち越しBIG → 7揃い → BIG BONUS      : OK")


def main():
    test_basic_settings()
    test_reel_control()
    test_big_carryover()

    print()
    print("====================================")
    print("         ALL TESTS PASSED")
    print("====================================")


if __name__ == "__main__":
    main()

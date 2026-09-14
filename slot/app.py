from flask import Flask, jsonify, render_template, request

from slot_engine import (
    BIG_TARGET_PAYOUT,
    REELS,
    SlotState,
    begin_game,
    can_start_game,
    choose_sequential_stop,
    create_screen,
    resolve_stopped_game,
)

app = Flask(__name__)

# ローカルで1人が遊ぶ前提。
slot_state = SlotState()
last_positions = [0, 0, 0]
active_context = None
pressed_positions = [None, None, None]
stopped_positions = [None, None, None]
round_slides = [None, None, None]
next_reel_index = 0


def state_json():
    return {
        "credit": slot_state.credit,
        "mode": slot_state.state.value,
        "big_pending": slot_state.big_pending,
        "big_payout": slot_state.big_payout,
        "big_target": BIG_TARGET_PAYOUT,
        "replay_pending": slot_state.replay_pending,
        "can_start": can_start_game(slot_state),
    }


def win_messages(result):
    messages = []
    for line_name, symbol, payout in result.wins:
        if symbol == "7":
            messages.append(f"{line_name}ライン：7揃い → BIG BONUS")
        elif symbol == "リプレイ":
            messages.append(f"{line_name}ライン：リプレイ揃い → 再遊技")
        else:
            messages.append(f"{line_name}ライン：{symbol}揃い → {payout}枚")
    return messages


def build_notice(context, result):
    if result.big_started:
        return "★ BIG BONUS START ★"
    if result.big_carried:
        return "★ BIG成立中：次ゲームへ持ち越し ★"
    if result.big_ended:
        return "BIG BONUS終了。通常ゲームへ戻りました。"
    if result.replay_hit:
        return "★ REPLAY：次ゲームはBET不要 ★"
    if context.new_big_hit:
        return "★ BONUS確定：BIG内部当選 ★"
    if result.wins:
        return " / ".join(win_messages(result))
    return "ハズレ"


@app.route("/")
def index():
    return render_template(
        "index.html",
        reels=REELS,
        initial_positions=last_positions,
        initial_screen=create_screen(last_positions),
        state=state_json(),
    )


@app.post("/api/start")
def start_game():
    global active_context, pressed_positions, stopped_positions
    global round_slides, next_reel_index

    if active_context is not None:
        return jsonify({"ok": False, "message": "すでにリールが回転中です。"}), 409

    if not can_start_game(slot_state):
        return jsonify({"ok": False, "message": "CREDITが不足しています。"}), 400

    active_context = begin_game(slot_state)
    pressed_positions = [None, None, None]
    stopped_positions = [None, None, None]
    round_slides = [None, None, None]
    next_reel_index = 0

    if active_context.new_big_hit:
        message = "★ BONUS確定！ 7を狙ってください ★"
    elif active_context.role.value == "BIG" and slot_state.big_pending:
        message = "★ BIG成立中：7を狙ってください ★"
    else:
        message = "リール回転中…STOP 1から順番に停止してください。"

    return jsonify({
        "ok": True,
        "message": message,
        "state": state_json(),
        "next_reel": next_reel_index,
        "debug": {
            "role": active_context.role.value,
            "random_value": (
                "持ち越し" if active_context.random_value == -1
                else active_context.random_value
            ),
            "bet": active_context.bet,
        },
    })


@app.post("/api/stop")
def stop_reel():
    global active_context, pressed_positions, stopped_positions
    global round_slides, next_reel_index, last_positions

    if active_context is None:
        return jsonify({"ok": False, "message": "STARTを押してください。"}), 409

    data = request.get_json(silent=True) or {}

    try:
        reel_index = int(data["reel_index"])
        position = int(data["position"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"ok": False, "message": "STOP情報が不正です。"}), 400

    if reel_index not in (0, 1, 2):
        return jsonify({"ok": False, "message": "リール番号が不正です。"}), 400

    if reel_index != next_reel_index:
        return jsonify({
            "ok": False,
            "message": f"STOP {next_reel_index + 1} を先に押してください。"
        }), 409

    if not 0 <= position < len(REELS[reel_index]):
        return jsonify({"ok": False, "message": "リール位置が不正です。"}), 400

    stop_position, slide, step_success = choose_sequential_stop(
        active_context.role,
        reel_index,
        position,
        stopped_positions,
    )

    pressed_positions[reel_index] = position
    stopped_positions[reel_index] = stop_position
    round_slides[reel_index] = slide

    # 左・中リールはその場で停止し、次のSTOPへ進む。
    if reel_index < 2:
        next_reel_index += 1
        return jsonify({
            "ok": True,
            "complete": False,
            "message": (
                f"STOP {reel_index + 1}：{slide}コマ滑り → "
                f"位置 {stop_position} で停止"
            ),
            "reel_index": reel_index,
            "pressed_position": position,
            "stop_position": stop_position,
            "slide": slide,
            "next_reel": next_reel_index,
            "partial_success": step_success,
        })

    # 右リール停止時点で1ゲームを確定する。
    context = active_context
    result = resolve_stopped_game(
        slot_state,
        context,
        pressed_positions,
        stopped_positions,
        round_slides,
        step_success,
    )
    last_positions = list(result.stopped_positions)

    response = {
        "ok": True,
        "complete": True,
        "message": build_notice(context, result),
        "state": state_json(),
        "reel_index": reel_index,
        "pressed_position": position,
        "stop_position": stop_position,
        "slide": slide,
        "current_positions": result.current_positions,
        "stopped_positions": result.stopped_positions,
        "slides": result.slides,
        "screen": result.screen,
        "wins": [
            {"line": line_name, "symbol": symbol, "payout": payout}
            for line_name, symbol, payout in result.wins
        ],
        "total_payout": result.total_payout,
        "control_success": result.control_success,
        "debug": {
            "role": context.role.value,
            "random_value": "持ち越し" if context.random_value == -1 else context.random_value,
            "bet": context.bet,
        },
    }

    active_context = None
    pressed_positions = [None, None, None]
    stopped_positions = [None, None, None]
    round_slides = [None, None, None]
    next_reel_index = 0
    return jsonify(response)


@app.post("/api/reset")
def reset_game():
    global slot_state, last_positions, active_context
    global pressed_positions, stopped_positions, round_slides, next_reel_index

    slot_state = SlotState()
    last_positions = [0, 0, 0]
    active_context = None
    pressed_positions = [None, None, None]
    stopped_positions = [None, None, None]
    round_slides = [None, None, None]
    next_reel_index = 0

    return jsonify({
        "ok": True,
        "message": "RESETしました。STARTを押してください。",
        "state": state_json(),
        "positions": last_positions,
        "screen": create_screen(last_positions),
    })


if __name__ == "__main__":
    app.run(debug=True)

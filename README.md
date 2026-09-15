# Web Slot Simulator (Flask × JavaScript)

Flaskをバックエンド、JavaScriptをフロントエンドに用いたブラウザ上で動作するスロットシミュレーターです。

## 概要
実機さながらの演出やリール制御、役判定ロジックをWebアプリケーションとして再現しました。
バックエンド側で出目や内部状態の計算を行い、APIを介してフロントエンドのアニメーションと同期させています。

## 主な機能
- **スロットゲームエンジン**: 内部状態に応じた小役・ボーナス抽選およびリール停止位置の制御ロジック
- **リアルタイムリール制御**: JavaScriptを用いたリール回転・停止アニメーション
- **Web API連携**: フロントエンドからの操作（BET・レバーオン・ストップ）に応じた非同期通信処理
- **デバッグ機能**: 開発・挙動確認用のデバッグスクリプト

## 構成・ファイル概要
- `app.py`: FlaskによるルーティングおよびWebサーバー処理
- `slot_engine.py`: 役抽選、確率計算、リール停止ロジックを司るコアモジュール
- `slot.py`: ゲームステート・セッション管理
- `templates/index.html`: ゲーム画面のUI定義
- `static/js/slot.js`: リール描画、アニメーション制御、API通信
- `static/css/style.css`: スロット筐体・リールデザインのスタイリング

## 使用技術
- **Backend**: Python 3.11, Flask
- **Frontend**: JavaScript (ES6+), HTML5, CSS3
- **Tools**: VS Code, Git / GitHub

## 起動方法
1. リポジトリをクローン
   ```bash
   git clone [https://github.com/241kazuki/web-slot-simulator.git](https://github.com/241kazuki/web-slot-simulator.git)
   cd web-slot-simulator

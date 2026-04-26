from __future__ import annotations

from .api import Api


def main() -> None:
    api = Api()
    room = api.create_room("Voice CLI")
    room_id = str(room["id"])

    print("Voice CLI mode ready")
    print("Speak to microphone. Say one of: หยุด, ออก, เลิก, พอ")

    while True:
        try:
            text = api.listen_once().strip()
        except Exception as exc:
            print(f"Mic error: {exc}")
            continue

        if not text:
            continue

        print(f"You: {text}")
        if text in {"หยุด", "ออก", "เลิก", "พอ"}:
            api.speak_text("ไว้คุยกันใหม่นะ")
            break

        reply = api.send_message(room_id, text)
        if reply:
            print(f"AI: {reply}")
            try:
                api.speak_text(reply)
            except Exception as exc:
                print(f"Speaker error: {exc}")


if __name__ == "__main__":
    main()

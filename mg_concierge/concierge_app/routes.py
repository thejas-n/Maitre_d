from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request


def create_blueprint(manager, agent, speech_service, profile):
    bp = Blueprint("concierge", __name__)

    @bp.route("/")
    def index():
        return render_template("index.html", profile=profile)

    @bp.route("/api/status")
    def status():
        return jsonify(manager.get_status())

    @bp.route("/api/checkout", methods=["POST"])
    def checkout():
        payload = request.get_json(force=True, silent=True) or {}
        table_id = payload.get("table_id")
        if not table_id:
            return jsonify({"success": False, "message": "table_id required"}), 400
        result = manager.checkout_and_fill_waitlist(table_id)
        code = 200 if result.get("success") else 400
        return jsonify(result), code

    @bp.route("/api/chat", methods=["POST"])
    def chat():
        payload = request.get_json(force=True, silent=True) or {}
        user_message = payload.get("message")
        if not user_message:
            return jsonify({"response": "I didn't catch that, could you repeat?"}), 400

        try:
            reply, event = agent.respond(user_message)
        except Exception as exc:  # pragma: no cover - runtime safety
            print(f"Chat error: {exc}")
            return jsonify({"response": "I had a glitch, could you say that again?"}), 500

        # If a waitlist event, append ETA from manager.get_status()
        if event and event.get("type") == "waitlist":
            status = manager.get_status()
            for entry in status["waitlist"]:
                if entry["name"] == event["name"] and entry["party_size"] == event["party_size"]:
                    event["eta_minutes"] = entry.get("eta_minutes")
                    break

        return jsonify(
            {
                "response": reply,
                "interactionComplete": bool(event),
                "event": event,
            }
        )

    @bp.route("/api/tts", methods=["POST"])
    def tts():
        if not speech_service.available:
            return jsonify({"error": "TTS unavailable"}), 500
        payload = request.get_json(force=True, silent=True) or {}
        text = payload.get("text")
        if not text:
            return jsonify({"error": "No text supplied"}), 400
        audio = speech_service.synthesize(text)
        if not audio:
            return jsonify({"error": "TTS failed"}), 500
        return jsonify({"audio": audio})

    return bp

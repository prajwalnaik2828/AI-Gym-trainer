import threading


_engine = None
_lock = threading.Lock()


def _get_engine():
    global _engine
    if _engine is not None:
        return _engine
    try:
        import pyttsx3
        with _lock:
            if _engine is None:
                _engine = pyttsx3.init()
        return _engine
    except Exception:
        return None


def speak(text: str) -> None:
    """
    Best-effort text-to-speech. Silently no-ops if TTS is unavailable.
    """
    try:
        engine = _get_engine()
        if engine is None:
            return
        # Run speaking in a non-blocking way so UI remains responsive
        def _run():
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception:
                pass
        threading.Thread(target=_run, daemon=True).start()
    except Exception:
        pass









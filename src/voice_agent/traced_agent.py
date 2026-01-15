"""
Voice Agent с трейсингом времени.

Показывает сколько времени занимает каждый этап:
- VAD (определение речи)
- STT (распознавание)
- LLM (генерация ответа)
- TTS (синтез речи)

Запуск:
    python -m src.voice_agent.traced_agent dev
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv

from livekit.agents import cli, WorkerOptions, JobContext
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, cartesia, silero, openai

load_dotenv()


class TimingTracker:
    """Трекер времени для каждого этапа."""
    
    def __init__(self):
        self.events = []
        self.turn_start = None
        self.stt_start = None
        self.llm_start = None
        self.tts_start = None
        
    def log(self, event: str, duration_ms: float = None):
        """Логировать событие."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if duration_ms:
            print(f"[{timestamp}] ⏱️  {event}: {duration_ms:.0f}ms")
        else:
            print(f"[{timestamp}] 📍 {event}")
        self.events.append({
            "time": timestamp,
            "event": event,
            "duration_ms": duration_ms
        })
    
    def start_turn(self):
        """Начало нового turn (пользователь начал говорить)."""
        self.turn_start = time.time()
        self.log("USER_SPEECH_START")
    
    def end_user_speech(self):
        """Пользователь закончил говорить."""
        if self.turn_start:
            duration = (time.time() - self.turn_start) * 1000
            self.log("USER_SPEECH_END", duration)
            self.stt_start = time.time()
    
    def stt_done(self, text: str):
        """STT завершён."""
        if self.stt_start:
            duration = (time.time() - self.stt_start) * 1000
            self.log(f"STT_DONE: '{text[:50]}...'", duration)
            self.llm_start = time.time()
    
    def llm_first_token(self):
        """Первый токен от LLM."""
        if self.llm_start:
            duration = (time.time() - self.llm_start) * 1000
            self.log("LLM_FIRST_TOKEN (TTFT)", duration)
    
    def llm_done(self, text: str):
        """LLM завершил генерацию."""
        if self.llm_start:
            duration = (time.time() - self.llm_start) * 1000
            self.log(f"LLM_DONE: '{text[:50]}...'", duration)
            self.tts_start = time.time()
    
    def tts_first_audio(self):
        """Первый аудио чанк от TTS."""
        if self.tts_start:
            duration = (time.time() - self.tts_start) * 1000
            self.log("TTS_FIRST_AUDIO", duration)
    
    def tts_done(self):
        """TTS завершён."""
        if self.tts_start:
            duration = (time.time() - self.tts_start) * 1000
            self.log("TTS_DONE", duration)
    
    def end_turn(self):
        """Конец turn (бот закончил говорить)."""
        if self.turn_start:
            total = (time.time() - self.turn_start) * 1000
            self.log("TURN_COMPLETE (total)", total)
            print("-" * 60)
            self.turn_start = None


tracker = TimingTracker()


async def entrypoint(ctx: JobContext):
    """Точка входа агента с трейсингом."""
    
    await ctx.connect()
    
    print(f"\n{'='*60}")
    print(f"[Agent] Подключен к комнате: {ctx.room.name}")
    print(f"[Agent] Трейсинг времени ВКЛЮЧЁН")
    print(f"{'='*60}\n")
    
    agent = Agent(
        instructions="""Ты голосовой ассистент компании AI Prosto.
Отвечай коротко и дружелюбно, 1-2 предложения.
Говори на русском языке.""",
    )
    
    # Выбор LLM
    use_groq = os.getenv("USE_GROQ", "true").lower() == "true"
    
    if use_groq and os.getenv("GROQ_API_KEY"):
        llm = openai.LLM(
            model="llama-3.1-8b-instant",
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
        )
        print("[Agent] LLM: Groq (llama-3.1-8b-instant)")
    else:
        llm = openai.LLM(
            model="qwen2:1.5b",
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )
        print("[Agent] LLM: Ollama (qwen2:1.5b)")
    
    # STT
    stt = deepgram.STT(
        model="nova-2",
        language="ru",
    )
    print("[Agent] STT: Deepgram (nova-2)")
    
    # TTS
    tts = cartesia.TTS(
        model="sonic-2",
        voice="064b17af-d36b-4bfb-b003-be07dba1b649",
        language="ru",
    )
    print("[Agent] TTS: Cartesia (sonic-2)")
    
    # VAD
    vad = silero.VAD.load()
    print("[Agent] VAD: Silero")
    print()
    
    session = AgentSession(
        llm=llm,
        stt=stt,
        tts=tts,
        vad=vad,
    )
    
    # Подписываемся на события для трейсинга
    @session.on("user_started_speaking")
    def on_user_started_speaking():
        tracker.start_turn()
    
    @session.on("user_stopped_speaking")
    def on_user_stopped_speaking():
        tracker.end_user_speech()
    
    @session.on("agent_started_speaking")
    def on_agent_started_speaking():
        tracker.tts_first_audio()
    
    @session.on("agent_stopped_speaking")
    def on_agent_stopped_speaking():
        tracker.tts_done()
        tracker.end_turn()
    
    await session.start(agent, room=ctx.room)
    
    tracker.log("AGENT_READY")
    await session.say("Здравствуйте! Чем могу помочь?")
    
    print("\n[Agent] Ожидаю голос... (смотри тайминги выше)")
    print("-" * 60)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="voice-agent"
    ))

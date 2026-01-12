"""
Voice Agent — голосовой AI-агент на базе LiveKit.

Компоненты:
- agent.py — основной агент
- pipeline.py — STT → LLM → TTS пайплайн
"""

from .agent import VoiceAgent

__all__ = ["VoiceAgent"]

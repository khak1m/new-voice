#!/usr/bin/env python3
"""
Тестирование Telemetry системы (Phase 3).

Этот скрипт тестирует:
1. TelemetryService - сбор и агрегация метрик
2. MetricCollector - хуки для timing
3. CostCalculator - расчёт стоимости
4. QualityMetrics - interruptions, sentiment, outcome

Запуск:
    python scripts/test_telemetry.py
"""

import sys
import asyncio
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_telemetry_service():
    """Тест TelemetryService."""
    print("=" * 70)
    print("🧪 ТЕСТ 1: TelemetryService")
    print("=" * 70)
    
    try:
        from telemetry import TelemetryService, TurnMetrics
        
        # Создаём mock session (без реальной БД)
        class MockSession:
            def __init__(self):
                self.added = []
                self.committed = False
            
            def add(self, obj):
                self.added.append(obj)
            
            async def commit(self):
                self.committed = True
            
            async def rollback(self):
                pass
            
            async def execute(self, query):
                class MockResult:
                    def scalar_one_or_none(self):
                        return None
                    def scalars(self):
                        class MockScalars:
                            def all(self):
                                return []
                        return MockScalars()
                return MockResult()
        
        session = MockSession()
        telemetry = TelemetryService(session)
        
        print("✅ TelemetryService создан")
        
        # Тест 1: Запись turn metrics
        from uuid import uuid4
        call_uuid = uuid4()
        call_id = str(call_uuid)
        
        turn1 = TurnMetrics(
            turn_number=1,
            role="user",
            content="Здравствуйте",
            ttfb_stt=150.5,
            latency_llm=250.3,
            ttfb_tts=100.2,
            eou_latency=500.0,
            llm_input_tokens=10,
            llm_output_tokens=20,
            tts_characters=50
        )
        
        await telemetry.record_turn(call_id, turn1)
        print("✅ Turn 1 записан")
        
        turn2 = TurnMetrics(
            turn_number=2,
            role="assistant",
            content="Здравствуйте! Чем могу помочь?",
            ttfb_stt=None,
            latency_llm=300.0,
            ttfb_tts=120.0,
            eou_latency=550.0,
            llm_input_tokens=30,
            llm_output_tokens=40,
            tts_characters=100
        )
        
        await telemetry.record_turn(call_id, turn2)
        print("✅ Turn 2 записан")
        
        # Тест 2: Агрегация метрик
        metrics = await telemetry.finalize_call(
            call_id=call_uuid,
            outcome="success",
            outcome_confidence=0.95,
            outcome_reason="Test call completed",
            interruption_count=1,
            sentiment_score=0.8,
            stt_duration_sec=5.0,
            livekit_duration_sec=60.0
        )
        
        if metrics:
            print("✅ Метрики агрегированы")
            print(f"   Turn count: {metrics.turn_count}")
            print(f"   Avg TTFB STT: {metrics.avg_ttfb_stt:.2f}ms")
            print(f"   Avg Latency LLM: {metrics.avg_latency_llm:.2f}ms")
            print(f"   Total LLM tokens: {metrics.llm_input_tokens + metrics.llm_output_tokens}")
            print(f"   Interruption rate: {metrics.interruption_rate:.2%}")
        else:
            print("❌ Не удалось агрегировать метрики")
            return False
        
        # Проверка агрегации
        assert metrics.turn_count == 2
        assert metrics.avg_ttfb_stt == 150.5  # Только turn1 имеет STT
        assert metrics.avg_latency_llm == 275.15  # (250.3 + 300.0) / 2
        assert metrics.llm_input_tokens == 40  # 10 + 30
        assert metrics.llm_output_tokens == 60  # 20 + 40
        assert metrics.interruption_count == 1
        assert metrics.interruption_rate == 0.5  # 1 / 2
        
        print("✅ Все проверки агрегации пройдены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metric_collector():
    """Тест MetricCollector."""
    print("\n" + "=" * 70)
    print("🧪 ТЕСТ 2: MetricCollector")
    print("=" * 70)
    
    try:
        from telemetry import MetricCollector
        
        # Mock TelemetryService
        class MockTelemetry:
            def __init__(self):
                self.recorded_turns = []
            
            async def record_turn(self, call_id, metrics):
                self.recorded_turns.append(metrics)
        
        telemetry = MockTelemetry()
        collector = MetricCollector("test-call-456", telemetry)
        
        print("✅ MetricCollector создан")
        
        # Симуляция turn
        collector.start_turn(role="user", content="Привет")
        print("✅ Turn начат")
        
        # Симуляция STT
        collector.on_stt_start()
        import time
        time.sleep(0.01)  # 10ms
        ttfb_stt = collector.on_stt_first_byte()
        
        if ttfb_stt and ttfb_stt > 0:
            print(f"✅ TTFB STT: {ttfb_stt:.2f}ms")
        else:
            print("❌ TTFB STT не записан")
            return False
        
        # Симуляция LLM
        collector.on_llm_start()
        time.sleep(0.02)  # 20ms
        latency_llm = collector.on_llm_complete(input_tokens=50, output_tokens=100)
        
        if latency_llm and latency_llm > 0:
            print(f"✅ Latency LLM: {latency_llm:.2f}ms")
        else:
            print("❌ Latency LLM не записан")
            return False
        
        # Симуляция TTS
        collector.on_tts_start("Привет! Как дела?")
        time.sleep(0.015)  # 15ms
        ttfb_tts = collector.on_tts_first_byte()
        
        if ttfb_tts and ttfb_tts > 0:
            print(f"✅ TTFB TTS: {ttfb_tts:.2f}ms")
        else:
            print("❌ TTFB TTS не записан")
            return False
        
        # EOU latency
        eou = collector.on_audio_playback_start()
        
        if eou and eou > 0:
            print(f"✅ EOU Latency: {eou:.2f}ms")
        else:
            print("❌ EOU Latency не записан")
            return False
        
        print("✅ Все timing hooks работают")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cost_calculator():
    """Тест CostCalculator."""
    print("\n" + "=" * 70)
    print("🧪 ТЕСТ 3: CostCalculator")
    print("=" * 70)
    
    try:
        from telemetry import CostCalculator, PricingConfig
        
        # Создаём calculator с дефолтными ценами
        calculator = CostCalculator()
        print("✅ CostCalculator создан")
        
        # Тест 1: Расчёт стоимости
        breakdown = calculator.calculate(
            stt_duration_sec=60.0,  # 1 минута STT
            llm_input_tokens=1000,
            llm_output_tokens=2000,
            tts_characters=5000,  # 5000 символов
            livekit_duration_sec=120.0  # 2 минуты LiveKit
        )
        
        print("✅ Стоимость рассчитана")
        print(f"   STT: ${float(breakdown.cost_stt):.4f}")
        print(f"   LLM: ${float(breakdown.cost_llm):.4f}")
        print(f"   TTS: ${float(breakdown.cost_tts):.4f}")
        print(f"   LiveKit: ${float(breakdown.cost_livekit):.4f}")
        print(f"   TOTAL: ${float(breakdown.cost_total):.4f}")
        
        # Проверка расчётов
        # STT: 60 * 0.0043 = 0.258
        expected_stt = Decimal("0.2580")
        assert breakdown.cost_stt == expected_stt, f"Expected {expected_stt}, got {breakdown.cost_stt}"
        
        # LLM: (1000/1M * 0.05) + (2000/1M * 0.08) = 0.00005 + 0.00016 = 0.00021
        # С округлением до 4 знаков: 0.0001 + 0.0002 = 0.0003
        expected_llm = Decimal("0.0003")
        assert breakdown.cost_llm == expected_llm, f"Expected {expected_llm}, got {breakdown.cost_llm}"
        
        # TTS: 5000/1000 * 0.015 = 0.075
        expected_tts = Decimal("0.0750")
        assert breakdown.cost_tts == expected_tts, f"Expected {expected_tts}, got {breakdown.cost_tts}"
        
        # LiveKit: 120/60 * 0.004 = 0.008
        expected_livekit = Decimal("0.0080")
        assert breakdown.cost_livekit == expected_livekit, f"Expected {expected_livekit}, got {breakdown.cost_livekit}"
        
        print("✅ Все расчёты корректны")
        
        # Тест 2: Оценка стоимости за минуту
        cost_per_minute = calculator.estimate_cost_per_minute(
            turns_per_minute=10,
            avg_user_speech_sec=3.0,
            avg_bot_response_chars=100,
            avg_llm_tokens_per_turn=200
        )
        
        print(f"✅ Оценка стоимости за минуту: ${float(cost_per_minute):.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_metrics():
    """Тест Quality Metrics."""
    print("\n" + "=" * 70)
    print("🧪 ТЕСТ 4: Quality Metrics")
    print("=" * 70)
    
    try:
        from telemetry.quality_metrics import (
            InterruptionTracker,
            OutcomeClassifier,
            CallOutcome,
            QualityMetricsCollector
        )
        
        # Тест 1: InterruptionTracker
        print("\n📊 Тест: InterruptionTracker")
        tracker = InterruptionTracker()
        
        # Нормальный разговор
        tracker.on_user_speech_start()  # User говорит
        tracker.on_bot_speech_start()   # Bot отвечает
        tracker.on_bot_speech_end()     # Bot закончил
        
        # Interruption
        tracker.on_bot_speech_start()   # Bot говорит
        is_interruption = tracker.on_user_speech_start()  # User перебивает
        
        assert is_interruption == True, "Should detect interruption"
        assert tracker.get_interruption_count() == 1, "Should have 1 interruption"
        
        rate = tracker.get_interruption_rate()
        assert rate == 0.5, f"Expected rate 0.5, got {rate}"  # 1 interruption / 2 turns
        
        print(f"✅ Interruptions: {tracker.get_interruption_count()}")
        print(f"✅ Interruption rate: {rate:.2%}")
        
        # Тест 2: OutcomeClassifier
        print("\n📊 Тест: OutcomeClassifier")
        classifier = OutcomeClassifier()
        
        # Success outcome
        result = classifier.classify_from_state(
            final_state="booking_success",
            turn_count=10,
            duration_sec=120.0
        )
        
        assert result.outcome == CallOutcome.SUCCESS
        assert result.confidence > 0.8
        print(f"✅ Success outcome: {result.outcome} (confidence: {result.confidence:.2f})")
        
        # Voicemail outcome
        result = classifier.classify_from_state(
            final_state="voicemail_detected",
            turn_count=2,
            duration_sec=5.0
        )
        
        assert result.outcome == CallOutcome.VOICEMAIL
        print(f"✅ Voicemail outcome: {result.outcome} (confidence: {result.confidence:.2f})")
        
        # Keyword-based classification
        transcript = """
        Пользователь: Здравствуйте
        Бот: Здравствуйте! Хотите записаться?
        Пользователь: Да, спасибо, отлично!
        Бот: Отлично, записал вас
        """
        
        result = classifier.classify_from_keywords(transcript)
        print(f"✅ Keyword outcome: {result.outcome} (confidence: {result.confidence:.2f})")
        
        # Тест 3: QualityMetricsCollector
        print("\n📊 Тест: QualityMetricsCollector")
        collector = QualityMetricsCollector()
        
        collector.on_user_speech_start()
        collector.on_bot_speech_start()
        collector.on_user_speech_start()  # Interruption
        
        metrics = collector.get_interruption_metrics()
        assert metrics["interruption_count"] == 1
        print(f"✅ QualityMetricsCollector: {metrics}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Основная функция тестирования."""
    print("\n" + "=" * 70)
    print("🚀 ТЕСТИРОВАНИЕ TELEMETRY СИСТЕМЫ (PHASE 3)")
    print("=" * 70)
    print()
    
    tests = [
        ("TelemetryService", test_telemetry_service),
        ("MetricCollector", test_metric_collector),
        ("CostCalculator", test_cost_calculator),
        ("QualityMetrics", test_quality_metrics),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        if asyncio.iscoroutinefunction(test_func):
            success = await test_func()
        else:
            success = test_func()
        results.append((test_name, success))
    
    # Итоговый отчет
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 70)
    print(f"Результат: {passed}/{total} тестов пройдено ({passed/total*100:.1f}%)")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Telemetry система готова к использованию")
        return 0
    else:
        print("\n💥 ЕСТЬ ПРОБЛЕМЫ!")
        print("❌ Некоторые тесты провалены")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

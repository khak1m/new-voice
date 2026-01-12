"""
LanguageDetector — определение языка речи пользователя.

Определяет язык (ru/en) и управляет переключением языка
согласно language_policy из конфига.
"""

import re
from dataclasses import dataclass
from typing import Optional

from .models import LanguagePolicy


@dataclass
class DetectionResult:
    """Результат определения языка."""
    language: str           # "ru" или "en"
    confidence: float       # Уверенность 0-1
    should_switch: bool     # Нужно ли переключить язык бота


class LanguageDetector:
    """
    Определяет язык текста и управляет переключением.
    
    Использование:
        detector = LanguageDetector(language_policy)
        
        result = detector.detect("Hello, I want to book", current_lang="ru")
        if result.should_switch:
            print(f"Переключаемся на {result.language}")
    """
    
    # Русские буквы
    CYRILLIC_PATTERN = re.compile(r'[а-яёА-ЯЁ]')
    
    # Английские буквы
    LATIN_PATTERN = re.compile(r'[a-zA-Z]')
    
    # Типичные русские слова
    RU_MARKERS = {
        'да', 'нет', 'привет', 'здравствуйте', 'хочу', 'можно', 'пожалуйста',
        'спасибо', 'записаться', 'когда', 'сколько', 'какой', 'где', 'как',
        'мне', 'меня', 'вас', 'вам', 'это', 'что', 'кто', 'почему',
    }
    
    # Типичные английские слова
    EN_MARKERS = {
        'yes', 'no', 'hello', 'hi', 'want', 'please', 'thank', 'thanks',
        'book', 'appointment', 'when', 'how', 'much', 'what', 'where', 'why',
        'can', 'could', 'would', 'the', 'is', 'are', 'am', 'have', 'has',
    }
    
    def __init__(self, policy: Optional[LanguagePolicy] = None):
        """
        Args:
            policy: Политика языка из конфига. Если None — дефолтная.
        """
        self.policy = policy or LanguagePolicy(
            default="ru",
            detect=True,
            allow_switch=True
        )
    
    def detect(
        self, 
        text: str, 
        current_language: str = "ru"
    ) -> DetectionResult:
        """
        Определить язык текста.
        
        Args:
            text: Текст от пользователя
            current_language: Текущий язык диалога
            
        Returns:
            DetectionResult с языком и флагом переключения
        """
        if not text or not text.strip():
            return DetectionResult(
                language=current_language,
                confidence=0.0,
                should_switch=False
            )
        
        text_lower = text.lower()
        
        # Считаем символы
        cyrillic_count = len(self.CYRILLIC_PATTERN.findall(text))
        latin_count = len(self.LATIN_PATTERN.findall(text))
        total_letters = cyrillic_count + latin_count
        
        if total_letters == 0:
            # Только цифры или спецсимволы
            return DetectionResult(
                language=current_language,
                confidence=0.5,
                should_switch=False
            )
        
        # Считаем маркерные слова
        words = set(re.findall(r'\b\w+\b', text_lower))
        ru_word_count = len(words & self.RU_MARKERS)
        en_word_count = len(words & self.EN_MARKERS)
        
        # Определяем язык
        ru_score = (cyrillic_count / total_letters) * 0.7 + (ru_word_count / max(len(words), 1)) * 0.3
        en_score = (latin_count / total_letters) * 0.7 + (en_word_count / max(len(words), 1)) * 0.3
        
        if ru_score > en_score:
            detected = "ru"
            confidence = min(ru_score, 1.0)
        else:
            detected = "en"
            confidence = min(en_score, 1.0)
        
        # Определяем нужно ли переключаться
        should_switch = self._should_switch(detected, current_language, confidence)
        
        return DetectionResult(
            language=detected,
            confidence=confidence,
            should_switch=should_switch
        )
    
    def _should_switch(
        self, 
        detected: str, 
        current: str, 
        confidence: float
    ) -> bool:
        """Определить нужно ли переключить язык."""
        
        # Если язык тот же — не переключаем
        if detected == current:
            return False
        
        # Если детекция выключена — не переключаем
        if not self.policy.detect:
            return False
        
        # Если переключение запрещено — не переключаем
        if not self.policy.allow_switch:
            return False
        
        # Переключаем только при высокой уверенности
        if confidence < 0.7:
            return False
        
        return True
    
    def get_default_language(self) -> str:
        """Получить язык по умолчанию."""
        return self.policy.default
    
    def is_switch_allowed(self) -> bool:
        """Разрешено ли переключение языка."""
        return self.policy.allow_switch

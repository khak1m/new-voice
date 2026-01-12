"""
FieldExtractor — извлечение и валидация данных из речи пользователя.

Вытаскивает из фразы клиента нужные данные:
- Телефон: "восемь девятьсот..." → "+79001234567"
- Дата: "завтра", "в пятницу" → "2026-01-13"
- Время: "в два часа" → "14:00"
- И другие типы полей
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional
from dataclasses import dataclass

from .models import FieldType, FieldToCollect


@dataclass
class ExtractionResult:
    """Результат извлечения данных."""
    success: bool
    value: Any = None
    raw_value: str = ""          # Что нашли в тексте
    confidence: float = 1.0      # Уверенность 0-1
    error: Optional[str] = None  # Причина ошибки


@dataclass  
class ValidationResult:
    """Результат валидации."""
    valid: bool
    value: Any = None            # Нормализованное значение
    error: Optional[str] = None


class BaseExtractor(ABC):
    """Базовый класс для извлечения данных."""
    
    @abstractmethod
    def extract(self, text: str, field: FieldToCollect) -> ExtractionResult:
        """Извлечь значение из текста."""
        pass
    
    @abstractmethod
    def validate(self, value: Any, field: FieldToCollect) -> ValidationResult:
        """Проверить и нормализовать значение."""
        pass


class PhoneExtractor(BaseExtractor):
    """Извлечение телефонных номеров."""
    
    # Паттерны для поиска телефона
    PATTERNS = [
        # +7 (900) 123-45-67
        r'\+?[78]?\s*\(?(\d{3})\)?\s*(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})',
        # 89001234567
        r'[78](\d{10})',
        # Словами: восемь девятьсот...
        r'(?:восемь|8|семь|7)\s*(?:девятьсот|девятисот|900|девять сот)',
    ]
    
    # Замена слов на цифры
    WORD_TO_DIGIT = {
        'ноль': '0', 'один': '1', 'два': '2', 'три': '3', 'четыре': '4',
        'пять': '5', 'шесть': '6', 'семь': '7', 'восемь': '8', 'девять': '9',
        'одна': '1', 'две': '2',
    }
    
    def extract(self, text: str, field: FieldToCollect) -> ExtractionResult:
        """Найти телефон в тексте."""
        text_lower = text.lower()
        
        # Заменяем слова на цифры
        normalized = text_lower
        for word, digit in self.WORD_TO_DIGIT.items():
            normalized = normalized.replace(word, digit)
        
        # Убираем всё кроме цифр и +
        digits_only = re.sub(r'[^\d+]', '', normalized)
        
        # Ищем 10-11 цифр
        match = re.search(r'\+?[78]?(\d{10})', digits_only)
        if match:
            phone = match.group(1)
            return ExtractionResult(
                success=True,
                value=f"+7{phone}",
                raw_value=match.group(0),
                confidence=0.9
            )
        
        return ExtractionResult(
            success=False,
            error="Не удалось найти номер телефона"
        )
    
    def validate(self, value: Any, field: FieldToCollect) -> ValidationResult:
        """Проверить формат телефона."""
        if not value:
            return ValidationResult(valid=False, error="Пустой номер")
        
        # Нормализуем
        digits = re.sub(r'[^\d]', '', str(value))
        
        if len(digits) == 11 and digits[0] in '78':
            return ValidationResult(valid=True, value=f"+7{digits[1:]}")
        elif len(digits) == 10:
            return ValidationResult(valid=True, value=f"+7{digits}")
        else:
            return ValidationResult(valid=False, error="Неверный формат телефона")


class DateExtractor(BaseExtractor):
    """Извлечение дат."""
    
    # Дни недели
    WEEKDAYS = {
        'понедельник': 0, 'вторник': 1, 'среда': 2, 'среду': 2,
        'четверг': 3, 'пятница': 4, 'пятницу': 4,
        'суббота': 5, 'субботу': 5, 'воскресенье': 6,
    }
    
    # Месяцы
    MONTHS = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
        'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4,
        'май': 5, 'июнь': 6, 'июль': 7, 'август': 8,
        'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12,
    }
    
    def extract(self, text: str, field: FieldToCollect) -> ExtractionResult:
        """Найти дату в тексте."""
        text_lower = text.lower()
        today = datetime.now().date()
        
        # Сегодня
        if 'сегодня' in text_lower:
            return ExtractionResult(
                success=True,
                value=today.isoformat(),
                raw_value='сегодня',
                confidence=1.0
            )
        
        # Завтра
        if 'завтра' in text_lower:
            date = today + timedelta(days=1)
            return ExtractionResult(
                success=True,
                value=date.isoformat(),
                raw_value='завтра',
                confidence=1.0
            )
        
        # Послезавтра
        if 'послезавтра' in text_lower:
            date = today + timedelta(days=2)
            return ExtractionResult(
                success=True,
                value=date.isoformat(),
                raw_value='послезавтра',
                confidence=1.0
            )
        
        # День недели
        for day_name, day_num in self.WEEKDAYS.items():
            if day_name in text_lower:
                # Находим ближайший такой день
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                date = today + timedelta(days=days_ahead)
                return ExtractionResult(
                    success=True,
                    value=date.isoformat(),
                    raw_value=day_name,
                    confidence=0.9
                )
        
        # Число + месяц: "15 января"
        for month_name, month_num in self.MONTHS.items():
            pattern = rf'(\d{{1,2}})\s*{month_name}'
            match = re.search(pattern, text_lower)
            if match:
                day = int(match.group(1))
                year = today.year
                # Если дата уже прошла — следующий год
                try:
                    date = datetime(year, month_num, day).date()
                    if date < today:
                        date = datetime(year + 1, month_num, day).date()
                    return ExtractionResult(
                        success=True,
                        value=date.isoformat(),
                        raw_value=match.group(0),
                        confidence=0.9
                    )
                except ValueError:
                    pass
        
        return ExtractionResult(
            success=False,
            error="Не удалось определить дату"
        )
    
    def validate(self, value: Any, field: FieldToCollect) -> ValidationResult:
        """Проверить дату."""
        if not value:
            return ValidationResult(valid=False, error="Пустая дата")
        
        try:
            # Пробуем распарсить ISO формат
            date = datetime.fromisoformat(str(value)).date()
            today = datetime.now().date()
            
            # Проверяем что дата не в прошлом
            if date < today:
                return ValidationResult(valid=False, error="Дата в прошлом")
            
            return ValidationResult(valid=True, value=date.isoformat())
        except ValueError:
            return ValidationResult(valid=False, error="Неверный формат даты")



class TimeExtractor(BaseExtractor):
    """Извлечение времени."""
    
    # Слова для времени
    TIME_WORDS = {
        'утром': '10:00', 'утро': '10:00',
        'днём': '14:00', 'днем': '14:00', 'день': '14:00',
        'после обеда': '14:00', 'обед': '13:00',
        'вечером': '18:00', 'вечер': '18:00',
    }
    
    HOUR_WORDS = {
        'час': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5,
        'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9, 'десять': 10,
        'одиннадцать': 11, 'двенадцать': 12,
    }
    
    def extract(self, text: str, field: FieldToCollect) -> ExtractionResult:
        """Найти время в тексте."""
        text_lower = text.lower()
        
        # Точное время: 14:00, 14.00, 14-00
        match = re.search(r'(\d{1,2})[:.\-](\d{2})', text)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return ExtractionResult(
                    success=True,
                    value=f"{hour:02d}:{minute:02d}",
                    raw_value=match.group(0),
                    confidence=1.0
                )
        
        # "в 14 часов", "в 2 часа"
        match = re.search(r'в\s*(\d{1,2})\s*час', text_lower)
        if match:
            hour = int(match.group(1))
            # Если час < 12 и не указано утро — считаем день
            if hour < 12 and 'утр' not in text_lower:
                hour += 12 if hour < 8 else 0
            if 0 <= hour <= 23:
                return ExtractionResult(
                    success=True,
                    value=f"{hour:02d}:00",
                    raw_value=match.group(0),
                    confidence=0.9
                )
        
        # Словами: "в два часа"
        for word, hour in self.HOUR_WORDS.items():
            if f'в {word}' in text_lower or f'{word} час' in text_lower:
                # Если < 8 — скорее всего день
                if hour < 8:
                    hour += 12
                return ExtractionResult(
                    success=True,
                    value=f"{hour:02d}:00",
                    raw_value=word,
                    confidence=0.8
                )
        
        # Общие слова: утром, днём, вечером
        for word, time_val in self.TIME_WORDS.items():
            if word in text_lower:
                return ExtractionResult(
                    success=True,
                    value=time_val,
                    raw_value=word,
                    confidence=0.7
                )
        
        return ExtractionResult(
            success=False,
            error="Не удалось определить время"
        )
    
    def validate(self, value: Any, field: FieldToCollect) -> ValidationResult:
        """Проверить время."""
        if not value:
            return ValidationResult(valid=False, error="Пустое время")
        
        # Парсим HH:MM
        match = re.match(r'^(\d{1,2}):(\d{2})$', str(value))
        if not match:
            return ValidationResult(valid=False, error="Неверный формат времени")
        
        hour, minute = int(match.group(1)), int(match.group(2))
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return ValidationResult(valid=False, error="Неверное время")
        
        # Проверяем рабочие часы если указано в field
        if field.validation_hint:
            # Простая проверка "с 9 до 21"
            match = re.search(r'с\s*(\d+)\s*до\s*(\d+)', field.validation_hint)
            if match:
                start, end = int(match.group(1)), int(match.group(2))
                if not (start <= hour < end):
                    return ValidationResult(
                        valid=False, 
                        error=f"Время должно быть с {start}:00 до {end}:00"
                    )
        
        return ValidationResult(valid=True, value=f"{hour:02d}:{minute:02d}")


class TextExtractor(BaseExtractor):
    """Извлечение текста (имя, адрес и т.д.)."""
    
    def extract(self, text: str, field: FieldToCollect) -> ExtractionResult:
        """Извлечь текст — просто возвращаем как есть."""
        text = text.strip()
        if text:
            return ExtractionResult(
                success=True,
                value=text,
                raw_value=text,
                confidence=0.8
            )
        return ExtractionResult(success=False, error="Пустой текст")
    
    def validate(self, value: Any, field: FieldToCollect) -> ValidationResult:
        """Проверить текст."""
        if not value or not str(value).strip():
            return ValidationResult(valid=False, error="Пустое значение")
        return ValidationResult(valid=True, value=str(value).strip())


class ChoiceExtractor(BaseExtractor):
    """Извлечение выбора из списка вариантов."""
    
    def extract(self, text: str, field: FieldToCollect) -> ExtractionResult:
        """Найти выбор из списка."""
        text_lower = text.lower()
        
        if not field.validation or not field.validation.choices:
            return ExtractionResult(success=False, error="Нет вариантов выбора")
        
        # Ищем совпадение с вариантами
        for choice in field.validation.choices:
            choice_id = choice.get('id', '')
            
            # Проверяем синонимы на русском и английском
            for lang in ['ru', 'en']:
                synonyms = choice.get(lang, [])
                if isinstance(synonyms, str):
                    synonyms = [synonyms]
                
                for synonym in synonyms:
                    if synonym.lower() in text_lower:
                        return ExtractionResult(
                            success=True,
                            value=choice_id,
                            raw_value=synonym,
                            confidence=0.9
                        )
        
        return ExtractionResult(
            success=False,
            error="Не удалось определить выбор"
        )
    
    def validate(self, value: Any, field: FieldToCollect) -> ValidationResult:
        """Проверить что выбор валидный."""
        if not field.validation or not field.validation.choices:
            return ValidationResult(valid=True, value=value)
        
        valid_ids = [c.get('id') for c in field.validation.choices]
        if value in valid_ids:
            return ValidationResult(valid=True, value=value)
        
        return ValidationResult(
            valid=False, 
            error=f"Неверный выбор. Доступно: {valid_ids}"
        )


class EmailExtractor(BaseExtractor):
    """Извлечение email."""
    
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    def extract(self, text: str, field: FieldToCollect) -> ExtractionResult:
        """Найти email в тексте."""
        match = re.search(self.EMAIL_PATTERN, text)
        if match:
            return ExtractionResult(
                success=True,
                value=match.group(0).lower(),
                raw_value=match.group(0),
                confidence=1.0
            )
        return ExtractionResult(success=False, error="Email не найден")
    
    def validate(self, value: Any, field: FieldToCollect) -> ValidationResult:
        """Проверить email."""
        if not value:
            return ValidationResult(valid=False, error="Пустой email")
        
        if re.match(self.EMAIL_PATTERN, str(value)):
            return ValidationResult(valid=True, value=str(value).lower())
        
        return ValidationResult(valid=False, error="Неверный формат email")


# =============================================================================
# Главный класс
# =============================================================================

class FieldExtractor:
    """
    Главный класс для извлечения данных.
    
    Использование:
        extractor = FieldExtractor()
        
        result = extractor.extract("Запишите на завтра", date_field)
        if result.success:
            print(f"Дата: {result.value}")
    """
    
    def __init__(self):
        self._extractors: dict[FieldType, BaseExtractor] = {
            FieldType.PHONE: PhoneExtractor(),
            FieldType.DATE: DateExtractor(),
            FieldType.TIME: TimeExtractor(),
            FieldType.TEXT: TextExtractor(),
            FieldType.CHOICE: ChoiceExtractor(),
            FieldType.EMAIL: EmailExtractor(),
            FieldType.NUMBER: TextExtractor(),  # Пока простой
            FieldType.BOOLEAN: TextExtractor(),  # Пока простой
        }
    
    def extract(self, text: str, field: FieldToCollect) -> ExtractionResult:
        """Извлечь значение поля из текста."""
        extractor = self._extractors.get(field.type)
        if not extractor:
            return ExtractionResult(
                success=False, 
                error=f"Неизвестный тип поля: {field.type}"
            )
        
        return extractor.extract(text, field)
    
    def validate(self, value: Any, field: FieldToCollect) -> ValidationResult:
        """Проверить значение поля."""
        extractor = self._extractors.get(field.type)
        if not extractor:
            return ValidationResult(valid=True, value=value)
        
        return extractor.validate(value, field)
    
    def extract_and_validate(
        self, 
        text: str, 
        field: FieldToCollect
    ) -> ExtractionResult:
        """Извлечь и сразу проверить."""
        result = self.extract(text, field)
        
        if not result.success:
            return result
        
        validation = self.validate(result.value, field)
        
        if not validation.valid:
            return ExtractionResult(
                success=False,
                value=result.value,
                raw_value=result.raw_value,
                error=validation.error
            )
        
        # Возвращаем нормализованное значение
        return ExtractionResult(
            success=True,
            value=validation.value,
            raw_value=result.raw_value,
            confidence=result.confidence
        )

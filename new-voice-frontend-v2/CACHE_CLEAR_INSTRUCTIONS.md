# Инструкция по очистке кеша и запуску

## Проблема
Браузер показывает старую версию интерфейса из-за кеша Vite.

## Решение выполнено
1. ✅ Исправлен импорт в `src/main.tsx` (добавлено `.tsx` расширение)
2. ✅ Очищен кеш Vite (`node_modules/.vite`)

## Что нужно сделать

### 1. Остановить dev server (если запущен)
Нажмите `Ctrl+C` в терминале где запущен `pnpm dev`

### 2. Запустить заново
```bash
cd "C:\Users\Dmitriy\Desktop\new voice\new-voice-frontend-v2"
pnpm dev
```

### 3. Очистить кеш браузера
Выберите ОДИН из вариантов:

**Вариант А: Hard Refresh (быстрый)**
- Chrome/Edge: `Ctrl + Shift + R` или `Ctrl + F5`
- Firefox: `Ctrl + Shift + R`

**Вариант Б: Incognito Mode (надежный)**
- Chrome/Edge: `Ctrl + Shift + N`
- Firefox: `Ctrl + Shift + P`
- Откройте http://localhost:5173

**Вариант В: Очистка через DevTools (полный)**
1. Откройте DevTools: `F12`
2. Правый клик на кнопке обновления страницы
3. Выберите "Empty Cache and Hard Reload"

### 4. Проверить консоль браузера
Откройте DevTools (`F12`) → вкладка Console
Проверьте, нет ли ошибок JavaScript

## Что должно появиться
После очистки кеша вы должны увидеть:
- ✅ Кнопку "Create Skillbase" в правом верхнем углу
- ✅ Модальное окно при клике на кнопку
- ✅ Форму с полями Name и Description
- ✅ Кнопки Cancel и Create

## Если не помогло
1. Полностью закройте браузер
2. Удалите папку `node_modules/.vite` вручную
3. Перезапустите `pnpm dev`
4. Откройте браузер в режиме Incognito

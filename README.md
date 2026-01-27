# NEW-VOICE 2.0 Frontend

Модульная архитектура фронтенда для платформы NEW-VOICE 2.0.

## 🏗️ Архитектура

Проект использует **monorepo** структуру с **pnpm workspaces**.

### Структура проекта

```
new-voice-frontend-v2/
├── packages/              # Переиспользуемые пакеты
│   ├── ui/               # UI компоненты
│   ├── api-client/       # API клиент
│   ├── shared/           # Утилиты и хуки
│   └── types/            # TypeScript типы
├── modules/              # Бизнес-модули
│   ├── skillbases/
│   ├── campaigns/
│   ├── analytics/
│   ├── calls/
│   ├── leads/
│   └── knowledge-bases/
└── src/                  # Главное приложение
```

## 🚀 Быстрый старт

### Предварительные требования

- Node.js >= 18.0.0
- pnpm >= 8.0.0

### Установка pnpm

```bash
# Через npm (рекомендуется)
npm install -g pnpm

# Проверить версию
pnpm --version
```

### Установка зависимостей

```bash
# Установить зависимости
pnpm install
```

Подробная инструкция: [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md)

### Разработка

```bash
# Запустить dev сервер
pnpm dev

# Запустить линтер
pnpm lint

# Проверить типы
pnpm type-check

# Форматировать код
pnpm format
```

### Сборка

```bash
# Собрать все пакеты
pnpm build
```

## 📦 Пакеты

### @new-voice/types

TypeScript типы для всего проекта.

**Содержимое:**
- Модели данных (Company, Skillbase, Campaign, Call, Lead, KnowledgeBase)
- API типы (Request/Response)
- Общие типы

### @new-voice/shared

Общие утилиты и хуки.

**Содержимое:**
- `cn()` - утилита для объединения классов
- `formatDate()`, `formatCurrency()`, `formatDuration()` - форматирование
- `useDebounce()` - debounce хук
- `useLocalStorage()` - localStorage хук
- Константы

### @new-voice/api-client

Типизированный API клиент для бэкенда.

**Содержимое:**
- `skillbasesClient` - работа со Skillbases
- `campaignsClient` - работа с кампаниями
- `callsClient` - работа со звонками
- `leadsClient` - работа с лидами
- `knowledgeBasesClient` - работа с базами знаний
- `companiesClient` - работа с компаниями
- `analyticsClient` - аналитика
- `dashboardClient` - дашборд

### @new-voice/ui

Переиспользуемые UI компоненты.

**Компоненты:**
- Button (6 вариантов, 4 размера)
- Input (text, email, password, file, etc.)
- Textarea (auto-resize)
- Card (Header, Title, Description, Content, Footer)
- Badge (6 вариантов)
- Select (с Radix UI)
- Dialog/Modal (с анимациями)
- Table (responsive, hover states)

**Технологии:**
- React + TypeScript
- TailwindCSS
- Radix UI primitives
- class-variance-authority

## 🎯 Roadmap

- [x] **Phase 1: Подготовка** - Monorepo структура, базовые пакеты
- [x] **Phase 2: UI Kit** - Базовые UI компоненты
- [x] **Phase 3: API Client** - Полная интеграция с бэкендом (готов из Phase 1)
- [ ] **Phase 4: Модуль Skillbases** - Конфигуратор Skillbases
- [ ] **Phase 5: Модуль Campaigns** - Управление кампаниями
- [ ] **Phase 6: Модуль Analytics** - Аналитика и дашборд
- [ ] **Phase 7: Остальные модули** - Calls, Leads, Knowledge Bases
- [ ] **Phase 8: Интеграция** - Сборка всех модулей
- [ ] **Phase 9: Деплой** - Production деплой

## 🔧 Технологии

- **React 18** - UI framework
- **TypeScript 5** - Type safety
- **Vite 5** - Build tool
- **pnpm** - Package manager
- **TailwindCSS** - Styling
- **Axios** - HTTP client
- **date-fns** - Date utilities

## 📝 Соглашения

### Именование

- Файлы компонентов: `PascalCase.tsx`
- Утилиты и хуки: `camelCase.ts`
- Константы: `UPPER_SNAKE_CASE`

### Импорты

```typescript
// Используйте алиасы для импорта пакетов
import { Button } from '@new-voice/ui'
import { skillbasesClient } from '@new-voice/api-client'
import { formatDate } from '@new-voice/shared'
import type { Skillbase } from '@new-voice/types'
```

### Стиль кода

- Используйте `prettier` для форматирования
- Используйте `eslint` для линтинга
- Все компоненты должны быть типизированы
- Избегайте `any`, используйте `unknown` если тип неизвестен

## 🤝 Вклад

1. Создайте feature branch от `frontend-refactor`
2. Сделайте изменения
3. Запустите `pnpm lint` и `pnpm type-check`
4. Создайте Pull Request

## 📄 Лицензия

Proprietary - NEW-VOICE 2.0

---

**Дата создания:** 26 января 2026  
**Версия:** 2.0.0  
**Статус:** Phase 2 Complete ✅

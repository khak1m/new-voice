# 📋 NEW-VOICE 2.0 — План завершения Frontend

**Дата создания:** 29 января 2026  
**Проект:** NEW-VOICE 2.0  
**Цель:** Завершить разработку всех оставшихся frontend модулей

---

## 📊 ТЕКУЩИЙ СТАТУС

### ✅ Что готово (70%)
- ✅ **Monorepo архитектура** — packages структура
- ✅ **UI Kit** — 8 компонентов (Button, Input, Select, Dialog, Table, Card, Badge, Textarea)
- ✅ **API Client** — типизированный клиент с interceptors
- ✅ **Skillbases модуль** — 100% (список, детали, конфигуратор с 5 табами, TTS Preview)
- ✅ **Campaigns модуль** — 100% (список, детали, редактор, routes добавлены)
- ✅ **Calls модуль** — 100% (список, детали с 6 табами, Audio Player, Transcript)
- ✅ **TypeScript типы** — все модели определены
- ✅ **Backend API** — все endpoints работают

### ❌ Что нужно сделать (30%)
- ❌ **Leads модуль** — 0% (API готов, типы готовы, клиент готов)
- ❌ **Knowledge Bases модуль** — 0% (API готов, типы готовы, клиент готов)
- ❌ **Dashboard виджеты** — 0% (сейчас пустые карточки)

---

## 🎯 ПЛАН РАЗРАБОТКИ

### **PHASE 6: Leads Module** 
**Приоритет:** 🔴 CRITICAL  
**Время:** 2-3 часа  
**Статус:** ⏳ Не начато

#### 6.1. Создать структуру модуля
**Файлы:**
```
src/pages/leads/
├── LeadsList.tsx          # Список лидов
├── LeadDetail.tsx         # Детальная страница
├── components/
│   ├── LeadCard.tsx       # Карточка лида
│   ├── LeadStatusBadge.tsx # Бейдж статуса
│   └── LeadEditor.tsx     # Форма редактирования
└── index.ts               # Экспорты

src/schemas/
└── lead-schemas.ts        # Zod схемы валидации
```

#### 6.2. LeadsList.tsx — Список лидов
**Функционал:**
- Таблица с колонками:
  - Name (имя лида)
  - Phone (телефон)
  - Email (email)
  - Status (статус с бейджем)
  - Created (дата создания)
  - Actions (кнопка "View Details")
- Фильтры:
  - По статусу (new, contacted, converted, rejected)
  - По campaign_id (опционально)
  - Поиск по имени/телефону
- Пагинация (skip/limit)
- Кнопка "Export CSV"
- Loading states
- Error handling

**API запросы:**
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['leads', filters],
  queryFn: () => apiClient.leads.list(filters)
})
```

#### 6.3. LeadDetail.tsx — Детальная страница
**Функционал:**
- Информация о лиде:
  - Name, Phone, Email
  - Status (с возможностью изменения)
  - Notes (с возможностью редактирования)
  - Created/Updated timestamps
  - Custom data (JSON поля)
- Связанный звонок (если есть call_id):
  - Ссылка на Call Detail
  - Краткая информация о звонке
- Форма редактирования:
  - Изменение статуса (select)
  - Добавление/редактирование заметок (textarea)
  - Кнопка "Save"

**API запросы:**
```typescript
const { data: lead } = useQuery({
  queryKey: ['leads', id],
  queryFn: () => apiClient.leads.get(id)
})

const updateMutation = useMutation({
  mutationFn: (data) => apiClient.leads.update(id, data),
  onSuccess: () => queryClient.invalidateQueries(['leads'])
})
```

#### 6.4. LeadStatusBadge.tsx — Компонент бейджа
**Статусы и цвета:**
- `new` → синий (blue)
- `contacted` → желтый (yellow)
- `converted` → зеленый (green)
- `rejected` → красный (red)

#### 6.5. Добавить routes в App.tsx
```typescript
<Route path="leads" element={<LeadsList />} />
<Route path="leads/:id" element={<LeadDetail />} />
```

#### 6.6. Добавить в Navigation (MainLayout.tsx)
```typescript
{ name: 'Leads', href: '/leads' }
```

#### 6.7. Git commit & push
```bash
git add .
git commit -m "feat: implement Leads module (Phase 6)"
git push origin master
```

---

### **PHASE 7: Knowledge Bases Module**
**Приоритет:** 🟡 HIGH  
**Время:** 2-3 часа  
**Статус:** ⏳ Не начато

#### 7.1. Создать структуру модуля
**Файлы:**
```
src/pages/knowledge-bases/
├── KnowledgeBasesList.tsx    # Список баз знаний
├── KnowledgeBaseDetail.tsx   # Детальная страница
├── components/
│   ├── KnowledgeBaseCard.tsx       # Карточка базы
│   ├── KnowledgeBaseCreateModal.tsx # Модалка создания
│   ├── DocumentUploader.tsx        # Drag & drop uploader
│   ├── DocumentList.tsx            # Список документов
│   └── SearchPanel.tsx             # Поиск по базе
└── index.ts

src/schemas/
└── knowledge-base-schemas.ts
```

#### 7.2. KnowledgeBasesList.tsx — Список баз знаний
**Функционал:**
- Таблица с колонками:
  - Name (название базы)
  - Description (описание)
  - Documents Count (количество документов)
  - Chunks Count (количество чанков)
  - Created (дата создания)
  - Actions (View, Delete)
- Кнопка "Create Knowledge Base"
- Поиск по названию
- Loading states
- Error handling

**API запросы:**
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['knowledge-bases', companyId],
  queryFn: () => apiClient.knowledgeBases.list({ company_id: companyId })
})
```

#### 7.3. KnowledgeBaseDetail.tsx — Детальная страница
**Функционал:**
- Информация о базе знаний:
  - Name, Description
  - Document count, Chunk count
  - Created/Updated timestamps
  - Settings (chunk_size, chunk_overlap, embedding_model)
- Список документов:
  - Title, Source Type, Chunk Count, Indexed Status
  - Кнопка Delete для каждого документа
- Upload документа:
  - Drag & drop зона
  - Или кнопка "Choose File"
  - Поддержка .txt, .pdf, .docx (опционально)
- Поиск по базе знаний:
  - Input для запроса
  - Slider для top_k (1-10)
  - Кнопка "Search"
  - Результаты с score и content

**API запросы:**
```typescript
// Get KB
const { data: kb } = useQuery({
  queryKey: ['knowledge-bases', id],
  queryFn: () => apiClient.knowledgeBases.get(id)
})

// Get documents
const { data: documents } = useQuery({
  queryKey: ['knowledge-bases', id, 'documents'],
  queryFn: () => apiClient.knowledgeBases.listDocuments(id)
})

// Upload document
const uploadMutation = useMutation({
  mutationFn: (file) => apiClient.knowledgeBases.uploadDocument(id, file)
})

// Search
const searchMutation = useMutation({
  mutationFn: (query) => apiClient.knowledgeBases.search(id, query)
})
```

#### 7.4. DocumentUploader.tsx — Drag & Drop компонент
**Функционал:**
- Drag & drop зона
- Показывать preview файла
- Валидация типа файла
- Progress bar при загрузке
- Success/Error сообщения

#### 7.5. SearchPanel.tsx — Поиск по базе
**Функционал:**
- Input для запроса
- Slider для top_k
- Кнопка "Search"
- Результаты:
  - Content (текст чанка)
  - Score (релевантность)
  - Title (название документа)

#### 7.6. Добавить routes в App.tsx
```typescript
<Route path="knowledge-bases" element={<KnowledgeBasesList />} />
<Route path="knowledge-bases/:id" element={<KnowledgeBaseDetail />} />
```

#### 7.7. Добавить в Navigation (MainLayout.tsx)
```typescript
{ name: 'Knowledge Bases', href: '/knowledge-bases' }
```

#### 7.8. Git commit & push
```bash
git add .
git commit -m "feat: implement Knowledge Bases module (Phase 7)"
git push origin master
```

---

### **PHASE 8: Dashboard Widgets**
**Приоритет:** 🟡 MEDIUM  
**Время:** 1-2 часа  
**Статус:** ⏳ Не начато

#### 8.1. Обновить Dashboard.tsx
**Убрать:**
- "Coming soon" карточки

**Добавить:**
- Реальные метрики с API

#### 8.2. Создать компоненты
**Файлы:**
```
src/pages/dashboard/
├── components/
│   ├── StatCard.tsx       # Карточка метрики
│   ├── CallsChart.tsx     # График звонков (опционально)
│   └── LeadsChart.tsx     # График лидов (опционально)
└── index.ts
```

#### 8.3. StatCard.tsx — Карточка метрики
**Props:**
```typescript
interface StatCardProps {
  title: string
  value: number | string
  icon?: React.ReactNode
  trend?: {
    value: number
    isPositive: boolean
  }
  link?: string
}
```

**Пример:**
```tsx
<StatCard
  title="Total Skillbases"
  value={12}
  icon={<BotIcon />}
  link="/skillbases"
/>
```

#### 8.4. Dashboard метрики
**Карточки:**
1. **Total Skillbases**
   - API: `GET /api/skillbases?company_id=...`
   - Показать: количество skillbases
   - Ссылка: `/skillbases`

2. **Active Campaigns**
   - API: `GET /api/campaigns?company_id=...&status=active`
   - Показать: количество активных кампаний
   - Ссылка: `/campaigns`

3. **Total Calls (Today)**
   - API: `GET /api/calls?company_id=...&date=today`
   - Показать: количество звонков за сегодня
   - Ссылка: `/calls`

4. **New Leads**
   - API: `GET /api/leads?company_id=...&status=new`
   - Показать: количество новых лидов
   - Ссылка: `/leads`

5. **Knowledge Bases**
   - API: `GET /api/knowledge-bases?company_id=...`
   - Показать: количество баз знаний
   - Ссылка: `/knowledge-bases`

#### 8.5. Графики (опционально)
**CallsChart.tsx:**
- График звонков за последние 7 дней
- Использовать recharts или chart.js
- API: `GET /api/analytics/calls-per-day?days=7`

**LeadsChart.tsx:**
- Pie chart лидов по статусам
- API: `GET /api/leads/stats/summary`

#### 8.6. Git commit & push
```bash
git add .
git commit -m "feat: implement Dashboard widgets (Phase 8)"
git push origin master
```

---

### **PHASE 9: Testing & Polish**
**Приоритет:** 🔴 CRITICAL  
**Время:** 1-2 часа  
**Статус:** ⏳ Не начато

#### 9.1. Проверить все модули в браузере
- [ ] Leads List работает
- [ ] Lead Detail работает
- [ ] Knowledge Bases List работает
- [ ] Knowledge Base Detail работает
- [ ] Document Upload работает
- [ ] Search работает
- [ ] Dashboard показывает метрики

#### 9.2. Проверить TypeScript компиляцию
```bash
cd new-voice-frontend-v2
pnpm typecheck
```

#### 9.3. Проверить responsive design
- [ ] Mobile (375px)
- [ ] Tablet (768px)
- [ ] Desktop (1024px+)

#### 9.4. Проверить loading states
- [ ] Все списки показывают loading
- [ ] Все формы показывают loading при submit

#### 9.5. Проверить error handling
- [ ] API errors показываются пользователю
- [ ] Network errors обрабатываются
- [ ] 404 errors обрабатываются

#### 9.6. Финальный commit
```bash
git add .
git commit -m "chore: final polish and testing (Phase 9)"
git push origin master
```

---

## 📈 ОЦЕНКА ВРЕМЕНИ

| Phase | Описание | Время | Приоритет | Статус |
|-------|----------|-------|-----------|--------|
| **Phase 6** | Leads Module | 2-3 часа | 🔴 CRITICAL | ⏳ Не начато |
| **Phase 7** | Knowledge Bases Module | 2-3 часа | 🟡 HIGH | ⏳ Не начато |
| **Phase 8** | Dashboard Widgets | 1-2 часа | 🟡 MEDIUM | ⏳ Не начато |
| **Phase 9** | Testing & Polish | 1-2 часа | 🔴 CRITICAL | ⏳ Не начато |
| **ИТОГО** | | **6-10 часов** | | |

---

## 🎯 ПОРЯДОК ВЫПОЛНЕНИЯ

### Рекомендуемый порядок:
1. **Phase 6: Leads Module** (самый важный для бизнеса)
2. **Phase 7: Knowledge Bases Module** (важный для функциональности)
3. **Phase 8: Dashboard Widgets** (улучшает UX)
4. **Phase 9: Testing & Polish** (обязательно перед деплоем)

### Альтернативный порядок (если нужно быстро показать результат):
1. **Phase 8: Dashboard Widgets** (быстро, видимый результат)
2. **Phase 6: Leads Module** (критичный функционал)
3. **Phase 7: Knowledge Bases Module** (дополнительный функционал)
4. **Phase 9: Testing & Polish** (финальная проверка)

---

## 🔧 ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ

### Стандарты кода (из KIRO_SYSTEM_PROMPT.md):
1. **TypeScript** — всегда типизировать, никогда не использовать `any`
2. **TanStack Query** — для всех API запросов
3. **react-hook-form + Zod** — для всех форм
4. **TailwindCSS** — только TailwindCSS, никаких inline styles
5. **Функциональные компоненты** — никаких class components
6. **Git workflow** — commit и push после каждой завершенной фазы

### Структура компонентов:
```typescript
// ✅ Правильно
interface Props {
  title: string
  onClose: () => void
}

export function MyComponent({ title, onClose }: Props) {
  return <div className="flex items-center gap-4">...</div>
}
```

### API запросы:
```typescript
// ✅ Правильно
const { data, isLoading, error } = useQuery({
  queryKey: ['resource', id],
  queryFn: () => apiClient.resource.get(id)
})
```

### Формы:
```typescript
// ✅ Правильно
const schema = z.object({
  name: z.string().min(1, 'Required'),
  email: z.string().email('Invalid email')
})

const form = useForm<z.infer<typeof schema>>({
  resolver: zodResolver(schema)
})
```

---

## 📝 ЧЕКЛИСТ ПЕРЕД НАЧАЛОМ КАЖДОЙ ФАЗЫ

- [ ] Прочитать описание фазы
- [ ] Понять требования
- [ ] Проверить что API endpoints работают
- [ ] Проверить что типы определены
- [ ] Проверить что API клиент готов
- [ ] Начать с создания структуры файлов
- [ ] Работать шаг за шагом
- [ ] Тестировать в браузере после каждого компонента
- [ ] Commit и push после завершения фазы

---

## 🚀 ГОТОВНОСТЬ К СТАРТУ

### Что уже готово:
- ✅ Backend API работает (http://77.233.212.58:8000)
- ✅ API клиенты готовы (leads, knowledge-bases)
- ✅ TypeScript типы определены
- ✅ UI Kit готов (Button, Input, Select, Dialog, Table, Card, Badge, Textarea)
- ✅ Monorepo структура настроена
- ✅ TanStack Query настроен
- ✅ Примеры других модулей есть (Skillbases, Campaigns, Calls)

### Можно начинать прямо сейчас! 🎉

---

## 📞 КОНТАКТЫ И РЕСУРСЫ

- **Backend API:** http://77.233.212.58:8000
- **API Docs:** http://77.233.212.58:8000/docs
- **Frontend Dev:** http://localhost:5173
- **GitHub:** https://github.com/khak1m/new-voice
- **Workspace:** `C:\Users\Dmitriy\Desktop\new voice\new-voice-frontend-v2`

---

**Создано:** 29 января 2026  
**Автор:** Kiro AI Assistant  
**Для:** Дмитрий (NEW-VOICE 2.0 Project)

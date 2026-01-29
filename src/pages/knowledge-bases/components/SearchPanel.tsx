import { useState } from 'react'
import { Button, Input, Card } from '@new-voice/ui'
import type { SearchResult } from '@new-voice/types'

interface SearchPanelProps {
  onSearch: (query: string, topK: number) => void
  results?: SearchResult[]
  isSearching: boolean
}

export function SearchPanel({ onSearch, results, isSearching }: SearchPanelProps) {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(3)

  const handleSearch = () => {
    if (query.trim()) {
      onSearch(query, topK)
    }
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Поиск по базе знаний</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Запрос
          </label>
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Введите поисковый запрос..."
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Количество результатов: {topK}
          </label>
          <input
            type="range"
            min="1"
            max="10"
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="w-full"
          />
        </div>

        <Button onClick={handleSearch} disabled={isSearching || !query.trim()} className="w-full">
          {isSearching ? 'Поиск...' : 'Искать'}
        </Button>
      </div>

      {results && results.length > 0 && (
        <div className="mt-6 space-y-4">
          <h4 className="font-semibold">Результаты:</h4>
          {results.map((result, index) => (
            <Card key={index} className="p-4 bg-gray-50">
              <div className="flex items-start justify-between mb-2">
                <div className="text-sm font-medium text-gray-700">
                  {result.title || 'Без названия'}
                </div>
                <div className="text-xs text-gray-500">
                  Score: {result.score.toFixed(3)}
                </div>
              </div>
              <p className="text-sm text-gray-600 whitespace-pre-wrap">
                {result.content}
              </p>
            </Card>
          ))}
        </div>
      )}

      {results && results.length === 0 && (
        <div className="mt-6 text-center text-gray-500">
          Ничего не найдено
        </div>
      )}
    </Card>
  )
}

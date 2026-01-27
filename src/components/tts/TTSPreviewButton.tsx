import { useState, useRef, useCallback } from 'react'
import { ttsClient } from '@new-voice/api-client'
import { toast } from 'sonner'

interface TTSPreviewButtonProps {
  text: string
  voiceId?: string
  language?: string
  disabled?: boolean
  className?: string
  size?: 'sm' | 'md'
}

export function TTSPreviewButton({
  text,
  voiceId,
  language = 'ru',
  disabled = false,
  className = '',
  size = 'sm',
}: TTSPreviewButtonProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const audioUrlRef = useRef<string | null>(null)

  const cleanup = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.src = ''
      audioRef.current = null
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current)
      audioUrlRef.current = null
    }
  }, [])

  const handleClick = async () => {
    // If already playing, stop
    if (isPlaying) {
      cleanup()
      setIsPlaying(false)
      return
    }

    // Validate text
    if (!text || text.trim().length === 0) {
      toast.error('Enter text to preview')
      return
    }

    if (text.length > 500) {
      toast.error('Text is too long (max 500 characters)')
      return
    }

    setIsLoading(true)

    try {
      // Get audio blob from API
      const audioBlob = await ttsClient.preview({
        text: text.trim(),
        voice_id: voiceId,
        language,
      })

      // Create object URL
      const audioUrl = URL.createObjectURL(audioBlob)
      audioUrlRef.current = audioUrl

      // Create audio element and play
      const audio = new Audio(audioUrl)
      audioRef.current = audio

      audio.onended = () => {
        setIsPlaying(false)
        cleanup()
      }

      audio.onerror = () => {
        setIsPlaying(false)
        cleanup()
        toast.error('Failed to play audio')
      }

      await audio.play()
      setIsPlaying(true)
    } catch (error) {
      console.error('TTS Preview Error:', error)
      toast.error('Failed to generate audio preview')
      cleanup()
    } finally {
      setIsLoading(false)
    }
  }

  const isDisabled = disabled || !text || text.trim().length === 0

  const sizeClasses = size === 'sm' 
    ? 'w-8 h-8'
    : 'w-10 h-10'

  const iconSize = size === 'sm' ? 'w-4 h-4' : 'w-5 h-5'

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isDisabled || isLoading}
      className={`
        ${sizeClasses}
        flex items-center justify-center rounded-full
        transition-all duration-200
        ${isPlaying 
          ? 'bg-red-100 text-red-600 hover:bg-red-200' 
          : 'bg-indigo-100 text-indigo-600 hover:bg-indigo-200'
        }
        disabled:opacity-50 disabled:cursor-not-allowed
        focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1
        ${className}
      `}
      title={isPlaying ? 'Stop' : 'Preview voice'}
    >
      {isLoading ? (
        <svg className={`${iconSize} animate-spin`} fill="none" viewBox="0 0 24 24">
          <circle 
            className="opacity-25" 
            cx="12" 
            cy="12" 
            r="10" 
            stroke="currentColor" 
            strokeWidth="4" 
          />
          <path 
            className="opacity-75" 
            fill="currentColor" 
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" 
          />
        </svg>
      ) : isPlaying ? (
        <svg className={iconSize} fill="currentColor" viewBox="0 0 24 24">
          <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
        </svg>
      ) : (
        <svg className={iconSize} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" 
          />
        </svg>
      )}
    </button>
  )
}

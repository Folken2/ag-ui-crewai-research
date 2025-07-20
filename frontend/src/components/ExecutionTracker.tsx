"use client"

import { useState, useEffect } from "react"

interface ExecutionEvent {
  type: string
  data: {
    message: string
    agent_role?: string
    tool_name?: string
    model?: string
    query?: string
    status?: string
    crew_name?: string
    execution_time?: number
    token_usage?: {
      total_tokens?: number
      prompt_tokens?: number
      completion_tokens?: number
    }
  }
  timestamp: string
  agent_id?: string
  session_id?: string
}

interface ExecutionTrackerProps {
  events: ExecutionEvent[]
  isProcessing: boolean
}

export function ExecutionTracker({ events, isProcessing }: ExecutionTrackerProps) {
  const [visibleEvents, setVisibleEvents] = useState<ExecutionEvent[]>([])

  useEffect(() => {
    // Add new events with a slight delay for animation
    events.forEach((event, index) => {
      setTimeout(() => {
        setVisibleEvents(prev => {
          // Avoid duplicates
          const exists = prev.some(e => 
            e.timestamp === event.timestamp && 
            e.type === event.type && 
            e.data.message === event.data.message
          )
          return exists ? prev : [...prev, event]
        })
      }, index * 50)
    })
  }, [events])

  useEffect(() => {
    // Clear events when not processing
    if (!isProcessing) {
      setTimeout(() => {
        setVisibleEvents([])
      }, 2000) // Keep events visible for 2 seconds after completion
    }
  }, [isProcessing])

  if (!isProcessing && visibleEvents.length === 0) {
    return null
  }

  const getEventIcon = (type: string) => {
    switch (type) {
      case "CREW_STARTED":
        return "🚀"
      case "CREW_COMPLETED":
        return "✅"
      case "CREW_ERROR":
        return "❌"
      case "AGENT_STARTED":
        return "🤖"
      case "AGENT_COMPLETED":
        return "✅"
      case "AGENT_ERROR":
        return "❌"
      case "TOOL_STARTED":
        return "🔍"
      case "TOOL_COMPLETED":
        return "✅"
      case "TOOL_ERROR":
        return "❌"
      case "LLM_STARTED":
        return "🧠"
      case "LLM_COMPLETED":
        return "✅"
      case "LLM_ERROR":
        return "❌"
      case "TASK_STARTED":
        return "📋"
      case "TASK_COMPLETED":
        return "✅"
      case "TASK_FAILED":
        return "❌"
      default:
        return "⚡"
    }
  }

  const getEventColor = (type: string) => {
    if (type.includes("ERROR") || type.includes("FAILED")) {
      return "text-red-500 border-red-200 bg-red-50"
    }
    if (type.includes("COMPLETED")) {
      return "text-green-600 border-green-200 bg-green-50"
    }
    if (type.includes("STARTED")) {
      return "text-blue-600 border-blue-200 bg-blue-50 animate-pulse"
    }
    return "text-gray-600 border-gray-200 bg-gray-50"
  }

  const formatEventMessage = (event: ExecutionEvent) => {
    const { data } = event
    let message = data.message

    // Add additional context for certain events
    if (data.tool_name && data.query) {
      message = `${message.split(' with query')[0]} with query: "${data.query}"`
    }
    
    if (data.execution_time) {
      message += ` (${data.execution_time.toFixed(2)}s)`
    }

    if (data.token_usage?.total_tokens) {
      message += ` • ${data.token_usage.total_tokens} tokens`
    }

    return message
  }

  return (
    <div className="mb-4 space-y-2">
      <div className="text-sm font-medium text-gray-700 mb-2">
        🔄 Execution Status
      </div>
      
      <div className="glass-card border border-gray-200 rounded-lg p-4 max-h-48 overflow-y-auto">
        <div className="space-y-2">
          {visibleEvents.map((event, index) => (
            <div
              key={`${event.type}-${event.timestamp}-${event.agent_id || 'no-agent'}-${index}`}
              className={`flex items-start space-x-3 p-2 rounded-md border transition-all duration-300 transform ${getEventColor(event.type)} animate-in slide-in-from-left-2`}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <span className="text-lg flex-shrink-0 mt-0.5">
                {getEventIcon(event.type)}
              </span>
              
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium break-words">
                  {formatEventMessage(event)}
                </div>
                
                {/* Additional details for certain events */}
                {event.data.agent_role && (
                  <div className="text-xs text-gray-500 mt-1">
                    Agent: {event.data.agent_role}
                  </div>
                )}
                
                {event.data.tool_name && !event.data.query && (
                  <div className="text-xs text-gray-500 mt-1">
                    Tool: {event.data.tool_name}
                  </div>
                )}
                
                {event.data.model && (
                  <div className="text-xs text-gray-500 mt-1">
                    Model: {event.data.model}
                  </div>
                )}
              </div>
              
              <div className="text-xs text-gray-400 flex-shrink-0">
                {new Date(event.timestamp).toLocaleTimeString([], { 
                  hour: '2-digit', 
                  minute: '2-digit',
                  second: '2-digit'
                })}
              </div>
            </div>
          ))}
          
          {isProcessing && (
            <div className="flex items-center space-x-2 p-2 text-blue-600">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-ping"></div>
              <span className="text-sm font-medium"></span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 
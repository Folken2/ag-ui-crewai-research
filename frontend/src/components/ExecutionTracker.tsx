"use client"

import { useState, useEffect } from "react"

interface ExecutionEvent {
  type: string
  data: {
    message: string
    agent_role?: string
    tool_name?: string
    tool_query?: string
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

  const formatEventMessage = (event: ExecutionEvent) => {
    const { data } = event
    let message = data.message

    // Handle tool usage events with the specific structure requested
    if (event.type === "TOOL_STARTED" && data.tool_query) {
      message = `🌐 Searching for: ${data.tool_query}`
    } else if (event.type === "TOOL_COMPLETED" && data.tool_query) {
      message = `Found results for: ${data.tool_query}`
    } else if (event.type === "TOOL_ERROR" && data.tool_query) {
      message = `Error searching for: ${data.tool_query}`
    }
    
    // Add additional context for certain events (but not for tool events)
    if (data.tool_name && data.query && !event.type.startsWith("TOOL_")) {
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
      
      <div className="glass-card border border-gray-200 rounded-lg p-4 max-h-48 overflow-y-auto bg-gradient-to-br from-white/80 to-gray-50/50 backdrop-blur-sm">
        <div className="space-y-2">
          {visibleEvents.map((event, index) => (
            <div
              key={`${event.type}-${event.timestamp}-${event.agent_id || 'no-agent'}-${index}`}
              className="flex items-start space-x-3 p-2 rounded-md border transition-all duration-500 transform text-gray-600 border-gray-200 bg-gray-50 hover:scale-105"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Loading spinner for STARTED events */}
              {event.type.includes("STARTED") && (
                <div className="flex-shrink-0 mt-0.5 relative">
                  <div className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                </div>
              )}
              
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
            <div className="flex items-center space-x-3 p-3 text-blue-600 bg-blue-50/50 rounded-md border border-blue-200 animate-pulse">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
              <span className="text-sm font-medium opacity-80">Processing...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 
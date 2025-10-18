"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { useToken } from '../contexts/TokenContext'

interface Source {
  url: string
  title: string
  image_url?: string
  snippet?: string
}

interface Message {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
  sources?: Source[]
  isSearching?: boolean
}

interface ChatState {
  processing: boolean
  currentAction: string
  conversationHistory: unknown[]
  sessionEnded?: boolean
  lastEventUpdate?: number
}

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

// Utility function to safely handle URLs
const getSafeUrl = (url: string) => {
  try {
    new URL(url);
    return url;
  } catch {
    return '#';
  }
}



const isValidUrl = (url: string) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

const extractDomain = (url: string) => {
  try {
    const domain = new URL(url).hostname;
    // Remove www. if present
    return domain.replace(/^www\./, '');
  } catch {
    return 'Source';
  }
}

export function ChatInterface() {
  const { token } = useToken()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false);
  const [eventMessages, setEventMessages] = useState<string[]>([]);
  const [eventMessageId, setEventMessageId] = useState<number>(0);
  const [chatState, setChatState] = useState<ChatState>({
    processing: false,
    currentAction: "Ready to assist",
    conversationHistory: [],
    sessionEnded: false,
    lastEventUpdate: Date.now()
  })
  const [showClearDialog, setShowClearDialog] = useState(false)
  const [executionEvents, setExecutionEvents] = useState<ExecutionEvent[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleNewChat = useCallback(() => {
    if (messages.length > 0) {
      setShowClearDialog(true)
    }
  }, [messages.length])

  // Keyboard shortcut for new chat (Ctrl+N or Cmd+N)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault()
        handleNewChat()
      }
      // ESC to close dialog
      if (e.key === 'Escape' && showClearDialog) {
        setShowClearDialog(false)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [showClearDialog, messages.length, handleNewChat])

  const clearChat = async () => {
    try {
      // Call backend to start new chat session
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      await fetch(`${backendUrl}/flow/new-chat`, {
        method: 'POST',
        headers,
      });
    } catch (error) {
      console.error('Error starting new chat session:', error);
    }

    // Clear frontend state
    setMessages([])
    setIsLoading(false)
    setExecutionEvents([])
    setChatState({
      processing: false,
      currentAction: "Ready to assist",
      conversationHistory: [],
      sessionEnded: false,
      lastEventUpdate: Date.now()
    })
    setShowClearDialog(false)
  }

  const handleSSEMessage = useCallback((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);
      
      if (data.type === 'TEXT_MESSAGE_DELTA') {
        // Handle streaming text content
        const content = data.data?.content;
        if (content) {
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.role === 'assistant') {
              // Update existing assistant message
              return prev.map((msg, index) => 
                index === prev.length - 1 
                  ? { ...msg, content: msg.content + content }
                  : msg
              );
            } else {
              // Create new assistant message
              return [...prev, { 
                id: Date.now().toString(),
                role: 'assistant', 
                content: content,
                timestamp: new Date()
              }];
            }
          });
        }
      } else if (data.type === 'SOURCES_UPDATE') {
        // Handle sources update
        const sources = data.data?.sources;
        if (sources) {
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.role === 'assistant') {
              return prev.map((msg, index) => 
                index === prev.length - 1 
                  ? { ...msg, sources: sources }
                  : msg
              );
            }
            return prev;
          });
        }
      } else if (data.type === 'EXECUTION_STATUS' || data.type === 'AGENT_STATUS' || data.type === 'TASK_STATUS' || 
                 data.type === 'TOOL_USAGE' || data.type === 'LLM_STATUS') {
        // Handle real-time execution events (agent, thoughts, tools)
        const message = data.data?.message;
        if (message) {
                  // Add a small delay to ensure proper sequencing
        setTimeout(() => {
          setEventMessages(prev => {
            // Only add if it's not already in the list
            if (!prev.includes(message)) {
              console.log('Adding event:', message); // Debug log
              return [...prev, message];
            }
            return prev;
          });
          setEventMessageId(prev => prev + 1);
        }, 500); // 500ms delay for natural progression
        }
      } else if (data.type === 'RUN_FINISHED') {
        // Clear the event messages when execution completes
        setEventMessages([]);
        setIsLoading(false);
      } else if (data.type === 'RUN_ERROR' || data.type === 'AGENT_ERROR' || data.type === 'TASK_ERROR') {
        setEventMessages([]);
        setIsLoading(false);
        setMessages(prev => [...prev, { 
          id: Date.now().toString(),
          role: 'assistant', 
          content: 'Sorry, there was an error processing your request.',
          timestamp: new Date()
        }]);
      }
    } catch (error) {
      console.error('Error parsing SSE message:', error);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { 
      id: Date.now().toString(),
      role: 'user', 
      content: userMessage,
      timestamp: new Date()
    }]);
    setIsLoading(true);
    setEventMessages([]); // Clear any previous event messages

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers,
        body: JSON.stringify({ messages: [
          ...messages.map(m => ({ role: m.role, content: m.content })),
          { role: 'user', content: userMessage }
        ] }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              setIsLoading(false);
              setEventMessages([]);
              return;
            }
            try {
              const parsed = JSON.parse(data);
              handleSSEMessage({ data: JSON.stringify(parsed) } as MessageEvent);
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setIsLoading(false);
      setEventMessages([]);
      setMessages(prev => [...prev, { 
        id: Date.now().toString(),
        role: 'assistant', 
        content: 'Sorry, there was an error processing your request.',
        timestamp: new Date()
      }]);
    }
  };

  const sendMessage = (content: string) => {
    setInput(content);
    // Use setTimeout to ensure state is updated before submission
    setTimeout(() => {
      const formEvent = new Event('submit', { bubbles: true, cancelable: true });
      const form = document.querySelector('form');
      if (form) {
        form.dispatchEvent(formEvent);
      }
    }, 0);
  }

  const handleQuickAction = (text: string) => {
    sendMessage(text)
  }

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      {/* Header */}
      <header className="glass-card border-b border-border px-6 py-4 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-amber-400 flex items-center justify-center font-bold text-lg shadow-lg">
              <svg className="w-5 h-5 text-amber-800" fill="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="2" />
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">
                AI Research Assistant
              </h1>
              <p className="text-sm text-muted-foreground">CrewAI + AG-UI Protocol Implementation</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-3">
            {/* New Chat Button - Only show when there are messages */}
            {messages.length > 0 && (
              <button
                onClick={handleNewChat}
                className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-amber-400 hover:bg-amber-500 text-white font-medium transition-all duration-200 shadow-md hover:shadow-lg hover:scale-105"
                title="Start a new conversation (Ctrl+N)"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <span>New Chat</span>
              </button>
            )}
            
          </div>
        </div>
      </header>

      {/* Chat Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          // Welcome Screen
          <div className="h-full flex items-center justify-center p-6">
            <div className="text-center max-w-6xl mx-auto">
              <div className="mb-12 animate-fade-in">
                <h2 className="text-5xl font-bold text-foreground mb-4">
                  AI Research Assistant
                </h2>
                <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed mb-8">
                  A cutting-edge implementation showcasing <span className="font-semibold text-foreground">CrewAI</span> for 
                  orchestrated AI agents and <span className="font-semibold text-foreground">AG-UI Protocol</span> for 
                  real-time streaming interactions.
                </p>
                
                {/* Technical Badges */}
                <div className="flex flex-wrap justify-center gap-4 mb-12">
                  <div className="glass-card px-5 py-3 rounded-full border border-amber-200">
                    <div className="flex items-center space-x-2">
                      <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <rect x="9" y="3" width="6" height="6" rx="1" strokeWidth={2}/>
                        <rect x="3" y="15" width="6" height="6" rx="1" strokeWidth={2}/>
                        <rect x="15" y="15" width="6" height="6" rx="1" strokeWidth={2}/>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v6M9 15l3-3M15 15l-3-3"/>
                      </svg>
                      <span className="text-base font-semibold text-foreground">CrewAI</span>
                    </div>
                  </div>
                  <div className="glass-card px-5 py-3 rounded-full border border-amber-200">
                    <div className="flex items-center space-x-2">
                      <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      <span className="text-base font-semibold text-foreground">AG-UI Protocol</span>
                    </div>
                  </div>
                  <div className="glass-card px-5 py-3 rounded-full border border-amber-200">
                    <div className="flex items-center space-x-2">
                      <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"/>
                      </svg>
                      <span className="text-base font-semibold text-foreground">Real-time Streaming</span>
                    </div>
                  </div>
                  <div className="glass-card px-5 py-3 rounded-full border border-amber-200">
                    <div className="flex items-center space-x-2">
                      <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span className="text-base font-semibold text-foreground">Source Attribution</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex justify-center">
                <button 
                  onClick={() => handleQuickAction("Research the latest developments in quantum computing")}
                  className="group glass-card p-4 text-left rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-300"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-amber-400 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </div>
                    <div className="font-bold text-base text-foreground">Search</div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        ) : (
          // Chat Messages
          <div className="max-w-6xl mx-auto p-6 space-y-4">
            {messages.map((message, index) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
                <div className={`max-w-[85%] rounded-2xl transition-all duration-300 ${
                  message.role === 'user' 
                    ? 'bg-amber-400 text-white rounded-br-md'
                    : 'glass-card rounded-bl-md'
                }`}>
                  <div className="px-4 py-2">
                    {/* Enhanced Sources Display */}
                    {message.role === 'assistant' && !message.isSearching && message.content && message.sources && message.sources.length > 0 && (
                      <div className="mb-4 pb-4 border-b border-border/50">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            <div className="w-5 h-5 bg-amber-500 rounded-md flex items-center justify-center">
                              <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                              </svg>
                            </div>
                            <span className="text-sm font-semibold text-foreground">Sources</span>
                            <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-full">
                              {message.sources.length} found
                            </span>
                          </div>
                        </div>
                        <div className="flex gap-3 overflow-x-auto pb-1 [&::-webkit-scrollbar]:h-2 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-amber-300/30 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-amber-300/50">
                          {message.sources.map((source, index) => (
                            <a
                              key={`${source.url}-${index}`}
                              href={getSafeUrl(source.url)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="group relative overflow-hidden glass-card hover:shadow-lg p-3 rounded-xl border border-border/50 hover:border-amber-300/50 transition-all duration-300 hover:scale-[1.02] block flex-shrink-0 w-50"
                              onClick={(e) => {
                                if (!isValidUrl(source.url)) {
                                  e.preventDefault();
                                }
                              }}
                            >

                              
                              {/* Content */}
                              <div className="space-y-2">
                                {/* Image if available */}
                                {source.image_url && (
                                  <div className="relative w-full h-16 mb-2 rounded-lg overflow-hidden">
                                    <img
                                      src={source.image_url}
                                      alt={source.title}
                                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                                      onError={(e) => {
                                        // Hide image on error
                                        e.currentTarget.style.display = 'none';
                                      }}
                                    />
                                    {/* Image overlay for better text readability */}
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
                                  </div>
                                )}
                                
                                {/* Source name/publisher on top (like Perplexity) */}
                                <div className="text-xs text-muted-foreground font-medium">
                                  {extractDomain(source.url)}
                                </div>
                                
                                {/* Title below source name */}
                                <div className="text-sm font-semibold text-foreground group-hover:text-amber-600 line-clamp-2 leading-tight transition-colors pr-6">
                                  {source.title}
                                </div>
                                
                                {/* Snippet if available */}
                                {source.snippet && (
                                  <div className="text-xs text-muted-foreground line-clamp-2 leading-tight">
                                    {source.snippet}
                                  </div>
                                )}
                              </div>
                              
                              {/* Hover effect overlay */}
                              <div className="absolute inset-0 bg-gradient-to-r from-amber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl"></div>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Real-time execution status - shown instead of generic "Searching..." */}
                    {message.role === 'assistant' && chatState.processing && index === messages.length - 1 && (
                      <div className="space-y-3 mb-4" key={chatState.lastEventUpdate}>
                        {executionEvents.length > 0 ? (
                          executionEvents.slice(-3).map((event, eventIndex) => (
                            <div
                              key={`${event.type}-${event.timestamp}-${event.agent_id || eventIndex}`}
                              className="flex items-center space-x-3 text-sm animate-fade-in"
                              style={{ animationDelay: `${eventIndex * 200}ms` }}
                            >
                              <div className="w-2 h-2 bg-amber-400 rounded-full animate-ping"></div>
                              <span className="text-amber-600 font-medium">
                                {event.data.message}
                              </span>
                            </div>
                          ))
                        ) : (
                          <div className="flex items-center space-x-3">
                            <div className="w-5 h-5 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></div>
                            <span className="text-sm text-amber-500 font-medium">
                              {message.isSearching ? "Initializing research..." : ""}
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Enhanced message content */}
                    {message.content && (
                      <div className="max-w-none text-foreground leading-relaxed">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          rehypePlugins={[rehypeRaw]}
                          components={{
                            h1: ({children}) => <h1 className="text-xl font-bold text-foreground mb-4 mt-6 first:mt-0 border-b border-gray-300 pb-2">{children}</h1>,
                            h2: ({children}) => <h2 className="text-lg font-semibold text-foreground mb-3 mt-5 first:mt-0">{children}</h2>,
                            h3: ({children}) => <h3 className="text-base font-medium text-foreground mb-2 mt-4 first:mt-0">{children}</h3>,
                            p: ({children}) => <p className="text-foreground mb-4 last:mb-0 leading-relaxed text-[15px]">{children}</p>,
                            ul: ({children}) => <ul className="list-none space-y-2 mb-4 last:mb-0">{children}</ul>,
                            ol: ({children}) => <ol className="list-decimal list-inside space-y-2 mb-4 last:mb-0 ml-4">{children}</ol>,
                            li: ({children}) => (
                              <li className="text-foreground leading-relaxed flex items-start text-[15px] mb-2">
                                <span className="text-gray-500 mr-3 mt-2 flex-shrink-0 w-2 h-2 rounded-full bg-gray-500"></span>
                                <span className="flex-1">{children}</span>
                              </li>
                            ),
                            strong: ({children}) => <strong className="font-semibold text-foreground">{children}</strong>,
                            em: ({children}) => <em className="italic text-foreground text-muted-foreground">{children}</em>,
                            code: ({children}) => <code className="bg-muted px-2 py-1 rounded-md text-sm font-mono text-foreground border border-border/50">{children}</code>,
                            pre: ({children}) => <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm font-mono text-foreground mb-4 border border-border/50 shadow-sm">{children}</pre>,
                            blockquote: ({children}) => (
                              <blockquote className="border-l-4 border-gray-300 pl-4 italic text-muted-foreground mb-4 bg-gray-50 dark:bg-gray-900/10 py-3 rounded-r-lg">
                                {children}
                              </blockquote>
                            ),
                            a: ({href, children}) => (
                              <a 
                                href={href} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-foreground underline font-medium hover:no-underline hover:bg-gray-100 dark:hover:bg-gray-800 px-1 rounded transition-colors"
                              >
                                {children}
                              </a>
                            ),
                            // Handle tables
                            table: ({children}) => (
                              <div className="overflow-x-auto my-4">
                                <table className="min-w-full border border-border rounded-lg overflow-hidden">
                                  {children}
                                </table>
                              </div>
                            ),
                            th: ({children}) => (
                              <th className="bg-muted px-4 py-2 text-left font-semibold text-foreground border-b border-border">
                                {children}
                              </th>
                            ),
                            td: ({children}) => (
                              <td className="px-4 py-2 text-foreground border-b border-border">
                                {children}
                              </td>
                            ),
                            // Handle horizontal rules
                            hr: () => (
                              <hr className="my-6 border-t border-border" />
                            ),
                            // Handle h4 headers
                            h4: ({children}) => <h4 className="text-sm font-medium text-foreground mb-2 mt-3 first:mt-0">{children}</h4>,
                            
                          }}
                        >
                          {message.content.replace(/##\s*##/g, '##')}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Real-time Execution Status - Shows all internal process steps */}
            {isLoading && eventMessages.length > 0 && (
              <div className="max-w-6xl mx-auto px-6 py-3 space-y-2">
                {eventMessages.map((message, index) => (
                  <div 
                    key={`event-${eventMessageId}-${index}-${message.substring(0, 20)}`}
                    className={`flex items-center space-x-3 text-sm animate-fade-in ${
                      index === eventMessages.length - 1 
                        ? 'text-amber-600 font-semibold' 
                        : 'text-muted-foreground'
                    }`}
                    style={{ 
                      animation: 'fadeIn 0.2s ease-in-out'
                    }}
                  >
                    <div className={`w-2 h-2 rounded-full ${
                      index === eventMessages.length - 1 
                        ? 'bg-amber-500 animate-pulse' 
                        : 'bg-amber-400'
                    }`}></div>
                    <span className="font-medium">{message}</span>
                    {index === eventMessages.length - 1 && (
                      <div className="w-3 h-3 border-2 border-amber-500 border-t-transparent rounded-full animate-spin ml-2"></div>
                    )}
                  </div>
                ))}
              </div>
            )}
            
            {/* Loading Spinner - Shows when loading but no specific event messages */}
            {isLoading && eventMessages.length === 0 && (
              <div className="max-w-6xl mx-auto px-6 py-3">
                <div className="flex items-center space-x-3 text-sm text-muted-foreground">
                  <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></div>
                  <span className="font-medium"></span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Chat Input */}
      <footer className="glass-card border-t border-border p-6 sticky bottom-0">
        <div className="max-w-6xl mx-auto">
          <form onSubmit={handleSubmit}>
            <ChatInput onSend={sendMessage} isLoading={isLoading} />
          </form>
        </div>
      </footer>

      {/* Confirmation Dialog */}
      {showClearDialog && (
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white dark:bg-zinc-900 p-6 rounded-xl max-w-md w-full mx-4 shadow-xl border border-border animate-fade-in">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L4.316 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-foreground">Start New Chat?</h3>
            </div>
            <p className="text-muted-foreground mb-3">
              This will clear your current conversation with <span className="font-medium text-foreground">{messages.length} messages</span>.
            </p>
            <p className="text-sm text-muted-foreground mb-8">
              Are you sure you want to start fresh?
            </p>
            <div className="flex space-x-3 justify-end">
              <button
                onClick={() => setShowClearDialog(false)}
                className="px-5 py-2.5 rounded-lg border border-border hover:bg-muted text-foreground transition-all duration-200 hover:shadow-md"
              >
                Cancel
              </button>
              <button
                onClick={clearChat}
                className="px-5 py-2.5 rounded-lg bg-amber-400 hover:bg-amber-500 text-white font-medium transition-all duration-200 shadow-md hover:shadow-lg hover:scale-105"
              >
                Start New Chat
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ChatInput({ 
  onSend, 
  isLoading 
}: { 
  onSend: (content: string) => void
  isLoading: boolean 
}) {
  const [content, setContent] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSendMessage = () => {
    if (content.trim()) {
      onSend(content)
      setContent("")
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSendMessage()
    }
  }

  return (
    <div className="flex items-center space-x-4">
      <div className="flex-1 relative">
        <input
          ref={inputRef}
          type="text"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me anything..."
          disabled={isLoading}
          className="w-full enhanced-input p-4 rounded-2xl text-foreground placeholder-muted-foreground disabled:opacity-50 transition-all duration-300"
        />
      </div>
      
      <button
        onClick={handleSendMessage}
        disabled={isLoading || !content.trim()}
        className="btn-primary p-4 rounded-2xl text-white disabled:opacity-50 disabled:cursor-not-allowed shadow-lg transition-all duration-300 group"
      >
        {isLoading ? (
          <svg className="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        ) : (
          <svg className="h-6 w-6 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
        )}
      </button>
    </div>
  )
} 
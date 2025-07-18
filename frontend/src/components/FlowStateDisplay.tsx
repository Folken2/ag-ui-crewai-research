interface FlowStateDisplayProps {
  state?: {
    conversation_history?: Array<{
      input: string
      response: string
      type: "chat" | "research_enhanced"
      sources?: string[]
    }>
    research_results?: {
      summary: string
      sources: string[]
      citations: string[]
    }
    processing?: boolean
    has_new_research?: boolean
  }
}

export function FlowStateDisplay({ state }: FlowStateDisplayProps) {
  const getStatusInfo = () => {
    if (state?.processing) return { 
      status: "Processing", 
      bgClass: "bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800/30", 
      dotClass: "bg-amber-500",
      textClass: "text-amber-700 dark:text-amber-400",
      icon: (
        <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      )
    }
    if (state?.has_new_research) return { 
      status: "Results Ready", 
      bgClass: "bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800/30", 
      dotClass: "bg-green-500",
      textClass: "text-green-700 dark:text-green-400",
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    }
    return { 
      status: "Ready", 
      bgClass: "bg-gray-50 border-gray-200 dark:bg-gray-900/20 dark:border-gray-800/30", 
      dotClass: "bg-gray-500",
      textClass: "text-gray-700 dark:text-gray-400",
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      )
    }
  }

  const { status, bgClass, dotClass, textClass, icon } = getStatusInfo()

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-amber-500 flex items-center justify-center shadow-lg">
          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-foreground">
          Flow State
        </h2>
      </div>
      
      {/* Status Indicator */}
      <div className={`glass-card p-6 rounded-2xl border transition-all duration-300 hover:scale-105 ${bgClass}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 rounded-xl ${dotClass} flex items-center justify-center text-white shadow-lg`}>
              {icon}
            </div>
            <div>
              <span className={`font-bold text-lg ${textClass}`}>{status}</span>
              <p className="text-sm text-muted-foreground mt-1">
                {state?.processing ? "AI is analyzing your request..." : 
                 state?.has_new_research ? "New insights are available" : 
                 "Ready for your next question"}
              </p>
            </div>
          </div>
          
          {/* Pulse indicator for processing */}
          {state?.processing && (
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-amber-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-amber-600 rounded-full animate-bounce delay-75"></div>
              <div className="w-2 h-2 bg-amber-700 rounded-full animate-bounce delay-150"></div>
            </div>
          )}
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Conversation Stats */}
        <div className="glass-card p-6 rounded-2xl border hover:border-gray-300 transition-all duration-300 hover:scale-105">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-8 h-8 rounded-lg bg-gray-600 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="font-bold text-lg text-foreground">
              Conversations
            </h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Total Messages:</span>
              <span className="font-bold text-2xl text-foreground">
                {state?.conversation_history?.length || 0}
              </span>
            </div>
          </div>
        </div>

        {/* Research Stats */}
        <div className="glass-card p-6 rounded-2xl border hover:border-gray-300 transition-all duration-300 hover:scale-105">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-8 h-8 rounded-lg bg-amber-500 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="font-bold text-lg text-foreground">
              Research
            </h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Status:</span>
              <span className={`font-bold px-3 py-1 rounded-full text-sm ${
                state?.has_new_research 
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' 
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400'
              }`}>
                {state?.has_new_research ? "Available" : "None"}
              </span>
            </div>
            {state?.research_results && (
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Sources:</span>
                <span className="font-bold text-2xl text-foreground">
                  {state.research_results.sources?.length || 0}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Processing Animation */}
      {state?.processing && (
        <div className="glass-card p-6 rounded-2xl border border-amber-200 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-800/30">
          <div className="flex items-center justify-center space-x-4">
            <div className="relative">
              <div className="w-12 h-12 border-4 border-amber-200 rounded-full"></div>
              <div className="absolute top-0 left-0 w-12 h-12 border-4 border-amber-500 rounded-full border-t-transparent animate-spin"></div>
            </div>
            <div className="text-center">
              <p className="font-bold text-amber-700 dark:text-amber-400">
                AI is working...
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Analyzing your request and gathering insights
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Research Progress Indicator */}
      {state?.has_new_research && (
        <div className="glass-card p-6 rounded-2xl border border-green-200 bg-green-50 dark:bg-green-900/20 dark:border-green-800/30">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center text-white shadow-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="flex-1">
              <h4 className="font-bold text-green-700 dark:text-green-400">
                Research Complete!
              </h4>
              <p className="text-sm text-muted-foreground">
                New research results are ready for you to explore
              </p>
            </div>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          </div>
        </div>
      )}
    </div>
  )
} 
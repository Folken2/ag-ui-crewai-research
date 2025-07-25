interface Source {
  url: string
  title?: string
  image_url?: string
  snippet?: string
}

interface ResearchResultsProps {
  results?: {
    summary: string
    sources: Source[]
    citations: string[]
  }
  conversations?: Array<{
    input: string
    response: string
    type: "chat" | "research_enhanced"
    sources?: Source[]
  }>
}

export function ResearchResults({ results, conversations }: ResearchResultsProps) {
  return (
    <div className="h-full flex flex-col space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500 flex items-center justify-center text-white shadow-lg">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-foreground">
            Research Results
          </h2>
        </div>
        {results && (
          <div className="flex items-center space-x-2 glass-card px-4 py-2 rounded-full border">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-bold text-foreground">
              {results.sources?.length || 0} sources found
            </span>
          </div>
        )}
      </div>

      {/* Research Results Section */}
      {results ? (
        <div className="space-y-6 flex-1">
          {/* Summary Card */}
          <div className="glass-card p-8 rounded-2xl border hover:border-gray-300 transition-all duration-300 hover:scale-[1.01]">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-8 h-8 rounded-lg bg-gray-600 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v6a2 2 0 002 2h2m8-6V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-foreground">
                Research Summary
              </h3>
            </div>
            <div className="prose prose-lg max-w-none">
              <p className="text-foreground leading-relaxed text-lg">{results.summary}</p>
            </div>
          </div>

          {/* Enhanced Sources Section */}
          {results.sources && results.sources.length > 0 && (
            <div className="glass-card p-8 rounded-2xl border hover:border-gray-300 transition-all duration-300 hover:scale-[1.01]">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-500 flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-foreground">
                    Sources
                  </h3>
                  <span className="text-sm text-muted-foreground bg-muted px-3 py-1 rounded-full">
                    {results.sources.length} found
                  </span>
                </div>
              </div>
              <div className="flex gap-3 overflow-x-auto pb-1 [&::-webkit-scrollbar]:h-2 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-amber-300/30 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-amber-300/50">
                {results.sources.map((source, index) => (
                  <a
                    key={index}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group relative overflow-hidden glass-card hover:shadow-lg p-3 rounded-xl border border-border/50 hover:border-amber-300/50 transition-all duration-300 hover:scale-[1.02] block flex-shrink-0 w-60"
                  >

                    
                    {/* Content */}
                    <div className="space-y-2">
                      {/* Image if available */}
                      {source.image_url && (
                        <div className="relative w-full h-16 mb-2 rounded-lg overflow-hidden">
                          <img
                            src={source.image_url}
                            alt={source.title || 'Source image'}
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
                        {new URL(source.url).hostname.replace(/^www\./, '')}
                      </div>
                      
                      {/* Title below source name */}
                      <div className="text-sm font-semibold text-foreground group-hover:text-amber-600 line-clamp-2 leading-tight transition-colors pr-6">
                        {source.title || new URL(source.url).hostname}
                      </div>
                      
                      {/* Snippet if available */}
                      {source.snippet && (
                        <div className="text-xs text-muted-foreground line-clamp-2 leading-tight">
                          {source.snippet}
                        </div>
                      )}
                      
                      <div className="flex items-center justify-center">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                          <span className="text-xs text-muted-foreground font-medium">
                            Verified source
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Hover effect overlay */}
                    <div className="absolute inset-0 bg-gradient-to-r from-amber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl"></div>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Citations Section */}
          {results.citations && results.citations.length > 0 && (
            <div className="glass-card p-8 rounded-2xl border hover:border-gray-300 transition-all duration-300 hover:scale-[1.01]">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-foreground">
                  Citations ({results.citations.length})
                </h3>
              </div>
              <div className="space-y-4">
                {results.citations.map((citation, index) => (
                  <div key={index} className="glass-card p-4 rounded-xl border-l-4 border-l-amber-400 bg-amber-50 dark:bg-amber-900/20">
                    <p className="text-foreground italic leading-relaxed">{citation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center glass-card p-12 rounded-2xl border max-w-md">
            <div className="mb-6">
              <div className="w-20 h-20 mx-auto bg-gray-100 dark:bg-gray-800 rounded-2xl flex items-center justify-center">
                <svg className="w-10 h-10 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
            <h3 className="text-xl font-bold text-foreground mb-3">No research results yet</h3>
            <p className="text-muted-foreground leading-relaxed">
              Start a conversation to see research results and insights here
            </p>
          </div>
        </div>
      )}

      {/* Conversation History */}
      {conversations && conversations.length > 0 && (
        <div className="glass-card p-8 rounded-2xl border hover:border-gray-300 transition-all duration-300">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-8 h-8 rounded-lg bg-gray-600 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-foreground">
              Recent Conversations
            </h3>
          </div>
          <div className="space-y-4 max-h-80 overflow-y-auto">
            {conversations.slice(-5).map((conv, index) => (
              <div key={index} className="group glass-card p-4 rounded-xl border hover:border-gray-300 transition-all duration-200 hover:scale-[1.01]">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold text-white ${
                      conv.type === "research_enhanced" 
                        ? "bg-amber-500" 
                        : "bg-gray-600"
                    }`}>
                      {conv.type === "research_enhanced" ? "R" : "C"}
                    </div>
                    <span className="text-sm font-bold text-foreground">
                      {conv.type === "research_enhanced" ? "Research Chat" : "Regular Chat"}
                    </span>
                  </div>
                  {conv.sources && (
                    <div className="flex items-center space-x-1 glass-card px-2 py-1 rounded-full border">
                      <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                      <span className="text-xs font-medium text-foreground">
                        {conv.sources.length} sources
                      </span>
                    </div>
                  )}
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2">{conv.input}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
} 
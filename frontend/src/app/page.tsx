"use client"

import { ChatInterface } from "@/components/ChatInterface";
import { useToken } from "@/contexts/TokenContext";

export default function Home() {
  const { isLoading } = useToken();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex items-center space-x-3">
          <div className="w-6 h-6 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-foreground font-medium">Initializing...</span>
        </div>
      </div>
    );
  }

  return <ChatInterface />;
}

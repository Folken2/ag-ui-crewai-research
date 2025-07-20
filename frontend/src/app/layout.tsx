import type { Metadata } from "next";
import { Inter, Geist, Geist_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI Research Assistant | CrewAI Powered",
  description: "Advanced AI-powered research assistant with real-time web search, in-depth analysis, and intelligent insights. Built with CrewAI and the AG-UI Protocol.",
  keywords: ["AI", "research", "assistant", "CrewAI", "artificial intelligence", "web search", "analysis"],
  authors: [{ name: "AI Research Team" }],
  viewport: "width=device-width, initial-scale=1",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#3b82f6" },
    { media: "(prefers-color-scheme: dark)", color: "#8b5cf6" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${geistSans.variable} ${geistMono.variable}`}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      </head>
      <body className={`${inter.className} antialiased min-h-screen`}>
        <div className="relative">
          {children}
        </div>
        <Analytics />
      </body>
    </html>
  );
}

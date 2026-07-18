import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ContinuaML — Production-Grade LLM Continual Learning Research Platform",

  description: "A professional platform for tracking catastrophic forgetting, evaluating continual-learning mitigation strategies, and exporting reproducible research outputs.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark h-full antialiased">
      <body className={`${geistSans.variable} ${geistMono.variable} min-h-screen bg-[#090d16] text-[#f1f5f9] flex flex-col`}>
        {children}
      </body>
    </html>
  );
}

import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'DUBAI AI CHAMPIONSHIP 2027 | SOVEREIGN GLASS COCKPIT',
  description: 'Bare-Metal C99 Sovereign Agent Cockpit for Dubai AI Agents Championship 2026-2027',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" dir="ltr">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased min-h-screen flex flex-col">{children}</body>
    </html>
  );
}

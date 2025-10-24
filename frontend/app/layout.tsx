import type { Metadata, Viewport } from 'next';
import { Noto_Serif } from 'next/font/google';
import './globals.css';
import { ChatProvider } from '@/lib/context/ChatContext';
import { WriteProvider } from '@/lib/context/WriteContext';

const notoSerif = Noto_Serif({ 
  weight: ['400', '500', '600', '700'],
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-noto-serif',
});

export const metadata: Metadata = {
  title: 'A Penny For My Thought - AI-Powered Journaling',
  description: 'An LLM-powered journaling web application with conversational interface',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={notoSerif.variable}>
      <body className={`${notoSerif.className} font-serif antialiased`}>
        <ChatProvider>
          <WriteProvider>
            {children}
          </WriteProvider>
        </ChatProvider>
      </body>
    </html>
  );
}

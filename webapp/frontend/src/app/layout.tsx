import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Research Dossier - Intelligence at Your Fingertips',
  description: 'Generate comprehensive research dossiers on companies and individuals. Professional intelligence reports powered by AI.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body>
        {children}
      </body>
    </html>
  )
}

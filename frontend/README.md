# LLM Journal Webapp - Frontend

Next.js 14 frontend for the LLM-powered journaling application.

## Setup

### Prerequisites
- Node.js 18 or higher
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp env_template.txt .env.local
# Edit .env.local if needed (default: http://localhost:8000)
```

### Running the Development Server

```bash
npm run dev
```

The application will be available at http://localhost:3000

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Home page
│   └── globals.css          # Global styles
├── components/
│   ├── chat/                # Chat components
│   ├── journal/             # Journal components
│   ├── shared/              # Shared components
│   └── ui/                  # UI components (shadcn/ui)
├── lib/
│   ├── api/                 # API client functions
│   ├── hooks/               # Custom React hooks
│   ├── context/             # React Context
│   ├── types/               # TypeScript types
│   └── utils.ts             # Utility functions
├── public/                  # Static assets
└── styles/                  # Additional styles
```

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 3
- **UI Components**: shadcn/ui (Radix UI)
- **State Management**: React Context
- **HTTP Client**: Native fetch API

## Development

### Building for Production
```bash
npm run build
npm start
```

### Linting
```bash
npm run lint
```

## Features

(Will be implemented in later tasks)

- Real-time chat interface
- Message history with markdown rendering
- Past conversation sidebar
- RAG-powered context retrieval
- Responsive design (mobile & desktop)



# Frontend - A Penny For My Thought Web App

Next.js 14 frontend for the AI-powered journaling web application.

## 🚀 Quick Start

### Prerequisites

- **Node.js 18 or higher**
- **npm** (comes with Node.js)
- **Backend running** on http://localhost:8000

### Installation

1. **Install dependencies**:
```bash
npm install
```

2. **Configure environment**:
```bash
cp env_template.txt .env.local
# Edit .env.local with your backend URL
```

3. **Run development server**:
```bash
npm run dev
```

The app will be available at http://localhost:3000

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# Required - Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development vs Production

- **Development**: `http://localhost:8000`
- **Production**: `https://your-api-domain.com`

## 📁 Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with ChatProvider
│   ├── page.tsx           # Home page (new chat)
│   ├── chat/[sessionId]/  # Dynamic chat session pages
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── chat/             # Chat interface components
│   │   ├── ChatInterface.tsx    # Main chat interface
│   │   ├── ChatInput.tsx        # Message input
│   │   ├── Message.tsx          # Individual message
│   │   ├── MessageList.tsx      # Message list
│   │   └── StreamingMessage.tsx # Streaming message display
│   ├── conversations/     # Conversation management
│   │   ├── ConversationList.tsx # Past conversations
│   │   └── NewConversationButton.tsx
│   ├── layout/           # Layout components
│   │   └── ChatSidebar.tsx # Responsive sidebar
│   ├── shared/           # Shared UI components
│   │   ├── ErrorMessage.tsx    # Error display
│   │   └── LoadingSpinner.tsx  # Loading indicator
│   └── ui/               # shadcn/ui components
├── lib/                  # Utilities and API clients
│   ├── api/             # API client functions
│   │   ├── chat.ts      # Chat API client
│   │   └── journals.ts  # Journal API client
│   ├── context/         # React Context
│   │   └── ChatContext.tsx # Global chat state
│   ├── types/           # TypeScript types
│   │   ├── chat.ts      # Chat-related types
│   │   └── journal.ts   # Journal-related types
│   ├── config.ts        # Configuration
│   └── utils.ts         # Utility functions
├── __tests__/           # Test setup
├── package.json         # Dependencies and scripts
├── tailwind.config.js   # Tailwind CSS configuration
├── jest.config.js       # Jest test configuration
└── README.md           # This file
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test ChatContext.test.tsx
```

### Test Structure

- `ChatContext.test.tsx` - Context and hook tests
- All components are tested with React Testing Library

## 🎨 UI Components

### Chat Components

- **ChatInterface**: Main chat interface with error handling
- **ChatInput**: Message input with auto-resize and keyboard shortcuts
- **Message**: Individual message display with markdown and syntax highlighting
- **MessageList**: Scrollable message list with auto-scroll
- **StreamingMessage**: Real-time streaming message display

### Layout Components

- **ChatSidebar**: Responsive sidebar (desktop) / drawer (mobile)
- **ConversationList**: List of past conversations with auto-refresh

### Shared Components

- **ErrorMessage**: Error display with retry/dismiss options
- **LoadingSpinner**: Loading indicator with size variants

### shadcn/ui Components

- **Button**: Various button styles and sizes
- **Card**: Container component for content
- **Input**: Form input component
- **ScrollArea**: Custom scrollable container
- **Separator**: Visual separator
- **Sheet**: Mobile drawer component
- **Textarea**: Multi-line text input

## 📱 Responsive Design

### Breakpoints

- **Mobile**: < 768px (drawer navigation)
- **Desktop**: ≥ 768px (fixed sidebar)

### Mobile Features

- **Hamburger Menu**: Slide-out drawer for navigation
- **Touch-Friendly**: 44px minimum tap targets
- **No Zoom**: Prevents unwanted zooming on iOS
- **Full-Width Messages**: Optimized message display

### Desktop Features

- **Fixed Sidebar**: Always visible navigation
- **Split Layout**: Sidebar + main content
- **Hover Effects**: Interactive elements

## 🔄 State Management

### ChatContext

Global state management using React Context:

```typescript
interface ChatContextType {
  // State
  sessionId: string;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
  error: string | null;
  currentJournalId: string | null;
  
  // Actions
  sendMessage: (content: string, useStreaming?: boolean) => Promise<void>;
  loadSession: (journalId: string) => Promise<void>;
  clearChat: () => void;
  setError: (error: string | null) => void;
}
```

### Key Features

- **Auto-save**: Conversations automatically saved after each message
- **Streaming**: Real-time message streaming with fallback
- **Error Handling**: Comprehensive error handling with retry
- **URL Routing**: Shareable conversation URLs

## 🌐 API Integration

### Chat API

```typescript
// Send message (non-streaming)
const response = await sendChatMessage(message, sessionId, history);

// Stream message
for await (const event of streamChatMessage(message, sessionId, history)) {
  if (event.type === 'token') {
    // Handle streaming token
  }
}
```

### Journal API

```typescript
// List conversations
const conversations = await getAllJournals(limit, offset);

// Load conversation
const journal = await getJournal(journalId);

// Save conversation
const metadata = await saveJournal(sessionId, messages, journalId);
```

## 🎯 Key Features

### Real-time Streaming

- **Server-Sent Events**: Real-time token streaming
- **Fallback**: Automatic fallback to non-streaming on errors
- **Smooth UX**: Character-by-character response display

### Auto-save

- **Automatic**: Conversations saved after each message exchange
- **No User Action**: No need to manually save
- **Persistent**: Survives browser refresh and navigation

### URL Routing

- **Shareable Links**: Copy URL to share specific conversations
- **Deep Linking**: Open app directly to a conversation
- **Browser History**: Back/forward navigation support

### Error Handling

- **User-Friendly**: Clear, actionable error messages
- **Retry Logic**: Automatic retry for recoverable errors
- **Graceful Degradation**: App continues working even with errors

## 🛠️ Development

### Available Scripts

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint

# Testing
npm test             # Run tests
npm test -- --watch  # Run tests in watch mode

# Type checking
npm run type-check   # Run TypeScript compiler
```

### Code Style

- **TypeScript**: Strict mode enabled
- **ESLint**: Configured for Next.js and React
- **Prettier**: Code formatting (if configured)
- **Tailwind**: Utility-first CSS

### Component Guidelines

1. **Use TypeScript**: All components should be typed
2. **React.memo**: Use for performance optimization
3. **useCallback**: Use for event handlers
4. **Error Boundaries**: Wrap components that might fail
5. **Accessibility**: Include ARIA labels and semantic HTML

## 🚀 Production Build

### Build Process

```bash
# Install dependencies
npm install

# Build the application
npm run build

# Start production server
npm start
```

### Environment Variables

Set production environment variables:

```bash
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

### Optimization

- **Static Generation**: Pages are statically generated
- **Code Splitting**: Automatic code splitting by Next.js
- **Image Optimization**: Built-in image optimization
- **Bundle Analysis**: Use `npm run analyze` to analyze bundle size

## 🐛 Troubleshooting

### Common Issues

1. **"Cannot find name 'process'"**
   - Ensure you're using `NEXT_PUBLIC_` prefix for env vars
   - Check that `next-env.d.ts` is present

2. **API connection errors**
   - Verify `NEXT_PUBLIC_API_URL` is correct
   - Ensure backend is running
   - Check CORS configuration

3. **Build errors**
   - Run `npm run type-check` to check TypeScript
   - Ensure all imports are correct
   - Check for unused variables

4. **Test failures**
   - Ensure test environment is set up correctly
   - Check that mocks are properly configured
   - Verify all dependencies are installed

### Development Tools

- **React DevTools**: Browser extension for debugging
- **Next.js DevTools**: Built-in development tools
- **TypeScript**: Strict type checking
- **ESLint**: Code quality checks

## 📊 Performance

### Metrics

- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

### Optimization Tips

1. **Code Splitting**: Use dynamic imports for large components
2. **Memoization**: Use React.memo for expensive components
3. **Lazy Loading**: Load components on demand
4. **Bundle Analysis**: Regularly analyze bundle size

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new components
3. Ensure TypeScript types are correct
4. Test on both mobile and desktop
5. Update documentation

## 📄 License

This project is licensed under the MIT License.
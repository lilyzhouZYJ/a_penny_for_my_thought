# Frontend - A Penny For My Thought Web App

Next.js 14 frontend for the AI-powered journaling web application. Features a responsive chat interface with real-time streaming, conversation management, and mobile-optimized design using modern React patterns and shadcn/ui components.

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
│   │   ├── ChatInterface.tsx    # Main chat interface with error handling
│   │   ├── ChatInput.tsx        # Message input with auto-resize
│   │   ├── Message.tsx          # Individual message with markdown
│   │   ├── MessageList.tsx      # Scrollable message list
│   │   └── StreamingMessage.tsx # Real-time streaming display
│   ├── conversations/     # Conversation management
│   │   ├── ConversationList.tsx # Past conversations with auto-refresh
│   │   └── NewConversationButton.tsx # New conversation trigger
│   ├── layout/           # Layout components
│   │   └── ChatSidebar.tsx # Responsive sidebar/drawer
│   ├── shared/           # Shared UI components
│   │   ├── ErrorMessage.tsx    # Error display with retry
│   │   └── LoadingSpinner.tsx  # Loading indicators
│   └── ui/               # shadcn/ui components
├── lib/                  # Utilities and API clients
│   ├── api/             # API client functions
│   │   ├── chat.ts       # Chat API with streaming support
│   │   └── journals.ts   # Journal management API
│   ├── context/         # React Context
│   │   └── ChatContext.tsx # Global chat state management
│   ├── types/           # TypeScript types
│   │   ├── chat.ts      # Chat-related types
│   │   └── journal.ts   # Journal-related types
│   ├── config.ts        # Configuration
│   └── utils/           # Utility functions
│       └── error-handlers.ts # Error parsing and handling
├── __tests__/           # Test setup
├── package.json         # Dependencies and scripts
├── tailwind.config.ts   # Tailwind CSS configuration
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

- `ChatContext.test.tsx` - Context and hook tests with React Testing Library
- All components tested with comprehensive user interaction scenarios

## 🎨 UI Components

### Chat Components

- **ChatInterface**: Main chat interface with comprehensive error handling and retry logic
- **ChatInput**: Message input with auto-resize, keyboard shortcuts (Enter/Shift+Enter), and disabled states
- **Message**: Individual message display with markdown rendering and syntax highlighting
- **MessageList**: Scrollable message list with auto-scroll to bottom and loading indicators
- **StreamingMessage**: Real-time streaming message display with smooth character-by-character updates

### Layout Components

- **ChatSidebar**: Responsive sidebar (desktop) / drawer (mobile) with touch-friendly navigation
- **ConversationList**: List of past conversations with auto-refresh, delete functionality, and loading states

### Shared Components

- **ErrorMessage**: Error display with retry/dismiss options and user-friendly error parsing
- **LoadingSpinner**: Loading indicator with size variants and text support

### shadcn/ui Components

- **Button**: Various button styles, sizes, and variants with proper accessibility
- **Card**: Container component for content with header, content, and footer sections
- **Input**: Form input component with proper styling and focus states
- **ScrollArea**: Custom scrollable container with smooth scrolling
- **Separator**: Visual separator with horizontal and vertical variants
- **Sheet**: Mobile drawer component with backdrop and animations
- **Textarea**: Multi-line text input with auto-resize functionality

## 📱 Responsive Design

### Breakpoints

- **Mobile**: < 768px (drawer navigation)
- **Desktop**: ≥ 768px (fixed sidebar)

### Mobile Features

- **Hamburger Menu**: Slide-out drawer for navigation with smooth animations
- **Touch-Friendly**: 44px minimum tap targets for accessibility
- **No Zoom**: Prevents unwanted zooming on iOS devices
- **Full-Width Messages**: Optimized message display for mobile screens
- **Swipe Gestures**: Natural mobile interaction patterns

### Desktop Features

- **Fixed Sidebar**: Always visible navigation with conversation list
- **Split Layout**: Sidebar + main content area
- **Hover Effects**: Interactive elements with smooth transitions
- **Keyboard Shortcuts**: Enhanced productivity with keyboard navigation

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
  clearChat: () => string;
  handleNewConversation: () => void;
  setError: (error: string | null) => void;
}
```

### Key Features

- **Auto-save**: Conversations automatically saved after each message exchange
- **Streaming**: Real-time message streaming with automatic fallback to non-streaming
- **Error Handling**: Comprehensive error handling with user-friendly messages and retry logic
- **URL Routing**: Shareable conversation URLs with deep linking support
- **Memory Management**: Efficient state management with React.memo and useCallback optimizations

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

- **Server-Sent Events**: Real-time token streaming with automatic reconnection
- **Fallback**: Automatic fallback to non-streaming on errors or network issues
- **Smooth UX**: Character-by-character response display with loading states
- **Error Recovery**: Graceful handling of streaming interruptions

### Auto-save

- **Automatic**: Conversations saved after each message exchange
- **No User Action**: No need to manually save
- **Persistent**: Survives browser refresh and navigation

### URL Routing

- **Shareable Links**: Copy URL to share specific conversations
- **Deep Linking**: Open app directly to a conversation
- **Browser History**: Back/forward navigation support

### Error Handling

- **User-Friendly**: Clear, actionable error messages with context
- **Retry Logic**: Automatic retry for recoverable errors (network, timeout)
- **Graceful Degradation**: App continues working even with partial failures
- **Error Parsing**: Intelligent error message parsing and display

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
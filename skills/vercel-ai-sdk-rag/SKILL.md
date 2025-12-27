---
name: vercel-ai-sdk-rag
description: Guide pour intégrer le RAG avec le template ai-chatbot de Vercel
allowed-tools: Read, Write, Grep, Glob
---

# Intégration Vercel AI SDK avec RAG

Guide pour intégrer le RAG avec le template ai-chatbot de Vercel.

## Setup du template

```bash
# Cloner le template
pnpx create-next-app@latest --example https://github.com/vercel/ai-chatbot

# Installer les dépendances
pnpm install
```

## Configuration pour RAG local

### Variables d'environnement

```env
# .env.local

# Backend RAG
NEXT_PUBLIC_API_URL=http://localhost:8000

# Auth (optionnel - pour multi-users)
AUTH_SECRET=your-secret-key

# Désactiver les providers cloud
OPENAI_API_KEY=not-needed
```

### API Route pour RAG

```typescript
// app/api/chat/route.ts
import { StreamingTextResponse } from 'ai';

export const runtime = 'edge';

export async function POST(req: Request) {
  const { messages, id: conversationId } = await req.json();

  // Dernier message = la question
  const lastMessage = messages[messages.length - 1];

  // Appeler le backend RAG
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: lastMessage.content,
      conversation_id: conversationId,
      include_sources: true
    }),
  });

  if (!response.ok) {
    throw new Error('RAG API error');
  }

  // Transformer SSE en stream compatible Vercel AI SDK
  const stream = new ReadableStream({
    async start(controller) {
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        controller.close();
        return;
      }

      let sources: any[] = [];

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          // Ajouter les sources à la fin
          if (sources.length > 0) {
            const sourcesText = `\n\n---\n**Sources:**\n${sources.map((s, i) =>
              `[${i + 1}] ${s.metadata?.title || s.id}`
            ).join('\n')}`;
            controller.enqueue(new TextEncoder().encode(sourcesText));
          }
          controller.close();
          break;
        }

        const text = decoder.decode(value);
        const lines = text.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'token') {
                controller.enqueue(new TextEncoder().encode(data.data));
              } else if (data.type === 'sources') {
                sources = data.data;
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }
    },
  });

  return new StreamingTextResponse(stream);
}
```

## Hook personnalisé pour RAG

```typescript
// lib/hooks/use-rag-chat.ts
import { useChat as useVercelChat, Message } from 'ai/react';
import { useState, useCallback } from 'react';

interface Source {
  id: string;
  content: string;
  score: number;
  metadata?: Record<string, any>;
}

interface UseRagChatOptions {
  id?: string;
  initialMessages?: Message[];
  onFinish?: (message: Message, sources: Source[]) => void;
}

export function useRagChat(options: UseRagChatOptions = {}) {
  const [sources, setSources] = useState<Record<string, Source[]>>({});

  const chat = useVercelChat({
    ...options,
    api: '/api/chat',
    onFinish: (message) => {
      // Parser les sources de la réponse si présentes
      const sourcesMatch = message.content.match(/---\n\*\*Sources:\*\*\n([\s\S]*?)$/);
      if (sourcesMatch) {
        // Les sources sont déjà dans le message
      }
      options.onFinish?.(message, sources[message.id] || []);
    },
  });

  const getSourcesForMessage = useCallback((messageId: string) => {
    return sources[messageId] || [];
  }, [sources]);

  return {
    ...chat,
    sources,
    getSourcesForMessage,
  };
}
```

## Composants personnalisés

### Message avec sources

```tsx
// components/message-with-sources.tsx
'use client';

import { Message } from 'ai';
import { SourcesPanel } from './sources-panel';
import { Markdown } from './markdown';

interface MessageWithSourcesProps {
  message: Message;
  sources?: Array<{
    id: string;
    content: string;
    score: number;
    metadata?: Record<string, any>;
  }>;
}

export function MessageWithSources({ message, sources }: MessageWithSourcesProps) {
  // Séparer le contenu des sources si elles sont inline
  const [content, sourcesSection] = message.content.split('\n\n---\n**Sources:**');

  return (
    <div className="space-y-3">
      <Markdown content={content} />

      {(sources?.length || sourcesSection) && (
        <SourcesPanel
          sources={sources || parseInlineSources(sourcesSection)}
          className="mt-4"
        />
      )}
    </div>
  );
}

function parseInlineSources(sourcesText?: string) {
  if (!sourcesText) return [];

  return sourcesText
    .split('\n')
    .filter(line => line.match(/^\[\d+\]/))
    .map((line, i) => ({
      id: `source-${i}`,
      content: line.replace(/^\[\d+\]\s*/, ''),
      score: 0,
    }));
}
```

### Input multimodal avec voice

```tsx
// components/chat-input.tsx
'use client';

import { useState, useRef, FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Mic, MicOff, Paperclip } from 'lucide-react';

interface ChatInputProps {
  onSubmit: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

export function ChatInput({ onSubmit, isLoading, placeholder }: ChatInputProps) {
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    onSubmit(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      // Stop recording - le hook gèrera la transcription
      setIsRecording(false);
    } else {
      setIsRecording(true);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <Textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || "Posez votre question..."}
        className="min-h-[60px] pr-24 resize-none"
        disabled={isLoading}
      />

      <div className="absolute right-2 bottom-2 flex gap-1">
        <Button
          type="button"
          size="icon"
          variant={isRecording ? "destructive" : "ghost"}
          onClick={toggleRecording}
          disabled={isLoading}
        >
          {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
        </Button>

        <Button
          type="submit"
          size="icon"
          disabled={!input.trim() || isLoading}
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}
```

## Page de chat complète

```tsx
// app/(chat)/page.tsx
'use client';

import { useRagChat } from '@/lib/hooks/use-rag-chat';
import { ChatInput } from '@/components/chat-input';
import { MessageWithSources } from '@/components/message-with-sources';

export default function ChatPage() {
  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    getSourcesForMessage,
  } = useRagChat({
    id: 'default-conversation',
  });

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="border-b p-4">
        <h1 className="text-xl font-semibold">Assistant RAG</h1>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            <p>Posez votre première question pour commencer.</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                }`}
              >
                {message.role === 'assistant' ? (
                  <MessageWithSources
                    message={message}
                    sources={getSourcesForMessage(message.id)}
                  />
                ) : (
                  <p>{message.content}</p>
                )}
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg p-4">
              <div className="flex gap-1">
                <div className="h-2 w-2 rounded-full bg-primary animate-bounce" />
                <div className="h-2 w-2 rounded-full bg-primary animate-bounce delay-100" />
                <div className="h-2 w-2 rounded-full bg-primary animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <ChatInput
          onSubmit={(msg) => handleSubmit(new Event('submit') as any)}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
```

## Configuration Next.js

```javascript
// next.config.mjs
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: true,
  },

  // Proxy vers le backend RAG en dev
  async rewrites() {
    return [
      {
        source: '/api/rag/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ];
  },

  // Output standalone pour Docker
  output: 'standalone',
};

export default nextConfig;
```

import React, { useRef, useEffect } from 'react';
import { Send, User, Bot, Sparkles, AlertCircle } from 'lucide-react';
import clsx from 'clsx';

export type MessageType = 'user' | 'ai';
export type MetadataType = 'chat' | 'quiz_question' | 'reward' | 'relearn' | null;

export interface Message {
  role: MessageType;
  content: string;
  metadata?: {
    type?: MetadataType;
  };
}

interface ChatBoxProps {
  messages: Message[];
  onSendMessage: (msg: string) => void;
  isLoading: boolean;
}

export const ChatBox: React.FC<ChatBoxProps> = ({ messages, onSendMessage, isLoading }) => {
  const [input, setInput] = React.useState('');
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const renderMessage = (msg: Message, idx: number) => {
    const isUser = msg.role === 'user';
    const msgType = msg.metadata?.type;

    let wrapperClasses = "flex gap-4 p-6 rounded-2xl mb-4 max-w-4xl mx-auto w-full transition-all";
    let icon = isUser ? <User size={24} /> : <Bot size={24} />;
    let iconBg = isUser ? "bg-indigo-100 text-indigo-600" : "bg-slate-200 text-slate-700";

    // Dynamic styling based on metadata for AI
    if (!isUser) {
      if (msgType === 'reward') {
        wrapperClasses = clsx(wrapperClasses, "bg-emerald-50 border-2 border-emerald-400 shadow-sm shadow-emerald-100");
        icon = <Sparkles size={24} />;
        iconBg = "bg-emerald-500 text-white";
      } else if (msgType === 'relearn') {
        wrapperClasses = clsx(wrapperClasses, "bg-amber-50 border border-amber-200 shadow-sm");
        icon = <AlertCircle size={24} />;
        iconBg = "bg-amber-500 text-white";
      } else if (msgType === 'quiz_question') {
        wrapperClasses = clsx(wrapperClasses, "bg-indigo-50 border border-indigo-100");
        iconBg = "bg-indigo-500 text-white";
      } else {
        wrapperClasses = clsx(wrapperClasses, "bg-white border border-slate-100 shadow-sm");
      }
    } else {
      wrapperClasses = clsx(wrapperClasses, "flex-row-reverse bg-transparent");
      iconBg = "bg-slate-800 text-white";
    }

    return (
      <div key={idx} className={wrapperClasses}>
        <div className={clsx("flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-sm", iconBg)}>
          {icon}
        </div>
        <div className={clsx("flex flex-col flex-1", isUser ? "items-end" : "items-start")}>
          <span className="text-sm font-medium text-slate-500 mb-1">{isUser ? 'You' : 'EduCompanion'}</span>
          <div className={clsx("text-slate-800 whitespace-pre-wrap leading-relaxed", isUser ? "bg-slate-100 px-5 py-3 rounded-2xl rounded-tr-sm" : "")}>
            {msg.content}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex-1 flex flex-col bg-slate-50 h-screen relative">
      <div className="flex-1 overflow-y-auto p-4 sm:p-8">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-4">
            <Bot size={48} className="text-indigo-200" />
            <h2 className="text-2xl font-semibold text-slate-600">Welcome to EduCompanion</h2>
            <p className="text-center max-w-md">Upload a document to get started, or just say hello! I can help you study, test your knowledge, and break down complex concepts.</p>
          </div>
        ) : (
          messages.map((msg, idx) => renderMessage(msg, idx))
        )}
        
        {isLoading && (
          <div className="flex gap-4 p-6 rounded-2xl mb-4 max-w-4xl mx-auto w-full items-center">
            <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-sm bg-slate-200 text-slate-700 animate-pulse">
              <Bot size={24} />
            </div>
            <div className="flex gap-1">
              <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      <div className="p-4 bg-white border-t border-slate-200">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question or request a quiz..."
            disabled={isLoading}
            className="w-full pl-6 pr-14 py-4 bg-slate-100 border-transparent rounded-full focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all outline-none text-slate-800 shadow-inner"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 disabled:opacity-50 disabled:hover:bg-indigo-600 transition-colors shadow-sm"
          >
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
};

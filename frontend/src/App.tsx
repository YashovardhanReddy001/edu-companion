import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Sidebar } from './components/Sidebar';
import { ChatBox, type Message } from './components/ChatBox';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [threadId] = useState(() => Math.random().toString(36).substring(7));
  
  // Graph state tracking
  const stateRef = useRef({
    context: "",
    quiz_active: false,
    last_score: 0
  });

  const handleSendMessage = async (content: string) => {
    // Optimistically add user message
    const newMessages: Message[] = [...messages, { role: 'user', content }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/chat', {
        message: content,
        thread_id: threadId,
        // send history except the one we just added optimistically
        messages_history: messages.map(m => ({ role: m.role, content: m.content })),
        context: stateRef.current.context,
        quiz_active: stateRef.current.quiz_active,
        last_score: stateRef.current.last_score
      });

      const data = response.data;
      
      // Update graph state from backend
      stateRef.current = {
        context: data.context,
        quiz_active: data.quiz_active,
        last_score: data.last_score
      };

      // Add backend responses
      const backendMessages = data.messages;
      
      // The backend returns the entire message history. 
      // We can just replace our messages state, mapping them to our Message interface.
      const mappedMessages: Message[] = backendMessages.map((msg: any, idx: number) => {
        // If it's the very last message and it's AI, we attach the metadata
        let metadata = {};
        if (idx === backendMessages.length - 1 && msg.role === 'ai') {
          metadata = { type: data.metadata?.type };
        }
        
        return {
          role: msg.role,
          content: msg.content,
          metadata
        };
      });

      setMessages(mappedMessages);

    } catch (error) {
      console.error("Failed to send message:", error);
      // Fallback message for error
      setMessages([...newMessages, { role: 'ai', content: "Sorry, I encountered an error connecting to the server. Please ensure the backend is running." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex w-full h-screen font-sans bg-slate-50 overflow-hidden">
      <Sidebar />
      <ChatBox 
        messages={messages} 
        onSendMessage={handleSendMessage} 
        isLoading={isLoading} 
      />
    </div>
  );
}

export default App;

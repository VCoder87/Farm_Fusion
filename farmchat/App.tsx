import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Chat } from '@google/genai';
import { ChatMessage, MessageRole } from './types';
import { startChat } from './services/geminiService';
import ChatMessageComponent from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import BotIcon from './components/icons/BotIcon';

const App: React.FC = () => {
  const [chat, setChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      const chatInstance = startChat();
      setChat(chatInstance);
      setMessages([
        {
          role: MessageRole.MODEL,
          content: "Hello! I'm FarmChat. How can I help you with your farming questions today?",
        },
      ]);
    } catch (e) {
      if (e instanceof Error) {
        setError(e.message);
      } else {
        setError("An unknown error occurred during initialization.");
      }
      console.error(e);
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = useCallback(async (userInput: string) => {
    if (!chat) return;

    setIsLoading(true);
    setError(null);

    const userMessage: ChatMessage = { role: MessageRole.USER, content: userInput };
    // Add user message and a placeholder for the model's response
    setMessages((prevMessages) => [...prevMessages, userMessage, { role: MessageRole.MODEL, content: '' }]);
    
    try {
      const stream = await chat.sendMessageStream({ message: userInput });

      let fullResponse = '';
      for await (const chunk of stream) {
        fullResponse += chunk.text;
        setMessages((prevMessages) => {
          const newMessages = [...prevMessages];
          newMessages[newMessages.length - 1] = { role: MessageRole.MODEL, content: fullResponse };
          return newMessages;
        });
      }
    } catch (e) {
      const errorMessage = 'Sorry, I encountered an error. Please try again.';
      if (e instanceof Error) {
        console.error("Gemini API Error:", e.message);
        setError(`API Error: ${e.message}`);
      } else {
        console.error("Gemini API Error:", e);
        setError(errorMessage);
      }
      setMessages((prevMessages) => {
         const newMessages = [...prevMessages];
         newMessages[newMessages.length - 1] = { role: MessageRole.MODEL, content: errorMessage };
         return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  }, [chat]);


  return (
    <div className="flex flex-col h-screen bg-black/50 backdrop-blur-md">
      <header className="p-4 bg-gray-900/80 backdrop-blur-md text-white text-center shadow-lg border-b border-gray-700">
        <h1 className="text-2xl font-bold flex items-center justify-center gap-3">
          <BotIcon className="w-8 h-8 text-green-400" />
          FarmChat
        </h1>
      </header>

      <main className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto">
          {messages.map((msg, index) => (
            <ChatMessageComponent key={index} message={msg} />
          ))}
          <div ref={messagesEndRef} />
        </div>
        {error && (
            <div className="max-w-4xl mx-auto p-4 my-2 bg-red-800/80 border border-red-600 rounded-lg text-white text-center">
              <p><strong>Error:</strong> {error}</p>
            </div>
        )}
      </main>
      
      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
};

export default App;
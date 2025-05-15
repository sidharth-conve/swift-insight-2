import React, { useState } from 'react';
import {
  MainContainer,
  ChatContainer,
  MessageList,
  Message,
  MessageInput,
} from '@chatscope/chat-ui-kit-react';

const ChatApp = () => {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null); // track sessionId


  const handleSend = async (innerHtml) => {
    const userMessage = {
      message: innerHtml,
      sender: 'user',
      direction: 'outgoing',
    };
    setMessages((prev) => [...prev, userMessage]);
    const bodyObj = JSON.stringify({ input_data: innerHtml,          session_id: sessionId, // send existing session id or null
  })
    console.log("bodyObj", bodyObj)
    console.log("InnerHTML", innerHtml)
    try {
      const response = await fetch('http://127.0.0.1:8000/api/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: bodyObj,
      });

      const data = await response.json();
      if (!sessionId) {
        setSessionId(data.session_id);
      }
      const botMessage = {
        message: data.output,
        sender: 'bot',
        direction: 'incoming',
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Error fetching AI response:', error);
    }
  };

  const handleNewChat = async () => {
    if (sessionId) {
      // Send exit message to backend to close the conversation session
      try {
        await fetch('http://127.0.0.1:8000/api/evaluate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            input_data: 'exit',
            session_id: sessionId,
          }),
        });
      } catch (error) {
        console.error('Error ending session:', error);
      }
    }
  
    // Now reset frontend state
    setMessages([]);
    setSessionId(null);
  };
  


  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '1rem' }}>
      <button
        onClick={handleNewChat}
        style={{
          marginBottom: '1rem',
          padding: '0.5rem 1rem',
          backgroundColor: '#007bff',
          color: '#fff',
          border: 'none',
          borderRadius: '0.5rem',
          cursor: 'pointer',
          height: '40px'
        }}
      >
        New Chat
      </button>

  <div style={{ width: '100%', maxWidth: '800px', height: '90vh' }}>
      <MainContainer>
        <ChatContainer>
          <MessageList>
            {messages.map((msg, idx) => (
              <Message
                key={idx}
                model={{
                  message: msg.message,
                  sentTime: 'just now',
                  sender: msg.sender,
                  direction: msg.direction,
                }}
              />
            ))}
          </MessageList>
          <MessageInput placeholder="Type your message..." onSend={handleSend} />
        </ChatContainer>
      </MainContainer>
    </div>
    </div>
  );
};

export default ChatApp;

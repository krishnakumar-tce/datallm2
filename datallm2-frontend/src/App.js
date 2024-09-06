import React, { useState } from 'react';
import styled from 'styled-components';
import axios from 'axios';

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px;
`;

const ChatContainer = styled.div`
  flex-grow: 1;
  overflow-y: auto;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 20px;
  margin-bottom: 20px;
`;

const MessageContainer = styled.div`
  margin-bottom: 10px;
`;

const UserMessage = styled.p`
  background-color: #e6f2ff;
  padding: 10px;
  border-radius: 4px;
`;

const BotMessage = styled.p`
  background-color: #f0f0f0;
  padding: 10px;
  border-radius: 4px;
`;

const InputContainer = styled.form`
  display: flex;
`;

const Input = styled.input`
  flex-grow: 1;
  padding: 10px;
  font-size: 16px;
`;

const Button = styled.button`
  padding: 10px 20px;
  font-size: 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  cursor: pointer;
`;

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
  
    const userMessage = input;
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setInput('');
  
    try {
      const response = await axios.post('http://127.0.0.1:5000/query', 
        { query: userMessage },
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      setMessages(prev => [
        ...prev, 
        { type: 'bot', content: `Raw Result: ${response.data.result}` },
        { type: 'bot', content: `Friendly Response: ${response.data.friendlyResponse}` }
      ]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { type: 'bot', content: 'Sorry, an error occurred.' }]);
    }
  };
  return (
    <AppContainer>
      <ChatContainer>
        {messages.map((message, index) => (
          <MessageContainer key={index}>
            {message.type === 'user' ? (
              <UserMessage>{message.content}</UserMessage>
            ) : (
              <BotMessage>{message.content}</BotMessage>
            )}
          </MessageContainer>
        ))}
      </ChatContainer>
      <InputContainer onSubmit={handleSubmit}>
        <Input 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your query here..."
        />
        <Button type="submit">Send</Button>
      </InputContainer>
    </AppContainer>
  );
}

export default App;
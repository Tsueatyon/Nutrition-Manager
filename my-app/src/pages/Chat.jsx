import { useState, useRef, useEffect } from 'react';
import { chatAPI } from '../services/api';
import '../index.css';

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setError('');

    const newUserMessage = { role: 'user', content: userMessage };
    setMessages((prev) => [...prev, newUserMessage]);
    setLoading(true);

    try {
      const response = await chatAPI.sendMessage(userMessage, messages);
      const data = response.data;

      if (data.code === 200) {
        const assistantMessage = { role: 'assistant', content: data.data.message };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        setError(data.message || 'Failed to get response');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto" style={{ padding: '1rem 1.5rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.875rem', fontWeight: 700, color: '#111827' }}>AI Nutrition Coach</h1>
        <p style={{ marginTop: '0.5rem', color: '#4b5563' }}>Ask me anything about your nutrition and health goals</p>
      </div>

      {error && <div className="alert-error">{error}</div>}

      <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '600px', padding: 0 }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {messages.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '2rem' }}>
              <p style={{ fontSize: '1.125rem' }}>Start a conversation with your AI nutrition coach!</p>
              <p style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>Try asking:</p>
              <ul style={{ marginTop: '0.5rem', fontSize: '0.875rem', listStyle: 'none', padding: 0 }}>
                <li>"What are my daily calorie needs?"</li>
                <li>"How many calories have I consumed today?"</li>
                <li>"What should I eat to reach my goals?"</li>
              </ul>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                <div
                  style={{
                    maxWidth: '28rem',
                    padding: '0.5rem 1rem',
                    borderRadius: '0.5rem',
                    backgroundColor: msg.role === 'user' ? '#16a34a' : '#e5e7eb',
                    color: msg.role === 'user' ? '#ffffff' : '#111827'
                  }}
                >
                  <p style={{ fontSize: '0.875rem', whiteSpace: 'pre-wrap', margin: 0 }}>{msg.content}</p>
                </div>
              </div>
            ))
          )}
          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{ backgroundColor: '#e5e7eb', color: '#111827', padding: '0.5rem 1rem', borderRadius: '0.5rem' }}>
                <p style={{ fontSize: '0.875rem', margin: 0 }}>Thinking...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div style={{ borderTop: '1px solid #e5e7eb', padding: '1rem' }}>
          <form onSubmit={handleSend} className="flex" style={{ gap: '0.5rem' }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              className="flex-1"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="btn-primary"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect, useRef } from 'react';
import { dailySummaryAPI, chatAPI } from '../services/api';
import { Link, useLocation } from 'react-router-dom';
import '../index.css';

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const location = useLocation();

  // Helper function to get today's date in YYYY-MM-DD format (local timezone)
  const getTodayDate = () => {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  };

  const isInitialMount = useRef(true);

  const fetchSummary = async () => {
    try {
      const response = await dailySummaryAPI.get();
      const data = response.data;
      if (data.code === 200) {
        setSummary(data.data);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load summary');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
    loadChatHistory();
  }, []);

  // Refetch summary when navigating to dashboard (skip initial mount)
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    if (location.pathname === '/' || location.pathname === '/dashboard') {
      fetchSummary();
    }
  }, [location.pathname]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const loadChatHistory = async () => {
    try {
      const response = await chatAPI.getHistory();
      if (response.data.code === 200) {
        const history = response.data.data.history || [];
        setChatMessages(history);
      }
    } catch (err) {
      console.error('Failed to load chat history from backend:', err);
      setChatMessages([]);
    }
  };

  const saveChatHistory = async (messages) => {
    try {
      await chatAPI.saveHistory(messages);
    } catch (err) {
      console.error('Failed to save chat history to backend:', err);
    }
  };

  const handleChatSend = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userMessage = chatInput.trim();
    setChatInput('');
    setError('');

    const newUserMessage = { role: 'user', content: userMessage };
    const updatedMessages = [...chatMessages, newUserMessage];
    setChatMessages(updatedMessages);
    saveChatHistory(updatedMessages); // Save user message immediately
    setChatLoading(true);

    try {
      const response = await chatAPI.sendMessage(userMessage, chatMessages);
      const data = response.data;

      if (data.code === 200) {
        const assistantMessage = { role: 'assistant', content: data.data.message };
        const updatedMessagesWithResponse = [...updatedMessages, assistantMessage];
        setChatMessages(updatedMessagesWithResponse);
        saveChatHistory(updatedMessagesWithResponse);
        setChatLoading(false);
      } else if (data.code === 202 && data.data.task_id) {
        // Background job started, poll for result
        pollTaskStatus(data.data.task_id, updatedMessages);
      } else {
        setError(data.message || 'Failed to get response');
        setChatLoading(false);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to send message. Please try again.');
      setChatLoading(false);
    }
  };

  const pollTaskStatus = async (taskId, currentMessages) => {
    const maxAttempts = 30;
    let attempts = 0;
    
    const poll = async () => {
      try {
        const response = await chatAPI.getTaskStatus(taskId);
        const data = response.data;
        
        if (data.code === 200) {
          const assistantMessage = { role: 'assistant', content: data.data.message };
          const updatedMessagesWithResponse = [...currentMessages, assistantMessage];
          setChatMessages(updatedMessagesWithResponse);
          saveChatHistory(updatedMessagesWithResponse);
          setChatLoading(false);
        } else if (data.code === 202 && attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 1000);
        } else {
          setError('Request timed out. Please try again.');
          setChatLoading(false);
        }
      } catch (err) {
        if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 1000);
        } else {
          setError('Failed to get response. Please try again.');
          setChatLoading(false);
        }
      }
    };
    
    poll();
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (error) {
    return <div className="alert-error">{error}</div>;
  }

  return (
    <div style={{ padding: '1rem 1.5rem', minHeight: '100vh', background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.875rem', fontWeight: 700, color: '#111827' }}>Dashboard</h1>
        <p style={{ marginTop: '0.5rem', color: '#4b5563' }}>Your daily nutrition overview</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4" style={{ gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card">
          <div className="flex items-center">
            <div style={{ flexShrink: 0, backgroundColor: '#fee2e2', borderRadius: '0.375rem', padding: '0.75rem' }}>
              <span style={{ fontSize: '1.5rem' }}>🔥</span>
            </div>
            <div style={{ marginLeft: '1rem' }}>
              <p style={{ fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>Calories</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827' }}>{summary?.calories || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div style={{ flexShrink: 0, backgroundColor: '#dbeafe', borderRadius: '0.375rem', padding: '0.75rem' }}>
              <span style={{ fontSize: '1.5rem' }}>💪</span>
            </div>
            <div style={{ marginLeft: '1rem' }}>
              <p style={{ fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>Protein (g)</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827' }}>{summary?.protein || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div style={{ flexShrink: 0, backgroundColor: '#fef9c3', borderRadius: '0.375rem', padding: '0.75rem' }}>
              <span style={{ fontSize: '1.5rem' }}>🍞</span>
            </div>
            <div style={{ marginLeft: '1rem' }}>
              <p style={{ fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>Carbs (g)</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827' }}>{summary?.carbs || 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div style={{ flexShrink: 0, backgroundColor: '#dcfce7', borderRadius: '0.375rem', padding: '0.75rem' }}>
              <span style={{ fontSize: '1.5rem' }}>🥑</span>
            </div>
            <div style={{ marginLeft: '1rem' }}>
              <p style={{ fontSize: '0.875rem', fontWeight: 500, color: '#6b7280' }}>Fat (g)</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827' }}>{summary?.fat || 0}</p>
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
        <Link to="/food-log" className="btn-primary" style={{ textDecoration: 'none', display: 'inline-block', padding: '0.75rem 2rem', fontSize: '1rem' }}>
          Add Food Log
        </Link>
      </div>

      <div className="card" style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827', marginBottom: '1rem' }}>AI Nutrition Coach</h2>
        <div style={{ display: 'flex', flexDirection: 'column', height: '400px', padding: 0 }}>
          <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {chatMessages.length === 0 ? (
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
              chatMessages.map((msg, idx) => (
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
            {chatLoading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{ backgroundColor: '#e5e7eb', color: '#111827', padding: '0.5rem 1rem', borderRadius: '0.5rem' }}>
                  <p style={{ fontSize: '0.875rem', margin: 0 }}>Thinking...</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div style={{ borderTop: '1px solid #e5e7eb', padding: '1rem' }}>
            <form onSubmit={handleChatSend} className="flex" style={{ gap: '0.5rem' }}>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Type your message..."
                className="flex-1"
                disabled={chatLoading}
              />
              <button
                type="submit"
                disabled={chatLoading || !chatInput.trim()}
                className="btn-primary"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

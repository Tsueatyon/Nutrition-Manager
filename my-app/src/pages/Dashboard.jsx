import { useState, useEffect } from 'react';
import { dailySummaryAPI } from '../services/api';
import { Link } from 'react-router-dom';
import '../index.css';

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Helper function to get today's date in YYYY-MM-DD format (local timezone)
  const getTodayDate = () => {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  };

  useEffect(() => {
    fetchSummary();
  }, []);

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
    <div style={{ padding: '1rem 1.5rem' }}>
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

      <div className="grid grid-cols-1 md:grid-cols-2" style={{ gap: '1.5rem' }}>
        <div className="card">
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827', marginBottom: '1rem' }}>Quick Actions</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <Link to="/food-log" className="btn-primary" style={{ textAlign: 'center', textDecoration: 'none', display: 'block' }}>
              Add Food Entry
            </Link>
            <Link to="/chat" className="btn-secondary" style={{ textAlign: 'center', textDecoration: 'none', display: 'block', backgroundColor: '#2563eb' }}>
              Ask AI Coach
            </Link>
            <Link to="/profile" className="btn-secondary" style={{ textAlign: 'center', textDecoration: 'none', display: 'block' }}>
              Update Profile
            </Link>
          </div>
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827', marginBottom: '1rem' }}>Date</h2>
          <p style={{ fontSize: '1.125rem', color: '#4b5563' }}>{summary?.date || getTodayDate()}</p>
        </div>
      </div>
    </div>
  );
}

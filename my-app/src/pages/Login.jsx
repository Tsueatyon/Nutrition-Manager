import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import '../index.css';

export default function LoginPage({ setIsAuthenticated }) {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.login(formData);
      const data = response.data;

      if (data.code === 200) {
        localStorage.setItem('token', data.data.token);
        localStorage.setItem('user', JSON.stringify(data.data.user));
        setIsAuthenticated(true);
        navigate('/');
      } else {
        setError(data.message || 'Login failed');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50" style={{ padding: '3rem 1rem' }}>
      <div className="max-w-md w-full" style={{ marginTop: '2rem', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '1.875rem', fontWeight: 800, color: '#111827' }}>
            Sign in to your account
          </h2>
        </div>
        <form style={{ marginTop: '2rem' }} onSubmit={handleSubmit}>
          {error && (
            <div className="alert-error">
              {error}
            </div>
          )}
          <div style={{ marginBottom: '1.5rem' }}>
            <div>
              <label htmlFor="username" className="sr-only">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                style={{ 
                  borderRadius: '0.375rem 0.375rem 0 0',
                  borderBottom: 'none'
                }}
                placeholder="Username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                style={{ 
                  borderRadius: '0 0 0.375rem 0.375rem',
                  marginTop: '-1px'
                }}
                placeholder="Password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full"
              style={{ 
                width: '100%',
                display: 'flex',
                justifyContent: 'center',
                padding: '0.5rem 1rem'
              }}
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>

          <div className="text-center" style={{ marginTop: '1rem' }}>
            <Link to="/register" style={{ color: '#16a34a' }}>
              Don't have an account? Register
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}

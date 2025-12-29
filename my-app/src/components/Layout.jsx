import { Link, useLocation, useNavigate } from 'react-router-dom';
import '../index.css';

export default function AppLayout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/food-log', label: 'Food Log', icon: '🍎' },
    { path: '/history', label: 'History', icon: '📈' },
    { path: '/profile', label: 'Profile', icon: '👤' },
    { path: '/chat', label: 'AI Coach', icon: '💬' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav style={{ backgroundColor: '#ffffff', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)', borderBottom: '1px solid #e5e7eb' }}>
        <div className="max-w-7xl mx-auto px-4" style={{ paddingLeft: '1rem', paddingRight: '1rem' }}>
          <div className="flex justify-between" style={{ height: '4rem' }}>
            <div className="flex">
              <div style={{ flexShrink: 0, display: 'flex', alignItems: 'center' }}>
                <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#16a34a' }}>Nutrition App</h1>
              </div>
              <div className="desktop-nav" style={{ marginLeft: '1.5rem', gap: '2rem' }}>
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      padding: '0.25rem 0.25rem 0.25rem 0.25rem',
                      borderBottom: `2px solid ${location.pathname === item.path ? '#22c55e' : 'transparent'}`,
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      color: location.pathname === item.path ? '#111827' : '#6b7280',
                      textDecoration: 'none'
                    }}
                  >
                    <span style={{ marginRight: '0.5rem' }}>{item.icon}</span>
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center">
              <button
                onClick={handleLogout}
                style={{
                  color: '#6b7280',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  border: 'none',
                  background: 'transparent',
                  cursor: 'pointer'
                }}
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        <div className="mobile-menu">
          <div style={{ paddingTop: '0.5rem', paddingBottom: '0.75rem' }}>
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  display: 'block',
                  paddingLeft: '0.75rem',
                  paddingRight: '1rem',
                  paddingTop: '0.5rem',
                  paddingBottom: '0.5rem',
                  borderLeft: `4px solid ${location.pathname === item.path ? '#22c55e' : 'transparent'}`,
                  fontSize: '1rem',
                  fontWeight: 500,
                  backgroundColor: location.pathname === item.path ? '#f0fdf4' : 'transparent',
                  color: location.pathname === item.path ? '#15803d' : '#6b7280',
                  textDecoration: 'none'
                }}
              >
                <span style={{ marginRight: '0.5rem' }}>{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="max-w-7xl mx-auto" style={{ paddingTop: '1.5rem', paddingBottom: '1.5rem', paddingLeft: '1.5rem', paddingRight: '1.5rem' }}>
        {children}
      </main>
    </div>
  );
}

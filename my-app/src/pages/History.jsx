import { useState, useEffect } from 'react';
import { historyAPI } from '../services/api';
import '../index.css';

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [dailyNeeds, setDailyNeeds] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const response = await historyAPI.get30Days();
      const data = response.data;
      if (data.code === 200) {
        setHistory(data.data.history || []);
        setDailyNeeds(data.data.daily_needs || {});
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    // Get today's date in YYYY-MM-DD format (local timezone)
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    
    // Get yesterday's date in YYYY-MM-DD format
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, '0')}-${String(yesterday.getDate()).padStart(2, '0')}`;
    
    // Compare date strings directly to avoid timezone issues
    if (dateStr === todayStr) {
      return 'Today';
    } else if (dateStr === yesterdayStr) {
      return 'Yesterday';
    } else {
      // Parse the date string and format it
      const [year, month, day] = dateStr.split('-');
      const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const getPercentage = (actual, optimal) => {
    if (actual === null || actual === undefined) return null;
    if (optimal === 0) return 0;
    return Math.round((actual / optimal) * 100);
  };

  const getStatusColor = (percentage) => {
    if (percentage === null) return '#9ca3af'; // gray for no data
    if (percentage < 70) return '#ef4444'; // red for under
    if (percentage > 130) return '#f59e0b'; // orange for over
    return '#10b981'; // green for good
  };

  const getStatusText = (percentage) => {
    if (percentage === null) return 'No data';
    if (percentage < 70) return 'Low';
    if (percentage > 130) return 'High';
    return 'Good';
  };

  if (loading) {
    return (
      <div className="loading" style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="text-lg" style={{ marginBottom: '0.5rem' }}>Loading...</div>
          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>Fetching your 30-day nutrition history</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem 1.5rem' }}>
        <div className="alert-error">{error}</div>
      </div>
    );
  }

  return (
    <div style={{ 
      padding: '2rem 1.5rem', 
      maxWidth: '1400px', 
      margin: '0 auto',
      minHeight: 'calc(100vh - 200px)'
    }}>
      {/* Header Section */}
      <div style={{ 
        marginBottom: '2.5rem',
        borderBottom: '2px solid #e5e7eb',
        paddingBottom: '1.5rem'
      }}>
        <h1 style={{ 
          fontSize: '2.25rem', 
          fontWeight: 700, 
          color: '#111827',
          marginBottom: '0.5rem',
          letterSpacing: '-0.025em'
        }}>
          30-Day Nutrition History
        </h1>
        <p style={{ 
          fontSize: '1.125rem', 
          color: '#6b7280',
          lineHeight: '1.6'
        }}>
          Track your daily intake compared to your optimal nutrition goals
        </p>
      </div>

      {/* Daily Needs Summary Card */}
      {dailyNeeds && (
        <div style={{
          backgroundColor: '#f0f9ff',
          border: '1px solid #bae6fd',
          borderRadius: '0.75rem',
          padding: '1.5rem',
          marginBottom: '2rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1.5rem'
        }}>
          <div>
            <div style={{ fontSize: '0.875rem', fontWeight: 500, color: '#0369a1', marginBottom: '0.5rem' }}>
              Daily Calorie Goal
            </div>
            <div style={{ fontSize: '1.875rem', fontWeight: 700, color: '#0c4a6e' }}>
              {dailyNeeds.calories?.toLocaleString() || 'N/A'}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', fontWeight: 500, color: '#0369a1', marginBottom: '0.5rem' }}>
              Protein Goal
            </div>
            <div style={{ fontSize: '1.875rem', fontWeight: 700, color: '#0c4a6e' }}>
              {dailyNeeds.protein_g || 'N/A'}g
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', fontWeight: 500, color: '#0369a1', marginBottom: '0.5rem' }}>
              Carbs Goal
            </div>
            <div style={{ fontSize: '1.875rem', fontWeight: 700, color: '#0c4a6e' }}>
              {dailyNeeds.carbs_g || 'N/A'}g
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', fontWeight: 500, color: '#0369a1', marginBottom: '0.5rem' }}>
              Fat Goal
            </div>
            <div style={{ fontSize: '1.875rem', fontWeight: 700, color: '#0c4a6e' }}>
              {dailyNeeds.fat_g || 'N/A'}g
            </div>
          </div>
        </div>
      )}

      {/* History Table */}
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '0.75rem',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        overflow: 'hidden'
      }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ 
                backgroundColor: '#f9fafb',
                borderBottom: '2px solid #e5e7eb'
              }}>
                <th style={{ 
                  padding: '1rem 1.25rem',
                  textAlign: 'left',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#374151',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  Date
                </th>
                <th style={{ 
                  padding: '1rem 1.25rem',
                  textAlign: 'right',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#374151',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  Calories
                </th>
                <th style={{ 
                  padding: '1rem 1.25rem',
                  textAlign: 'right',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#374151',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  Protein (g)
                </th>
                <th style={{ 
                  padding: '1rem 1.25rem',
                  textAlign: 'right',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#374151',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  Carbs (g)
                </th>
                <th style={{ 
                  padding: '1rem 1.25rem',
                  textAlign: 'right',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#374151',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  Fat (g)
                </th>
                <th style={{ 
                  padding: '1rem 1.25rem',
                  textAlign: 'center',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#374151',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {history.map((day, index) => {
                const calPercentage = getPercentage(day.calories, day.optimal?.calories);
                const hasData = day.calories !== null && day.calories !== undefined;
                
                return (
                  <tr 
                    key={day.date}
                    style={{
                      borderBottom: index < history.length - 1 ? '1px solid #e5e7eb' : 'none',
                      transition: 'background-color 0.2s',
                      ':hover': { backgroundColor: '#f9fafb' }
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f9fafb'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <td style={{ 
                      padding: '1rem 1.25rem',
                      fontSize: '0.9375rem',
                      fontWeight: 500,
                      color: '#111827'
                    }}>
                      {formatDate(day.date)}
                    </td>
                    <td style={{ 
                      padding: '1rem 1.25rem',
                      textAlign: 'right',
                      fontSize: '0.9375rem',
                      color: hasData ? '#111827' : '#9ca3af',
                      fontFamily: 'monospace'
                    }}>
                      {hasData ? day.calories?.toLocaleString() || 0 : (
                        <span style={{ fontStyle: 'italic', color: '#9ca3af' }}>No data</span>
                      )}
                      {hasData && day.optimal?.calories && (
                        <div style={{ 
                          fontSize: '0.75rem', 
                          color: '#6b7280',
                          marginTop: '0.25rem'
                        }}>
                          / {day.optimal.calories.toLocaleString()}
                        </div>
                      )}
                    </td>
                    <td style={{ 
                      padding: '1rem 1.25rem',
                      textAlign: 'right',
                      fontSize: '0.9375rem',
                      color: hasData ? '#111827' : '#9ca3af',
                      fontFamily: 'monospace'
                    }}>
                      {hasData ? day.protein?.toFixed(1) || 0 : (
                        <span style={{ fontStyle: 'italic', color: '#9ca3af' }}>No data</span>
                      )}
                      {hasData && day.optimal?.protein_g && (
                        <div style={{ 
                          fontSize: '0.75rem', 
                          color: '#6b7280',
                          marginTop: '0.25rem'
                        }}>
                          / {day.optimal.protein_g}g
                        </div>
                      )}
                    </td>
                    <td style={{ 
                      padding: '1rem 1.25rem',
                      textAlign: 'right',
                      fontSize: '0.9375rem',
                      color: hasData ? '#111827' : '#9ca3af',
                      fontFamily: 'monospace'
                    }}>
                      {hasData ? day.carbs?.toFixed(1) || 0 : (
                        <span style={{ fontStyle: 'italic', color: '#9ca3af' }}>No data</span>
                      )}
                      {hasData && day.optimal?.carbs_g && (
                        <div style={{ 
                          fontSize: '0.75rem', 
                          color: '#6b7280',
                          marginTop: '0.25rem'
                        }}>
                          / {day.optimal.carbs_g}g
                        </div>
                      )}
                    </td>
                    <td style={{ 
                      padding: '1rem 1.25rem',
                      textAlign: 'right',
                      fontSize: '0.9375rem',
                      color: hasData ? '#111827' : '#9ca3af',
                      fontFamily: 'monospace'
                    }}>
                      {hasData ? day.fat?.toFixed(1) || 0 : (
                        <span style={{ fontStyle: 'italic', color: '#9ca3af' }}>No data</span>
                      )}
                      {hasData && day.optimal?.fat_g && (
                        <div style={{ 
                          fontSize: '0.75rem', 
                          color: '#6b7280',
                          marginTop: '0.25rem'
                        }}>
                          / {day.optimal.fat_g}g
                        </div>
                      )}
                    </td>
                    <td style={{ 
                      padding: '1rem 1.25rem',
                      textAlign: 'center'
                    }}>
                      {calPercentage !== null ? (
                        <span style={{
                          display: 'inline-block',
                          padding: '0.25rem 0.75rem',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          backgroundColor: getStatusColor(calPercentage) + '20',
                          color: getStatusColor(calPercentage)
                        }}>
                          {calPercentage}%
                        </span>
                      ) : (
                        <span style={{
                          display: 'inline-block',
                          padding: '0.25rem 0.75rem',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          backgroundColor: '#f3f4f6',
                          color: '#6b7280',
                          fontStyle: 'italic'
                        }}>
                          No data
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div style={{
        marginTop: '2rem',
        padding: '1rem',
        backgroundColor: '#f9fafb',
        borderRadius: '0.5rem',
        fontSize: '0.875rem',
        color: '#6b7280'
      }}>
        <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#374151' }}>
          Status Guide:
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
          <span>
            <span style={{ 
              display: 'inline-block',
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: '#10b981',
              marginRight: '0.5rem',
              verticalAlign: 'middle'
            }}></span>
            Good (70-130%)
          </span>
          <span>
            <span style={{ 
              display: 'inline-block',
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: '#ef4444',
              marginRight: '0.5rem',
              verticalAlign: 'middle'
            }}></span>
            Low (&lt;70%)
          </span>
          <span>
            <span style={{ 
              display: 'inline-block',
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: '#f59e0b',
              marginRight: '0.5rem',
              verticalAlign: 'middle'
            }}></span>
            High (&gt;130%)
          </span>
          <span>
            <span style={{ 
              display: 'inline-block',
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: '#9ca3af',
              marginRight: '0.5rem',
              verticalAlign: 'middle'
            }}></span>
            No data
          </span>
        </div>
      </div>
    </div>
  );
}


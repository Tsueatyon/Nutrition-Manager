import { useState, useEffect } from 'react';
import { foodLogAPI } from '../services/api';
import '../index.css';

export default function FoodLogPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingLog, setEditingLog] = useState(null);
  // Helper function to get today's date in YYYY-MM-DD format (local timezone)
  const getTodayDate = () => {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  };

  const [formData, setFormData] = useState({
    food_name: '',
    quantity: '',
    intake_date: getTodayDate(),
    meal_type: 'breakfast',
  });

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await foodLogAPI.getAll();
      const data = response.data;
      if (data.code === 200) {
        setLogs(data.data || []);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load food logs');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const payload = {
        ...formData,
        quantity: parseFloat(formData.quantity),
      };

      let response;
      if (editingLog) {
        response = await foodLogAPI.update({ id: editingLog.id, ...payload });
      } else {
        response = await foodLogAPI.create(payload);
      }

      const data = response.data;
      if (data.code === 200) {
        setShowAddForm(false);
        setEditingLog(null);
        setFormData({
          food_name: '',
          quantity: '',
          intake_date: getTodayDate(),
          meal_type: 'breakfast',
        });
        fetchLogs();
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save food log');
    }
  };

  const handleEdit = (log) => {
    setEditingLog(log);
    setFormData({
      food_name: log.food_name || '',
      quantity: log.quantity || '',
      intake_date: log.intake_date || getTodayDate(),
      meal_type: log.meal_type || 'breakfast',
    });
    setShowAddForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this entry?')) {
      return;
    }

    try {
      const response = await foodLogAPI.delete({ id });
      const data = response.data;
      if (data.code === 200) {
        fetchLogs();
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to delete food log');
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '1rem 1.5rem' }}>
      <div className="flex justify-between items-center" style={{ marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 700, color: '#111827' }}>Food Log</h1>
          <p style={{ marginTop: '0.5rem', color: '#4b5563' }}>Track your daily food intake</p>
        </div>
        <button
          onClick={() => {
            setShowAddForm(true);
            setEditingLog(null);
            setFormData({
              food_name: '',
              quantity: '',
              intake_date: getTodayDate(),
              meal_type: 'breakfast',
            });
          }}
          className="btn-primary"
        >
          Add Entry
        </button>
      </div>

      {error && <div className="alert-error">{error}</div>}

      {showAddForm && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827', marginBottom: '1rem' }}>
            {editingLog ? 'Edit Entry' : 'Add Food Entry'}
          </h2>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label htmlFor="food_name" style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: '#374151', marginBottom: '0.25rem' }}>
                Food Name
              </label>
              <input
                id="food_name"
                type="text"
                required
                placeholder="e.g., Apple, Chicken Breast"
                value={formData.food_name}
                onChange={(e) => setFormData({ ...formData, food_name: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2" style={{ gap: '1rem' }}>
              <div>
                <label htmlFor="quantity" style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: '#374151', marginBottom: '0.25rem' }}>
                  Quantity (grams)
                </label>
                <input
                  id="quantity"
                  type="number"
                  step="0.1"
                  required
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                />
              </div>
              <div>
                <label htmlFor="intake_date" style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: '#374151', marginBottom: '0.25rem' }}>
                  Date
                </label>
                <input
                  id="intake_date"
                  type="date"
                  required
                  value={formData.intake_date}
                  onChange={(e) => setFormData({ ...formData, intake_date: e.target.value })}
                />
              </div>
            </div>
            <div>
              <label htmlFor="meal_type" style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: '#374151', marginBottom: '0.25rem' }}>
                Meal Type
              </label>
              <select
                id="meal_type"
                value={formData.meal_type}
                onChange={(e) => setFormData({ ...formData, meal_type: e.target.value })}
              >
                <option value="breakfast">Breakfast</option>
                <option value="lunch">Lunch</option>
                <option value="dinner">Dinner</option>
                <option value="snack">Snack</option>
              </select>
            </div>
            <div className="flex" style={{ gap: '0.5rem' }}>
              <button type="submit" className="btn-primary flex-1">
                {editingLog ? 'Update' : 'Add'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddForm(false);
                  setEditingLog(null);
                }}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card" style={{ overflow: 'hidden', padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Food</th>
              <th>Quantity (g)</th>
              <th>Meal</th>
              <th className="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', color: '#6b7280' }}>
                  No food entries yet. Add your first entry!
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.intake_date}</td>
                  <td>{log.food_name || 'N/A'}</td>
                  <td>{log.quantity}</td>
                  <td className="capitalize">{log.meal_type || 'N/A'}</td>
                  <td className="text-right">
                    <button
                      onClick={() => handleEdit(log)}
                      style={{ color: '#16a34a', marginRight: '1rem', background: 'none', border: 'none', cursor: 'pointer' }}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(log.id)}
                      style={{ color: '#dc2626', background: 'none', border: 'none', cursor: 'pointer' }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

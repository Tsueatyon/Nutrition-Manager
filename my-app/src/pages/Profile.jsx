import { useState, useEffect } from 'react';
import { profileAPI } from '../services/api';
import '../index.css';

export default function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [formData, setFormData] = useState({
    age: '',
    sex: 'male',
    height_cm: '',
    weight_kg: '',
    activity_level: 'moderate',
    goal: 'maintain',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await profileAPI.get();
      const data = response.data;
      if (data.code === 200) {
        setProfile(data.data);
        setFormData({
          age: data.data.age || '',
          sex: data.data.sex || 'male',
          height_cm: data.data.height_cm || '',
          weight_kg: data.data.weight_kg || '',
          activity_level: data.data.activity_level || 'moderate',
          goal: data.data.goal || 'maintain',
        });
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSaving(true);

    try {
      const payload = {
        ...formData,
        age: parseInt(formData.age),
        height_cm: parseFloat(formData.height_cm),
        weight_kg: parseFloat(formData.weight_kg),
      };

      const response = await profileAPI.update(payload);
      const data = response.data;

      if (data.code === 200) {
        setSuccess('Profile updated successfully!');
        await fetchProfile();
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update profile');
    } finally {
      setSaving(false);
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
    <div className="max-w-2xl mx-auto" style={{ padding: '1rem 1.5rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.875rem', fontWeight: 700, color: '#111827' }}>Profile</h1>
        <p style={{ marginTop: '0.5rem', color: '#4b5563' }}>Manage your profile information</p>
      </div>

      {error && <div className="alert-error">{error}</div>}
      {success && <div className="alert-success">{success}</div>}

      <form onSubmit={handleSubmit} className="card">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label htmlFor="username" style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: '#374151', marginBottom: '0.25rem' }}>
              Username
            </label>
            <input
              id="username"
              type="text"
              value={profile?.username || ''}
              disabled
              style={{ backgroundColor: '#f9fafb', color: '#6b7280' }}
            />
          </div>

          <div>
            <label htmlFor="age" style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: '#374151', marginBottom: '0.25rem' }}>
              Age
            </label>
            <input
              id="age"
              name="age"
              type="number"
              min="1"
              max="150"
              required
              placeholder="Enter your age"
              value={formData.age}
              onChange={(e) => setFormData({ ...formData, age: e.target.value })}
            />
          </div>

          <div>
            <label htmlFor="sex" style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: '#374151', marginBottom: '0.25rem' }}>
              Sex
            </label>
            <select
              id="sex"
              name="sex"
              required
              value={formData.sex}
              onChange={(e) => setFormData({ ...formData, sex: e.target.value })}
            >
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </div>

          <div className="grid grid-cols-2" style={{ gap: '1rem' }}>
            <div>
              <label htmlFor="height_cm" style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: '#374151', marginBottom: '0.25rem' }}>
                Height (cm)
              </label>
              <input
                id="height_cm"
                name="height_cm"
                type="number"
                step="0.1"
                required
                value={formData.height_cm}
                onChange={(e) => setFormData({ ...formData, height_cm: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="weight_kg" style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: '#374151', marginBottom: '0.25rem' }}>
                Weight (kg)
              </label>
              <input
                id="weight_kg"
                name="weight_kg"
                type="number"
                step="0.1"
                required
                value={formData.weight_kg}
                onChange={(e) => setFormData({ ...formData, weight_kg: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label htmlFor="activity_level" style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: '#374151', marginBottom: '0.25rem' }}>
              Activity Level
            </label>
            <select
              id="activity_level"
              name="activity_level"
              required
              value={formData.activity_level}
              onChange={(e) => setFormData({ ...formData, activity_level: e.target.value })}
            >
              <option value="sedentary">Sedentary</option>
              <option value="light">Light</option>
              <option value="moderate">Moderate</option>
              <option value="active">Active</option>
              <option value="extra">Extra Active</option>
            </select>
          </div>

          <div>
            <label htmlFor="goal" style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, color: '#374151', marginBottom: '0.25rem' }}>
              Goal
            </label>
            <select
              id="goal"
              name="goal"
              required
              value={formData.goal}
              onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
            >
              <option value="cut">Cut (Lose Weight)</option>
              <option value="maintain">Maintain Weight</option>
              <option value="bulk">Bulk (Gain Weight)</option>
            </select>
          </div>
        </div>

        <div style={{ marginTop: '1.5rem' }}>
          <button type="submit" disabled={saving} className="btn-primary w-full" style={{ width: '100%' }}>
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
}

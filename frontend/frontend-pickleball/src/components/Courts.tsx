import React, { useEffect, useState } from 'react'
import api from '../api'

interface Court {
  id: number
  name: string
  address?: string
  num_courts?: number
  indoor?: boolean
  notes?: string
  hours?: string
}

export default function Courts() {
  const [courts, setCourts] = useState<Court[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [name, setName] = useState('')
  const [address, setAddress] = useState('')
  const [numCourts, setNumCourts] = useState(1)
  const [indoor, setIndoor] = useState(false)
  const [notes, setNotes] = useState('')

  async function loadCourts() {
    try {
      setLoading(true)
      const res = await api.get('/api/courts/')
      setCourts(res.data)
      setError('')
    } catch (err: any) {
      setError('Failed to load courts: ' + (err.message || 'Unknown error'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCourts()
  }, [])

  async function handleCreateCourt(e: React.FormEvent) {
    e.preventDefault()
    try {
      setError('')
      const payload = { name, address, num_courts: numCourts, indoor, notes }
      const res = await api.post('/api/courts/', payload)
      setCourts([res.data, ...courts])
      setName('')
      setAddress('')
      setNumCourts(1)
      setIndoor(false)
      setNotes('')
    } catch (err: any) {
      setError('Failed to create court: ' + (err.response?.data?.message || err.message))
    }
  }

  return (
    <div>
      <h2>🏐 Courts Management</h2>
      {error && <div className="error">{error}</div>}

      <form onSubmit={handleCreateCourt}>
        <h3>Create New Court</h3>
        <label htmlFor="name">Court Name *</label>
        <input
          id="name"
          type="text"
          placeholder="e.g., Downtown Community Center"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <label htmlFor="address">Address</label>
        <input
          id="address"
          type="text"
          placeholder="e.g., 123 Main St, City, State"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
        />
        <label htmlFor="numCourts">Number of Courts</label>
        <input
          id="numCourts"
          type="number"
          placeholder="Number of Courts"
          value={numCourts}
          onChange={(e) => setNumCourts(Number(e.target.value))}
          min={1}
        />
        <label>
          <input
            type="checkbox"
            checked={indoor}
            onChange={(e) => setIndoor(e.target.checked)}
          />
          Indoor
        </label>
        <label htmlFor="notes">Notes</label>
        <textarea
          id="notes"
          placeholder="e.g., Lighting available, Free parking"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
        />
        <button type="submit">➕ Create Court</button>
        <button type="button" className="secondary" onClick={loadCourts}>
          🔄 Refresh
        </button>
      </form>

      {loading ? (
        <div className="loading">⏳ Loading courts...</div>
      ) : (
        <div>
          <h3>All Courts ({courts.length})</h3>
          {courts.length === 0 ? (
            <p style={{ padding: '2rem', textAlign: 'center', color: '#7f8c8d' }}>
              No courts found. Create one above.
            </p>
          ) : (
            <ul>
              {courts.map((c) => (
                <li key={c.id}>
                  <strong>{c.name}</strong>
                  {c.address && <p>📍 <strong>Address:</strong> {c.address}</p>}
                  <p>
                    {c.indoor ? '🏢 Indoor' : '🌳 Outdoor'} • 
                    {c.num_courts} court{c.num_courts !== 1 ? 's' : ''} •
                    ID: {c.id}
                  </p>
                  {c.notes && <p>📝 <strong>Notes:</strong> {c.notes}</p>}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
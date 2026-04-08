import React, { useEffect, useState } from 'react'
import api from '../api'

interface Court {
  id: number
  name: string
  address?: string
  num_courts?: number
  indoor?: boolean
}

interface Visit {
  id: number
  court_id: number
  visited_at: string
  crowdedness?: number
  notes?: string
}

export default function Visits() {
  const [courts, setCourts] = useState<Court[]>([])
  const [visits, setVisits] = useState<Visit[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const [selectedCourtId, setSelectedCourtId] = useState<number | ''>('')
  const [searchCourtName, setSearchCourtName] = useState('')
  const [filteredCourts, setFilteredCourts] = useState<Court[]>([])
  const [showCourtDropdown, setShowCourtDropdown] = useState(false)
  
  const [crowdedness, setCrowdedness] = useState<number | ''>('')
  const [notes, setNotes] = useState('')

  // Load all courts on mount
  async function loadCourts() {
    try {
      const res = await api.get('/api/courts/')
      setCourts(res.data)
    } catch (err: any) {
      setError('Failed to load courts: ' + (err.message || 'Unknown error'))
    }
  }

  // Load all visits
  async function loadVisits() {
    try {
      setLoading(true)
      const res = await api.get('/api/visits/')
      setVisits(res.data)
      setError('')
    } catch (err: any) {
      setError('Failed to load visits: ' + (err.message || 'Unknown error'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCourts()
    loadVisits()
  }, [])

  // Filter courts based on search input
  useEffect(() => {
    if (searchCourtName.trim() === '') {
      setFilteredCourts(courts)
    } else {
      const filtered = courts.filter((court) =>
        court.name.toLowerCase().includes(searchCourtName.toLowerCase()) ||
        court.address?.toLowerCase().includes(searchCourtName.toLowerCase())
      )
      setFilteredCourts(filtered)
    }
  }, [searchCourtName, courts])

  // Handle court selection from dropdown
  function handleSelectCourt(court: Court) {
    setSelectedCourtId(court.id)
    setSearchCourtName(court.name)
    setShowCourtDropdown(false)
  }

  async function handleCreateVisit(e: React.FormEvent) {
    e.preventDefault()
    try {
      setError('')
      if (!selectedCourtId) {
        setError('Please select a court')
        return
      }
      const payload = {
        court_id: Number(selectedCourtId),
        crowdedness: crowdedness ? Number(crowdedness) : undefined,
        notes,
        visited_at: new Date().toISOString(),
      }
      const res = await api.post('/api/visits/', payload)
      setVisits([res.data, ...visits])
      setSelectedCourtId('')
      setSearchCourtName('')
      setCrowdedness('')
      setNotes('')
      setFilteredCourts(courts)
    } catch (err: any) {
      setError('Failed to create visit: ' + (err.response?.data?.message || err.message))
    }
  }

  const getCrowdColor = (crowd?: number) => {
    if (!crowd) return '#95a5a6'
    if (crowd <= 3) return '#27ae60'
    if (crowd <= 6) return '#f39c12'
    return '#e74c3c'
  }

  return (
    <div>
      <h2>📊 Visit Logging</h2>
      {error && <div className="error">{error}</div>}

      <form onSubmit={handleCreateVisit}>
        <h3>Log a New Visit</h3>
        
        <label htmlFor="courtSearch">Pickleball Court Name *</label>
        <div style={{ position: 'relative' }}>
          <input
            id="courtSearch"
            type="text"
            placeholder="Search court by name or address (e.g., Downtown Center)"
            value={searchCourtName}
            onChange={(e) => {
              setSearchCourtName(e.target.value)
              setShowCourtDropdown(true)
              if (!e.target.value) {
                setSelectedCourtId('')
              }
            }}
            onFocus={() => setShowCourtDropdown(true)}
            required
          />
          
          {/* Dropdown list */}
          {showCourtDropdown && filteredCourts.length > 0 && (
            <ul
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                background: 'white',
                border: '2px solid #3498db',
                borderTop: 'none',
                borderRadius: '0 0 8px 8px',
                listStyle: 'none',
                padding: '0',
                margin: '0',
                maxHeight: '250px',
                overflowY: 'auto',
                zIndex: 10,
              }}
            >
              {filteredCourts.map((court) => (
                <li
                  key={court.id}
                  onClick={() => handleSelectCourt(court)}
                  style={{
                    padding: '0.75rem 1rem',
                    cursor: 'pointer',
                    borderBottom: '1px solid #ecf0f1',
                    transition: 'background-color 0.3s ease',
                    backgroundColor: selectedCourtId === court.id ? '#e3f2fd' : 'white',
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLElement).style.backgroundColor = '#f0f0f0'
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLElement).style.backgroundColor =
                      selectedCourtId === court.id ? '#e3f2fd' : 'white'
                  }}
                >
                  <strong>{court.name}</strong>
                  {court.address && (
                    <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.9rem', color: '#7f8c8d' }}>
                      📍 {court.address}
                    </p>
                  )}
                  <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#95a5a6' }}>
                    {court.indoor ? '🏢 Indoor' : '🌳 Outdoor'} • {court.num_courts} court
                    {court.num_courts !== 1 ? 's' : ''} • ID: {court.id}
                  </p>
                </li>
              ))}
            </ul>
          )}

          {showCourtDropdown && searchCourtName && filteredCourts.length === 0 && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                background: 'white',
                border: '2px solid #e74c3c',
                borderTop: 'none',
                borderRadius: '0 0 8px 8px',
                padding: '1rem',
                color: '#e74c3c',
                textAlign: 'center',
                zIndex: 10,
              }}
            >
              No courts found matching "{searchCourtName}"
            </div>
          )}
        </div>

        {selectedCourtId && (
          <p style={{ color: '#27ae60', fontWeight: '600', marginBottom: '1rem' }}>
            ✅ Court selected: {courts.find((c) => c.id === selectedCourtId)?.name}
          </p>
        )}

        <label htmlFor="crowdedness">Crowdedness Level (1-10)</label>
        <input
          id="crowdedness"
          type="number"
          placeholder="Crowdedness (1-10)"
          value={crowdedness as any}
          onChange={(e) => setCrowdedness(e.target.value ? Number(e.target.value) : '')}
          min={1}
          max={10}
        />

        <label htmlFor="visitNotes">Visit Notes (Optional)</label>
        <textarea
          id="visitNotes"
          placeholder="e.g., Courts were well-lit, Good playing conditions"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
        />

        <button type="submit">✅ Log Visit</button>
        <button type="button" className="secondary" onClick={loadVisits}>
          🔄 Reload
        </button>
      </form>

      {loading ? (
        <div className="loading">⏳ Loading visits...</div>
      ) : (
        <div>
          <h3>Recent Visits ({visits.length})</h3>
          {visits.length === 0 ? (
            <p style={{ padding: '2rem', textAlign: 'center', color: '#7f8c8d' }}>
              No visits logged yet.
            </p>
          ) : (
            <ul>
              {visits.map((v) => {
                const court = courts.find((c) => c.id === v.court_id)
                return (
                  <li key={v.id}>
                    <strong>
                      {court?.name || `Court ${v.court_id}`}
                    </strong>
                    {court?.address && <p>📍 {court.address}</p>}
                    <p>📅 {new Date(v.visited_at).toLocaleString()}</p>
                    {v.crowdedness && (
                      <p>
                        👥 Crowdedness:{' '}
                        <span
                          style={{
                            color: getCrowdColor(v.crowdedness),
                            fontWeight: 'bold',
                          }}
                        >
                          {v.crowdedness}/10
                        </span>
                        {v.crowdedness <= 3 && ' (Not Crowded)'}
                        {v.crowdedness > 3 && v.crowdedness <= 6 && ' (Moderate)'}
                        {v.crowdedness > 6 && ' (Very Crowded)'}
                      </p>
                    )}
                    {v.notes && <p>📝 {v.notes}</p>}
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
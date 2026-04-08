import React, { useState } from 'react'
import api from '../api'

interface SearchResult {
  id: string
  name: string
  text: string
  metadata: Record<string, any>
  score: number
}

export default function AI() {
  const [activeTab, setActiveTab] = useState<'chat' | 'search' | 'rag' | 'upload'>('chat')
  
  // Chat state
  const [chatUserId, setChatUserId] = useState('user-1')
  const [chatMessage, setChatMessage] = useState('')
  const [chatReply, setChatReply] = useState('')
  const [chatMemory, setChatMemory] = useState<any>(null)
  const [chatLoading, setChatLoading] = useState(false)

  // Search state
  const [query, setQuery] = useState('')
  const [k, setK] = useState(5)
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchLoading, setSearchLoading] = useState(false)

  // RAG state
  const [ragQuery, setRagQuery] = useState('')
  const [ragK, setRagK] = useState(5)
  const [ragAnswer, setRagAnswer] = useState('')
  const [ragDocs, setRagDocs] = useState<SearchResult[]>([])
  const [ragLoading, setRagLoading] = useState(false)

  // Upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadLoading, setUploadLoading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')

  // Chat (LLM) - UPDATED
  async function handleChat(e: React.FormEvent) {
    e.preventDefault()
    if (!chatMessage.trim()) return

    try {
      setChatLoading(true)
      const params = new URLSearchParams()
      params.append('user_id', chatUserId)
      params.append('message', chatMessage)
      
      const res = await api.post('/api/ai/chat', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      setChatReply(res.data.reply || '')
      setChatMemory(res.data.memory || null)
      setChatMessage('')
    } catch (err: any) {
      setChatReply('❌ Error: ' + (err.response?.data?.message || err.message))
    } finally {
      setChatLoading(false)
    }
  }

  // Semantic Search (VectorDB)
  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim()) return

    try {
      setSearchLoading(true)
      const params = new URLSearchParams()
      params.append('query', query)
      params.append('k', String(k))
      
      const res = await api.post('/api/ai/semantic-search', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      setSearchResults(res.data.results || [])
    } catch (err: any) {
      setSearchResults([])
      alert('Search error: ' + (err.response?.data?.message || err.message))
    } finally {
      setSearchLoading(false)
    }
  }

  // RAG (VectorDB + LLM grounding)
  async function handleRAG(e: React.FormEvent) {
    e.preventDefault()
    if (!ragQuery.trim()) return

    try {
      setRagLoading(true)
      const params = new URLSearchParams()
      params.append('query', ragQuery)
      params.append('k', String(ragK))
      
      const res = await api.post('/api/ai/rag', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      setRagAnswer(res.data.answer || '')
      setRagDocs(res.data.source_docs || [])
    } catch (err: any) {
      setRagAnswer('❌ Error: ' + (err.response?.data?.message || err.message))
      setRagDocs([])
    } finally {
      setRagLoading(false)
    }
  }

  // Upload to Vector Store
  async function handleUpload(e: React.FormEvent) {
    e.preventDefault()
    if (!uploadFile) {
      setUploadStatus('❌ Please select a file')
      return
    }

    try {
      setUploadLoading(true)
      const fd = new FormData()
      fd.append('file', uploadFile)
      fd.append('source', 'web-upload')
      
      const res = await api.post('/api/ai/load-text', fd, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      setUploadStatus(`✅ Successfully ingested ${res.data.ingested_chunks || 0} chunks`)
      setUploadFile(null)
    } catch (err: any) {
      setUploadStatus('❌ ' + (err.response?.data?.detail || err.response?.data?.message || err.message))
    } finally {
      setUploadLoading(false)
    }
  }

  return (
    <div>
      <h2>🤖 AI Tools</h2>
      
      <div className="tab-nav">
        <button
          className={activeTab === 'chat' ? 'active' : ''}
          onClick={() => setActiveTab('chat')}
        >
          💬 Chat (LLM)
        </button>
        <button
          className={activeTab === 'search' ? 'active' : ''}
          onClick={() => setActiveTab('search')}
        >
          🔍 Search (VectorDB)
        </button>
        <button
          className={activeTab === 'rag' ? 'active' : ''}
          onClick={() => setActiveTab('rag')}
        >
          📚 RAG (VectorDB + LLM)
        </button>
        <button
          className={activeTab === 'upload' ? 'active' : ''}
          onClick={() => setActiveTab('upload')}
        >
          📤 Upload Data
        </button>
      </div>

      {/* Chat Tab */}
      {activeTab === 'chat' && (
        <div>
          <form onSubmit={handleChat}>
            <h3>💬 Chat with AI Assistant</h3>
            <label htmlFor="userId">User ID</label>
            <input
              id="userId"
              type="text"
              placeholder="Your User ID"
              value={chatUserId}
              onChange={(e) => setChatUserId(e.target.value)}
            />
            <label htmlFor="message">Your Message</label>
            <textarea
              id="message"
              placeholder="Ask me anything about pickleball courts... (e.g., 'Which courts have the best reviews?')"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              rows={3}
            />
            <button type="submit" disabled={chatLoading}>
              {chatLoading ? '⏳ Sending...' : '📤 Send Message'}
            </button>
          </form>

          {chatReply && (
            <div style={{ background: 'linear-gradient(135deg, #e3f2fd 0%, #e8f5e9 100%)', padding: '1.5rem', borderRadius: '8px', marginTop: '1.5rem', borderLeft: '4px solid #3498db' }}>
              <h4>🤖 Assistant Reply:</h4>
              <p style={{ fontSize: '1.05rem', lineHeight: '1.8' }}>{chatReply}</p>
            </div>
          )}

          {chatMemory && (
            <div style={{ background: '#f8f8f8', padding: '1.5rem', borderRadius: '8px', marginTop: '1.5rem', borderLeft: '4px solid #95a5a6' }}>
              <h4>💾 Conversation Memory:</h4>
              <pre>{JSON.stringify(chatMemory, null, 2)}</pre>
            </div>
          )}
        </div>
      )}

      {/* Search Tab */}
      {activeTab === 'search' && (
        <div>
          <form onSubmit={handleSearch}>
            <h3>🔍 Semantic Search Database</h3>
            <label htmlFor="searchQuery">Search Query</label>
            <textarea
              id="searchQuery"
              placeholder="Enter your search query (e.g., 'Find free indoor courts near downtown')"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={2}
            />
            <label htmlFor="k">Number of Results</label>
            <input
              id="k"
              type="number"
              placeholder="Number of results (k)"
              value={k}
              onChange={(e) => setK(Number(e.target.value))}
              min={1}
              max={20}
            />
            <button type="submit" disabled={searchLoading}>
              {searchLoading ? '⏳ Searching...' : '🔎 Search'}
            </button>
          </form>

          {searchResults.length > 0 && (
            <div style={{ marginTop: '1.5rem' }}>
              <h3>📋 Search Results ({searchResults.length})</h3>
              <ul>
                {searchResults.map((result, idx) => (
                  <li key={result.id}>
                    <strong>#{idx + 1} - {result.name}</strong>
                    <p>{result.text}</p>
                    <p style={{ fontSize: '0.9rem', color: ' #3498db', fontWeight: 'bold' }}>
                      Relevance Score: {(result.score * 100).toFixed(1)}%
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* RAG Tab */}
      {activeTab === 'rag' && (
        <div>
          <form onSubmit={handleRAG}>
            <h3>📚 RAG - Ask Questions About Courts</h3>
            <label htmlFor="ragQuery">Your Question</label>
            <textarea
              id="ragQuery"
              placeholder="Ask a detailed question about pickleball courts (e.g., 'What are the opening hours of indoor courts with good lighting?')"
              value={ragQuery}
              onChange={(e) => setRagQuery(e.target.value)}
              rows={2}
            />
            <label htmlFor="ragK">Source Documents to Use</label>
            <input
              id="ragK"
              type="number"
              placeholder="Number of source docs (k)"
              value={ragK}
              onChange={(e) => setRagK(Number(e.target.value))}
              min={1}
              max={20}
            />
            <button type="submit" disabled={ragLoading}>
              {ragLoading ? '⏳ Generating...' : '💡 Get Answer'}
            </button>
          </form>

          {ragAnswer && (
            <div style={{ background: 'linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%)', padding: '1.5rem', borderRadius: '8px', marginTop: '1.5rem', borderLeft: '4px solid #27ae60' }}>
              <h4>✨ AI-Generated Answer:</h4>
              <p style={{ fontSize: '1.05rem', lineHeight: '1.8', color: '#1b5e20' }}>{ragAnswer}</p>
            </div>
          )}

          {ragDocs.length > 0 && (
            <div style={{ marginTop: '1.5rem' }}>
              <h4>📚 Source Documents ({ragDocs.length})</h4>
              <ul>
                {ragDocs.map((doc, idx) => (
                  <li key={doc.id}>
                    <strong>Source #{idx + 1}: {doc.name}</strong>
                    <p>{doc.text}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Upload Tab */}
      {activeTab === 'upload' && (
        <div>
          <form onSubmit={handleUpload}>
            <h3>📤 Upload Court Data to Vector Store</h3>
            <label htmlFor="fileInput">Select .txt File</label>
            <input
              id="fileInput"
              type="file"
              accept=".txt"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              required
            />
            <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.5rem' }}>
              💡 Tip: Upload a .txt file containing court information to ingest into the vector database. This data will be used for semantic search and RAG queries.
            </p>
            <button type="submit" disabled={uploadLoading}>
              {uploadLoading ? '⏳ Uploading...' : '✅ Upload & Ingest'}
            </button>
          </form>

          {uploadStatus && (
            <div
              style={{
                background: uploadStatus.startsWith('✅') ? 'linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%)' : 'linear-gradient(135deg, #ffebee 0%, #fff3e0 100%)',
                padding: '1.2rem',
                borderRadius: '8px',
                marginTop: '1.5rem',
                borderLeft: uploadStatus.startsWith('✅') ? '4px solid #27ae60' : '4px solid #e74c3c',
                color: uploadStatus.startsWith('✅') ? '#1b5e20' : '#c62828',
                fontWeight: '600',
              }}
            >
              {uploadStatus}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
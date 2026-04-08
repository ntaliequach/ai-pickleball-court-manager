import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Courts from './components/Courts.tsx'
import Visits from './components/Visits.tsx'
import AI from './components/AI.tsx'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <nav className="navbar">
        <h1>🏐 Pickleball Court Manager</h1>
        <ul>
          <li><Link to="/">Courts</Link></li>
          <li><Link to="/visits">Visits</Link></li>
          <li><Link to="/ai">AI Tools</Link></li>
        </ul>
      </nav>
      
      <main className="container">
        <Routes>
          <Route path="/" element={<Courts />} />
          <Route path="/visits" element={<Visits />} />
          <Route path="/ai" element={<AI />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

export default App

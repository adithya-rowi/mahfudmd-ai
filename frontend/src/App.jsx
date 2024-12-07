import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [input, setInput] = useState('')
  const [response, setResponse] = useState('')

  const handleSubmit = async () => {
    try {
      const res = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      })
      const data = await res.json()
      setResponse(data.response || 'No response')
    } catch (error) {
      console.error('Error:', error)
      setResponse('Error contacting backend')
    }
  }

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank" rel="noreferrer">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank" rel="noreferrer">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      
      <div className="card">
        <button onClick={() => setCount((c) => c + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
      </div>

      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>

      <hr />

      <div style={{ marginTop: '20px' }}>
        <input 
          type="text" 
          placeholder="Type your message" 
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          style={{ marginRight: '10px' }}
        />
        <button onClick={handleSubmit}>Send</button>
      </div>

      {response && (
        <div style={{ marginTop: '20px' }}>
          <strong>Response:</strong> {response}
        </div>
      )}
    </>
  )
}

export default App

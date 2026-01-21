import { useState, useEffect } from 'react'
import { Button } from '@conceptcast/ui'

function App() {
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    fetch('/api/')
      .then(res => res.json())
      .then(setData)
      .catch(console.error)
  }, [])

  return (
    <div style={{ padding: '20px', fontFamily: 'system-ui' }}>
      <h1>ConceptCast</h1>
      <div style={{ marginBottom: '20px' }}>
        <strong>Backend Status:</strong> {data?.message || 'Loading...'}{' '}
        {data?.status === 'ok' ? '✅' : '❌'}
      </div>
      <div>
        <h2>Shared UI Component:</h2>
        <Button variant="primary" onClick={() => alert('Clicked!')}>
          Click Me (From @conceptcast/ui)
        </Button>
      </div>
    </div>
  )
}

export default App

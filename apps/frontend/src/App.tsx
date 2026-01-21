import { useState } from 'react'
import { Button } from '@/components/ui'


function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div>
        <h1>ConceptCast</h1>
      </div>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
        <div style={{ marginTop: '20px' }}>
          <Button onClick={() => alert('Clicked!')}>
            Click Me (From Local UI)
          </Button>
        </div>
      </div>
    </>
  )
}

export default App

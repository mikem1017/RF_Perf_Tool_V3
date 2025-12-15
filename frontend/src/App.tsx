import { useState, useEffect } from 'react'
import './App.css'
import { healthCheck } from './services/api'
import DeviceManagement from './components/DeviceManagement'
import TestStageManagement from './components/TestStageManagement'
import RequirementSetEditor from './components/RequirementSetEditor'
import TestRunList from './components/TestRunList'

type Page = 'devices' | 'test-stages' | 'requirement-sets' | 'test-runs'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('devices')
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking')
  const [backendError, setBackendError] = useState<string>('')

  useEffect(() => {
    // Check backend health on mount
    const checkHealth = async () => {
      try {
        const result = await healthCheck()
        if (result.status === 'healthy') {
          setBackendStatus('connected')
          setBackendError('')
        } else {
          setBackendStatus('disconnected')
          setBackendError('Backend returned unexpected status')
        }
      } catch (error) {
        setBackendStatus('disconnected')
        setBackendError('Cannot connect to backend. Ensure backend is running on http://127.0.0.1:8000')
      }
    }
    checkHealth()
  }, [])

  const renderPage = () => {
    switch (currentPage) {
      case 'devices':
        return <DeviceManagement />
      case 'test-stages':
        return <TestStageManagement />
      case 'requirement-sets':
        return <RequirementSetEditor />
      case 'test-runs':
        return <TestRunList />
      default:
        return <div>Page not found</div>
    }
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>RF Performance Tool</h1>
        <p>Local-only RF test analysis application</p>
        <div className="backend-status">
          <span className={`status-indicator ${backendStatus}`}>
            {backendStatus === 'checking' && '⏳ Checking backend...'}
            {backendStatus === 'connected' && '✅ Backend connected'}
            {backendStatus === 'disconnected' && '❌ Backend disconnected'}
          </span>
          {backendError && <div className="backend-error">{backendError}</div>}
        </div>
      </header>
      
      <nav className="App-nav">
        <button
          className={currentPage === 'devices' ? 'active' : ''}
          onClick={() => setCurrentPage('devices')}
        >
          Devices
        </button>
        <button
          className={currentPage === 'test-stages' ? 'active' : ''}
          onClick={() => setCurrentPage('test-stages')}
        >
          Test Stages
        </button>
        <button
          className={currentPage === 'requirement-sets' ? 'active' : ''}
          onClick={() => setCurrentPage('requirement-sets')}
        >
          Requirement Sets
        </button>
        <button
          className={currentPage === 'test-runs' ? 'active' : ''}
          onClick={() => setCurrentPage('test-runs')}
        >
          Test Runs
        </button>
      </nav>

      <main className="App-main">
        {renderPage()}
      </main>
    </div>
  )
}

export default App

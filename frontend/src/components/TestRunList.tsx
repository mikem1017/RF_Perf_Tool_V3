import { useState, useEffect } from 'react'
import { api, handleApiError } from '../services/api'
import './TestRunList.css'

export default function TestRunList() {
  const [testRuns, setTestRuns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    loadTestRuns()
  }, [])

  const loadTestRuns = async () => {
    try {
      setLoading(true)
      const data = await api.testRuns.list()
      setTestRuns(data)
      setError('')
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="test-run-list">
      <h2>Test Runs</h2>
      {loading && <p>Loading test runs...</p>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && (
        <div>
          {testRuns.length === 0 ? (
            <p>No test runs found. Create a test run to get started.</p>
          ) : (
            <ul className="test-run-list-items">
              {testRuns.map((run) => (
                <li key={run.id}>
                  <strong>Test Run #{run.id}</strong> - Status: {run.status || 'unknown'}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}


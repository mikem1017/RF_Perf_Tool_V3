import { useState, useEffect } from 'react'
import { api, handleApiError } from '../services/api'
import './TestStageManagement.css'

export default function TestStageManagement() {
  const [stages, setStages] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    loadStages()
  }, [])

  const loadStages = async () => {
    try {
      setLoading(true)
      const data = await api.testStages.list()
      setStages(data)
      setError('')
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="test-stage-management">
      <h2>Test Stage Management</h2>
      {loading && <p>Loading test stages...</p>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && (
        <div>
          {stages.length === 0 ? (
            <p>No test stages found. Create a test stage to get started.</p>
          ) : (
            <ul className="stage-list">
              {stages.map((stage) => (
                <li key={stage.id}>
                  <strong>{stage.name}</strong>
                  {stage.description && <span> - {stage.description}</span>}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}


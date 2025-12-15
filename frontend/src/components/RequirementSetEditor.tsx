import { useState, useEffect } from 'react'
import { api, handleApiError } from '../services/api'
import './RequirementSetEditor.css'

export default function RequirementSetEditor() {
  const [requirementSets, setRequirementSets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    loadRequirementSets()
  }, [])

  const loadRequirementSets = async () => {
    try {
      setLoading(true)
      const data = await api.requirementSets.list()
      setRequirementSets(data)
      setError('')
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="requirement-set-editor">
      <h2>Requirement Set Editor</h2>
      {loading && <p>Loading requirement sets...</p>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && (
        <div>
          {requirementSets.length === 0 ? (
            <p>No requirement sets found. Create a requirement set to get started.</p>
          ) : (
            <ul className="req-set-list">
              {requirementSets.map((reqSet) => (
                <li key={reqSet.id}>
                  <strong>{reqSet.name}</strong> ({reqSet.test_type})
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}


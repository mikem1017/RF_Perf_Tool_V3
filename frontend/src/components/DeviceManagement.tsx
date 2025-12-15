import { useState, useEffect } from 'react'
import { api, handleApiError } from '../services/api'
import './DeviceManagement.css'

export default function DeviceManagement() {
  const [devices, setDevices] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    loadDevices()
  }, [])

  const loadDevices = async () => {
    try {
      setLoading(true)
      const data = await api.devices.list()
      setDevices(data)
      setError('')
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="device-management">
      <h2>Device Management</h2>
      {loading && <p>Loading devices...</p>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && (
        <div>
          {devices.length === 0 ? (
            <p>No devices found. Create a device to get started.</p>
          ) : (
            <ul className="device-list">
              {devices.map((device) => (
                <li key={device.id}>
                  <strong>{device.name}</strong> - {device.part_number || 'No part number'}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}


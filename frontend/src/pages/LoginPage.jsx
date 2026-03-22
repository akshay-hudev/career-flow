import { useState } from 'react'
import { useUser } from '../context/UserContext'
import { Zap, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const { login } = useUser()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim() || !email.trim()) return
    setLoading(true)
    try {
      await login(email.trim(), name.trim())
    } catch (e) {
      toast.error('Could not connect to backend. Is the server running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-brand-600 mb-4">
            <Zap size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">CareerAI</h1>
          <p className="text-gray-500 text-sm mt-1">AI-powered job search platform</p>
        </div>

        <div className="card">
          <h2 className="text-base font-semibold text-white mb-5">Get started</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Full Name</label>
              <input
                className="input"
                placeholder="Username"
                value={name}
                onChange={e => setName(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                className="input"
                placeholder="Email ID"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 mt-2"
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              {loading ? 'Connecting...' : 'Enter Platform →'}
            </button>
          </form>
          <p className="text-xs text-gray-600 text-center mt-4">
            Same email = same account. No password needed.
          </p>
        </div>
      </div>
    </div>
  )
}

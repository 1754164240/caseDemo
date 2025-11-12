import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import AdminRoute from './components/AdminRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Requirements from './pages/Requirements'
import TestCases from './pages/TestCases'
import Settings from './pages/Settings'
import KnowledgeBase from './pages/KnowledgeBase'
import Profile from './pages/Profile'

function App() {
  const { token } = useAuthStore()

  if (!token) {
    return <Login />
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/requirements" element={<Requirements />} />
        <Route path="/test-cases" element={<TestCases />} />
        <Route path="/knowledge-base" element={<KnowledgeBase />} />
        <Route path="/settings" element={
          <AdminRoute>
            <Settings />
          </AdminRoute>
        } />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

export default App


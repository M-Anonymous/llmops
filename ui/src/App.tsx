import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AdminPage from './pages/AdminPage'
import AgentConfigPage from './pages/AgentConfigPage'
import AgentDebugPage from './pages/AgentDebugPage'
import AgentPage from './pages/AgentPage'
import HomePage from './pages/HomePage'
import LibraryDocumentPage from './pages/LibraryDocumentPage'
import LibraryPage from './pages/LibraryPage'
import LoginPage from './pages/LoginPage'
import MiddlewarePage from './pages/MiddlewarePage'
import ModelPage from './pages/ModelPage'
import ToolPage from './pages/ToolPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/agent" element={<AgentPage />} />
        <Route path="/agent/config" element={<AgentConfigPage />} />
        <Route path="/agent/debug" element={<AgentDebugPage />} />
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/library/documents" element={<LibraryDocumentPage />} />
        <Route path="/model" element={<ModelPage />} />
        <Route path="/middleware" element={<MiddlewarePage />} />
        <Route path="/tool" element={<ToolPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

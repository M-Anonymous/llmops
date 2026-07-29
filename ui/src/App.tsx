import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AdminLayout from './layouts/AdminLayout'
import AgentConfigPage from './pages/AgentConfigPage'
import AgentDebugPage from './pages/AgentDebugPage'
import AgentPage from './pages/AgentPage'
import HomePage from './pages/HomePage'
import LibraryDocumentPage from './pages/LibraryDocumentPage'
import LibraryPage from './pages/LibraryPage'
import LoginPage from './pages/LoginPage'
import MiddlewarePage from './pages/MiddlewarePage'
import McpPage from './pages/McpPage'
import ModelPage from './pages/ModelPage'
import ToolPage from './pages/ToolPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<Navigate to="agent" replace />} />
          <Route path="agent" element={<AgentPage />} />
          <Route path="model" element={<ModelPage />} />
          <Route path="middleware" element={<MiddlewarePage />} />
          <Route path="mcp" element={<McpPage />} />
          <Route path="library" element={<LibraryPage />} />
          <Route path="tool" element={<ToolPage />} />
        </Route>
        <Route path="/agent/config" element={<AgentConfigPage />} />
        <Route path="/agent/debug" element={<AgentDebugPage />} />
        <Route path="/library/documents" element={<LibraryDocumentPage />} />
        <Route path="/agent" element={<Navigate to="/admin/agent" replace />} />
        <Route path="/model" element={<Navigate to="/admin/model" replace />} />
        <Route path="/middleware" element={<Navigate to="/admin/middleware" replace />} />
        <Route path="/mcp" element={<Navigate to="/admin/mcp" replace />} />
        <Route path="/library" element={<Navigate to="/admin/library" replace />} />
        <Route path="/tool" element={<Navigate to="/admin/tool" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

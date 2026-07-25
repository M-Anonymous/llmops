import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import HomePage from './pages/HomePage'
import LibraryDocumentPage from './pages/LibraryDocumentPage'
import LibraryPage from './pages/LibraryPage'
import LoginPage from './pages/LoginPage'
import ToolPage from './pages/ToolPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/library/documents" element={<LibraryDocumentPage />} />
        <Route path="/tool" element={<ToolPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { HomePage } from './pages/HomePage';
import { EnterprisesPage } from './pages/EnterprisesPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { CVBasePage } from './pages/CVBasePage';
import { CVParsingPage } from './pages/CVParsingPage';
import { MatchingPage } from './pages/MatchingPage';
import { ResultsPage } from './pages/ResultsPage';
import { MatchingResultDetailPage } from './pages/MatchingResultDetailPage';
import { EnterpriseDetailPage } from './pages/EnterpriseDetailPage';
import { ProjectDetailPage } from './pages/ProjectDetailPage';
import { OffrePage } from './pages/OffrePage';
import { InterviewSheetPage } from './pages/InterviewSheetPage';
import { InterviewSheetsListPage } from './pages/InterviewSheetsListPage';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />

          {/* Enterprises */}
          <Route path="/enterprises" element={<EnterprisesPage />} />
          <Route path="/enterprises/:enterpriseId" element={<EnterpriseDetailPage />} />

          {/* Projects */}
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/projects/:projectId/offre" element={<OffrePage />} />
          <Route path="/projects/:projectId/cvs" element={<CVBasePage />} />
          <Route path="/projects/:projectId/parsing" element={<CVParsingPage />} />
          <Route path="/projects/:projectId/matching" element={<MatchingPage />} />
          <Route path="/projects/:projectId/results" element={<ResultsPage />} />
          <Route path="/projects/:projectId/results/:timestamp" element={<MatchingResultDetailPage />} />

          {/* Interview sheets */}
          <Route path="/interviews" element={<InterviewSheetsListPage />} />
          <Route path="/interviews/:sheetId" element={<InterviewSheetPage />} />

          {/* Legacy routes (backwards compatibility) */}
          <Route path="/cvs" element={<CVBasePage />} />
          <Route path="/parsing" element={<CVParsingPage />} />
          <Route path="/matching" element={<MatchingPage />} />
          <Route path="/results" element={<ResultsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;

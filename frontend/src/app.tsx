import { BrowserRouter, Route, Routes } from './router'
import AppShell from './components/layout/app-shell'
import Dashboard from './pages/dashboard/dashboard'
import PromptsList from './pages/prompts/prompts-list'
import PromptDetail from './pages/prompts/prompt-detail'
import PromptPlayground from './pages/prompts/prompt-playground'
import PromptCompare from './pages/prompts/prompt-compare'
import ExperimentsList from './pages/experiments/experiments-list'
import ExperimentCreate from './pages/experiments/experiment-create'
import ExperimentDetail from './pages/experiments/experiment-detail'
import EvalDashboard from './pages/evaluations/eval-dashboard'
import EvalRunDetail from './pages/evaluations/eval-run-detail'
import EvalDatasets from './pages/evaluations/eval-datasets'
import CampaignsList from './pages/evaluations/human-eval/campaigns-list'
import CampaignCreate from './pages/evaluations/human-eval/campaign-create'
import CampaignDetail from './pages/evaluations/human-eval/campaign-detail'
import RatingInterface from './pages/evaluations/human-eval/rating-interface'
import CostDashboard from './pages/cost/cost-dashboard'
import TokenAnalytics from './pages/cost/token-analytics'
import RoutingRules from './pages/cost/routing-rules'
import BudgetAlerts from './pages/cost/budget-alerts'
import CostForecast from './pages/cost/cost-forecast'
import ObservabilityDashboard from './pages/observability/observability-dashboard'
import TracesList from './pages/observability/traces-list'
import TraceViewer from './pages/observability/trace-viewer'
import AlertConfig from './pages/observability/alert-config'
import PipelineStatus from './pages/deployments/pipeline-status'
import DeploymentHistory from './pages/deployments/deployment-history'
import CanaryControls from './pages/deployments/canary-controls'
import Login from './pages/auth/login'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/evaluations/human/:id/rate" element={<RatingInterface />} />
        <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/prompts" element={<PromptsList />} />
          <Route path="/prompts/:id" element={<PromptDetail />} />
          <Route path="/prompts/:id/playground" element={<PromptPlayground />} />
          <Route path="/prompts/:id/compare" element={<PromptCompare />} />
          <Route path="/experiments" element={<ExperimentsList />} />
          <Route path="/experiments/new" element={<ExperimentCreate />} />
          <Route path="/experiments/:id" element={<ExperimentDetail />} />
          <Route path="/evaluations" element={<EvalDashboard />} />
          <Route path="/evaluations/runs/:id" element={<EvalRunDetail />} />
          <Route path="/evaluations/datasets" element={<EvalDatasets />} />
          <Route path="/evaluations/human" element={<CampaignsList />} />
          <Route path="/evaluations/human/new" element={<CampaignCreate />} />
          <Route path="/evaluations/human/:id" element={<CampaignDetail />} />
          <Route path="/cost" element={<CostDashboard />} />
          <Route path="/cost/analytics" element={<TokenAnalytics />} />
          <Route path="/cost/routing" element={<RoutingRules />} />
          <Route path="/cost/alerts" element={<BudgetAlerts />} />
          <Route path="/cost/forecast" element={<CostForecast />} />
          <Route path="/observability" element={<ObservabilityDashboard />} />
          <Route path="/observability/traces" element={<TracesList />} />
          <Route path="/observability/traces/:id" element={<TraceViewer />} />
          <Route path="/observability/alerts" element={<AlertConfig />} />
          <Route path="/deployments" element={<PipelineStatus />} />
          <Route path="/deployments/:id" element={<DeploymentHistory />} />
          <Route path="/deployments/:id/canary" element={<CanaryControls />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

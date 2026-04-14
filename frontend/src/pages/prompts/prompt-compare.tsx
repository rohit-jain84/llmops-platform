import { useParams, useSearchParams } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import DiffViewer from '@/components/editor/diff-viewer'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { usePrompt, usePromptVersions, usePromptDiffDetailed } from '@/hooks/use-prompts'
import { useRegressionCheck } from '@/hooks/use-evaluations'
import { Badge } from '@/components/ui/badge'
import { GitCompare, Plus, Minus, Replace, Variable, AlertTriangle, TrendingUp, TrendingDown, Clock } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export default function PromptCompare() {
  const { id } = useParams<{ id: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const v1 = Number(searchParams.get('v1') || 1)
  const v2 = Number(searchParams.get('v2') || 2)
  const { data: template } = usePrompt(id!)
  const { data: versions, isLoading: versionsLoading } = usePromptVersions(id!)
  const { data: diff, isLoading: diffLoading } = usePromptDiffDetailed(id!, v1, v2)
  const { data: regression, isError: regressionError } = useRegressionCheck(id!, v1, v2)

  if (versionsLoading || diffLoading) return <LoadingSkeleton />

  const handleVersionChange = (key: 'v1' | 'v2', val: string) => {
    const params = new URLSearchParams(searchParams)
    params.set(key, val)
    setSearchParams(params)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Compare — ${template?.name ?? 'Prompt'}`}
        description="Side-by-side diff between two prompt versions"
      />

      {/* Version selectors */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">From:</label>
          <select className="rounded-md border px-3 py-2 text-sm" value={v1} onChange={(e) => handleVersionChange('v1', e.target.value)}>
            {versions?.map((v) => (
              <option key={v.version_number} value={v.version_number}>
                v{v.version_number} {v.tag ? `(${v.tag})` : ''}
              </option>
            ))}
          </select>
        </div>
        <GitCompare className="h-4 w-4 text-muted-foreground" />
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">To:</label>
          <select className="rounded-md border px-3 py-2 text-sm" value={v2} onChange={(e) => handleVersionChange('v2', e.target.value)}>
            {versions?.map((v) => (
              <option key={v.version_number} value={v.version_number}>
                v{v.version_number} {v.tag ? `(${v.tag})` : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Regression detection banner */}
      {regression && !regressionError && (
        <Card className={regression.has_regression ? 'border-red-300 bg-red-50' : 'border-green-300 bg-green-50'}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              {regression.has_regression ? (
                <>
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <span className="text-red-800">Regression Detected</span>
                </>
              ) : (
                <>
                  <TrendingUp className="h-4 w-4 text-green-600" />
                  <span className="text-green-800">No Regression</span>
                </>
              )}
            </CardTitle>
            <CardDescription className={regression.has_regression ? 'text-red-600' : 'text-green-600'}>
              Comparing eval scores between v{regression.previous_version} and v{regression.current_version} (threshold: {regression.threshold_pct}%)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Regressions */}
              {regression.regressions.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-red-800 mb-2 flex items-center gap-1">
                    <TrendingDown className="h-3 w-3" /> Regressions
                  </h4>
                  <div className="space-y-1">
                    {regression.regressions.map((r) => (
                      <div key={r.metric} className="flex items-center justify-between text-sm bg-white/60 rounded px-2 py-1">
                        <span className="font-medium capitalize">{r.metric}</span>
                        <span className="text-red-700">
                          {r.previous.toFixed(2)} → {r.current.toFixed(2)}
                          <span className="ml-1 text-xs">({r.pct_change.toFixed(1)}%)</span>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {/* Improvements */}
              {regression.improvements.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-green-800 mb-2 flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" /> Improvements
                  </h4>
                  <div className="space-y-1">
                    {regression.improvements.map((r) => (
                      <div key={r.metric} className="flex items-center justify-between text-sm bg-white/60 rounded px-2 py-1">
                        <span className="font-medium capitalize">{r.metric}</span>
                        <span className="text-green-700">
                          {r.previous.toFixed(2)} → {r.current.toFixed(2)}
                          <span className="ml-1 text-xs">(+{r.pct_change.toFixed(1)}%)</span>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {/* Score summary if no regressions or improvements */}
              {regression.regressions.length === 0 && regression.improvements.length === 0 && (
                <div className="col-span-2 text-sm text-muted-foreground">
                  All metrics within the {regression.threshold_pct}% threshold — no significant changes detected.
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Diff stats and metadata */}
      {diff && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Change stats */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Change Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <Plus className="h-3.5 w-3.5 text-green-600" />
                  <span className="text-green-700 font-medium">{diff.lines_added} lines added</span>
                </div>
                <div className="flex items-center gap-2">
                  <Minus className="h-3.5 w-3.5 text-red-600" />
                  <span className="text-red-700 font-medium">{diff.lines_removed} lines removed</span>
                </div>
                <div className="flex items-center gap-2">
                  <Replace className="h-3.5 w-3.5 text-yellow-600" />
                  <span className="text-yellow-700 font-medium">{diff.lines_changed} lines changed</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Variable changes */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-1">
                <Variable className="h-3.5 w-3.5" /> Variables
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 text-sm">
                {diff.variables_added.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {diff.variables_added.map((v) => (
                      <Badge key={v} variant="success" className="text-xs">+ {v}</Badge>
                    ))}
                  </div>
                )}
                {diff.variables_removed.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {diff.variables_removed.map((v) => (
                      <Badge key={v} variant="destructive" className="text-xs">- {v}</Badge>
                    ))}
                  </div>
                )}
                {diff.variables_added.length === 0 && diff.variables_removed.length === 0 && (
                  <span className="text-muted-foreground">No variable changes</span>
                )}
                <div className="mt-2 text-xs text-muted-foreground">
                  v{v1}: {diff.v1_variables.length} vars | v{v2}: {diff.v2_variables.length} vars
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Version metadata */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" /> Version Info
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div>
                  <div className="flex items-center gap-1.5">
                    <Badge variant="info" className="text-xs">v{v1}</Badge>
                    {diff.v1_tag && <Badge variant="secondary" className="text-xs">{diff.v1_tag}</Badge>}
                  </div>
                  {diff.v1_commit_message && (
                    <p className="text-xs text-muted-foreground mt-0.5 truncate" title={diff.v1_commit_message}>
                      {diff.v1_commit_message}
                    </p>
                  )}
                  {diff.v1_created_at && (
                    <p className="text-xs text-muted-foreground">{formatDate(diff.v1_created_at)}</p>
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <Badge variant="info" className="text-xs">v{v2}</Badge>
                    {diff.v2_tag && <Badge variant="secondary" className="text-xs">{diff.v2_tag}</Badge>}
                  </div>
                  {diff.v2_commit_message && (
                    <p className="text-xs text-muted-foreground mt-0.5 truncate" title={diff.v2_commit_message}>
                      {diff.v2_commit_message}
                    </p>
                  )}
                  {diff.v2_created_at && (
                    <p className="text-xs text-muted-foreground">{formatDate(diff.v2_created_at)}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Diff viewer */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Badge variant="info">v{v1}</Badge> vs <Badge variant="info">v{v2}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <DiffViewer original={diff?.v1_content ?? ''} modified={diff?.v2_content ?? ''} />
        </CardContent>
      </Card>
    </div>
  )
}

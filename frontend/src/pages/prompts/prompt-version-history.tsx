import { useParams, useNavigate } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/ui/data-table'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { usePrompt, usePromptVersions, useTagVersion } from '@/hooks/use-prompts'
import { formatDate } from '@/lib/utils'
import { Tag, GitCompare, Eye } from 'lucide-react'

interface VersionRow {
  id: string
  version_number: number
  tag?: string
  commit_message?: string
  created_at: string
  created_by?: string
  [key: string]: unknown
}

export default function PromptVersionHistory() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: template } = usePrompt(id!)
  const { data: versions, isLoading } = usePromptVersions(id!)
  const tagVersion = useTagVersion()

  if (isLoading) return <LoadingSkeleton lines={8} />

  const handleTag = async (versionNum: number, tag: string) => {
    if (!id) return
    await tagVersion.mutateAsync({ templateId: id, num: versionNum, tag })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Version History — ${template?.name ?? 'Prompt'}`}
        description="Full timeline of all prompt versions"
      />

      <DataTable<VersionRow>
        columns={[
          { key: 'version_number', header: 'Version', render: (v) => <span className="font-mono font-medium">v{v.version_number}</span> },
          { key: 'tag', header: 'Tag', render: (v) => v.tag ? <Badge variant={v.tag === 'production' ? 'success' : v.tag === 'staging' ? 'warning' : 'info'}>{v.tag}</Badge> : <span className="text-muted-foreground">—</span> },
          { key: 'commit_message', header: 'Message', render: (v) => <span className="text-muted-foreground">{v.commit_message || '—'}</span> },
          { key: 'created_by', header: 'Author', render: (v) => v.created_by ?? '—' },
          { key: 'created_at', header: 'Created', render: (v) => formatDate(v.created_at) },
          {
            key: 'actions', header: 'Actions', render: (v) => (
              <div className="flex gap-1">
                <Button size="sm" variant="ghost" title="View" onClick={() => navigate(`/prompts/${id}?version=${v.version_number}`)}>
                  <Eye className="h-3 w-3" />
                </Button>
                <Button size="sm" variant="ghost" title="Compare" onClick={() => navigate(`/prompts/${id}/compare?v1=${v.version_number - 1}&v2=${v.version_number}`)}>
                  <GitCompare className="h-3 w-3" />
                </Button>
                <Button size="sm" variant="ghost" title="Tag production" onClick={() => handleTag(v.version_number, 'production')}>
                  <Tag className="h-3 w-3" />
                </Button>
              </div>
            ),
          },
        ]}
        data={(versions ?? []) as VersionRow[]}
      />
    </div>
  )
}

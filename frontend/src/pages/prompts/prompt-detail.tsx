import { useState } from 'react'
import { useParams } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import PromptEditor from '@/components/editor/prompt-editor'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { usePrompt, usePromptVersions, useCreatePromptVersion, useTagVersion } from '@/hooks/use-prompts'
import { formatDate } from '@/lib/utils'
import { Save, Tag, Play } from 'lucide-react'

export default function PromptDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: template, isLoading } = usePrompt(id!)
  const { data: versions } = usePromptVersions(id!)
  const createVersion = useCreatePromptVersion()
  const tagVersion = useTagVersion()
  const [content, setContent] = useState('')
  const [commitMessage, setCommitMessage] = useState('')

  const latestVersion = versions?.[0]

  // Initialize content from latest version
  if (latestVersion && !content) {
    setContent(latestVersion.content)
  }

  if (isLoading) return <LoadingSkeleton />

  const handleSave = async () => {
    if (!id) return
    await createVersion.mutateAsync({
      templateId: id,
      content,
      commit_message: commitMessage || undefined,
    })
    setCommitMessage('')
  }

  const handleTag = async (versionNum: number, tag: string) => {
    if (!id) return
    await tagVersion.mutateAsync({ templateId: id, num: versionNum, tag })
  }

  return (
    <div>
      <PageHeader
        title={template?.name ?? 'Prompt'}
        description={template?.description ?? undefined}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => window.location.href = `/prompts/${id}/playground`}>
              <Play className="mr-2 h-4 w-4" />Playground
            </Button>
            <Button onClick={handleSave} disabled={createVersion.isPending}>
              <Save className="mr-2 h-4 w-4" />{createVersion.isPending ? 'Saving...' : 'Save Version'}
            </Button>
          </div>
        }
      />

      <Tabs defaultValue="editor">
        <TabsList>
          <TabsTrigger value="editor">Editor</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
          <TabsTrigger value="compare">Compare</TabsTrigger>
        </TabsList>

        <TabsContent value="editor" className="space-y-4">
          <PromptEditor value={content} onChange={setContent} />
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Commit message (optional)"
              value={commitMessage}
              onChange={(e) => setCommitMessage(e.target.value)}
              className="flex-1 rounded-md border px-3 py-2 text-sm"
            />
          </div>
          {latestVersion?.variables && Object.keys(latestVersion.variables).length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-sm">Variables</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {Object.keys(latestVersion.variables).map((v) => (
                    <Badge key={v} variant="secondary">{'{{' + v + '}}'}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardContent className="p-0">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 text-left text-sm font-medium">Version</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Tag</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Message</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Created</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {versions?.map((v) => (
                    <tr key={v.id} className="border-b">
                      <td className="px-4 py-3 text-sm font-mono">v{v.version_number}</td>
                      <td className="px-4 py-3">
                        {v.tag && (
                          <Badge variant={v.tag === 'production' ? 'success' : 'info'}>
                            {v.tag}
                          </Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">{v.commit_message || '—'}</td>
                      <td className="px-4 py-3 text-sm">{formatDate(v.created_at)}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          <Button size="sm" variant="ghost" onClick={() => handleTag(v.version_number, 'production')}>
                            <Tag className="h-3 w-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="compare">
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              Select two versions to compare. Use the Compare page at /prompts/{id}/compare?v1=1&v2=2
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

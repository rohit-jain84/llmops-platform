import { DiffEditor } from '@monaco-editor/react'

interface DiffViewerProps {
  original: string
  modified: string
  height?: string
}

export default function DiffViewer({ original, modified, height = '400px' }: DiffViewerProps) {
  return (
    <div className="rounded-md border overflow-hidden">
      <DiffEditor
        height={height}
        original={original}
        modified={modified}
        language="handlebars"
        options={{
          readOnly: true,
          minimap: { enabled: false },
          fontSize: 14,
          scrollBeyondLastLine: false,
          automaticLayout: true,
          renderSideBySide: true,
        }}
        theme="vs-light"
      />
    </div>
  )
}

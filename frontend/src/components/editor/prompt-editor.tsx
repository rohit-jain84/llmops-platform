import Editor from '@monaco-editor/react'

interface PromptEditorProps {
  value: string
  onChange: (value: string) => void
  readOnly?: boolean
  height?: string
}

export default function PromptEditor({ value, onChange, readOnly = false, height = '400px' }: PromptEditorProps) {
  return (
    <div className="rounded-md border overflow-hidden">
      <Editor
        height={height}
        defaultLanguage="handlebars"
        value={value}
        onChange={(val) => onChange(val || '')}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          wordWrap: 'on',
          readOnly,
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 2,
        }}
        theme="vs-light"
      />
    </div>
  )
}

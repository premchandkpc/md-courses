import { useEffect, useState, useRef } from 'react'
import { fetchFile } from '../../lib/api'

interface Props {
  filePath: string | null
}

function basicMarkdownToHtml(md: string): string {
  let h = md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3 class="text-sm font-bold text-infra-100 mt-4 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-base font-bold text-accent-cyan mt-5 mb-1">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-lg font-bold text-infra-50 mt-5 mb-2">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-infra-100">$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="text-accent-green bg-infra-800 px-1 rounded text-[11px]">$1</code>')
    .replace(/^- (.+)$/gm, '<li class="text-infra-300 ml-4 list-disc text-[13px] leading-relaxed">$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li class="text-infra-300 ml-4 list-decimal text-[13px] leading-relaxed">$1. $2</li>')
    .replace(/\n{2,}/g, '</p><p class="text-infra-300 text-[13px] leading-relaxed mb-2">')
    .replace(/\|(.+)\|/g, (m) => {
      const cells = m.split('|').filter(Boolean).map(c => c.trim())
      if (cells.every(c => /^[-:]+$/.test(c))) return ''
      return '<tr>' + cells.map(c => `<td class="border border-infra-700 px-3 py-1 text-[12px] text-infra-300">${c}</td>`).join('') + '</tr>'
    })
  h = '<p class="text-infra-300 text-[13px] leading-relaxed mb-2">' + h + '</p>'
  h = h.replace(/<li>/g, '<ul class="mb-2">$&')
  h = h.replace(/<\/ul>\s*<ul>/g, '')
  h = h.replace(/<ul class="mb-2"><\/ul>/g, '')
  return h
}

export function FileContentViewer({ filePath }: Props) {
  const [state, setState] = useState<'loading' | 'loaded' | 'error'>('loading')
  const [content, setContent] = useState('')
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const prevPath = useRef<string | null>(null)
  const isHtml = filePath ? filePath.endsWith('.html') : false

  useEffect(() => {
    if (!filePath) return
    if (filePath === prevPath.current) return
    prevPath.current = filePath
    let cancelled = false
    fetchFile(filePath).then((res) => {
      if (!cancelled && res.content) { setContent(res.content); setState('loaded') }
    }).catch(() => {
      if (!cancelled) setState('error')
    })
    return () => { cancelled = true }
  }, [filePath])

  if (!filePath) {
    return (
      <div className="flex items-center justify-center h-full text-infra-500 text-sm font-mono">
        Select a file from the sidebar
      </div>
    )
  }

  if (state === 'loading') {
    return (
      <div className="flex items-center justify-center h-32 text-infra-500 text-sm font-mono">
        Loading...
      </div>
    )
  }

  if (state === 'error') {
    return (
      <div className="flex items-center justify-center h-32 text-red-400 text-sm font-mono">
        Failed to load {filePath}
      </div>
    )
  }

  if (isHtml) {
    return (
      <iframe
        ref={iframeRef}
        srcDoc={content}
        className="w-full border-0 rounded-lg"
        style={{ height: 'calc(100vh - 200px)', minHeight: 500, background: '#1a1a2e' }}
        title={filePath}
        sandbox="allow-scripts"
      />
    )
  }

  const html = basicMarkdownToHtml(content)

  return (
    <div
      className="prose prose-invert max-w-none overflow-y-auto"
      style={{ height: 'calc(100vh - 200px)', minHeight: 400 }}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

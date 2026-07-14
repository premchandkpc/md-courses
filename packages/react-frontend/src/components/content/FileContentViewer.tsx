import { useEffect, useState, useRef, useMemo } from 'react'
import { fetchFile } from '../../lib/api'

interface Frontmatter {
  title?: string
  difficulty?: string
  time?: string
  prerequisites?: string[]
  related?: string[]
  paths?: string[]
  topic?: string
}

interface Props {
  filePath: string | null
  onSelect?: (path: string) => void
}

function parseFrontmatter(raw: string): { frontmatter: Frontmatter; body: string } {
  const m = raw.match(/^---\n([\s\S]+?)\n---\n?/)
  if (!m) return { frontmatter: {}, body: raw }

  const fm: Frontmatter = {}
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^(\w+):\s*(.+)$/)
    if (kv) {
      if (kv[1] === 'prerequisites' || kv[1] === 'related' || kv[1] === 'paths') continue
      ;(fm as Record<string, string>)[kv[1]] = kv[2].trim()
    }
  }

  const listRe = /^(\w+):\n((?:\s+- .+\n?)+)/gm
  let listMatch
  while ((listMatch = listRe.exec(m[1])) !== null) {
    const key = listMatch[1] as keyof Frontmatter
    const items = listMatch[2].split('\n').map(l => l.replace(/^\s*- /, '').trim()).filter(Boolean)
    ;(fm as Record<string, unknown>)[key] = items
  }

  const body = raw.slice(m[0].length)
  return { frontmatter: fm, body }
}

const difficultyColors: Record<string, string> = {
  beginner: '#3fb950',
  intermediate: '#fbbf24',
  advanced: '#f85149',
  staff: '#a78bfa',
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function renderMarkdown(md: string): string {
  const lines = md.split('\n')
  let html = ''
  let inCodeBlock = false
  let codeBuffer: string[] = []
  let codeLang = ''

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    if (line.startsWith('```')) {
      if (inCodeBlock) {
        const lang = codeLang ? ` class="language-${escapeHtml(codeLang)}"` : ''
        html += `<pre class="bg-infra-800 rounded-lg p-4 my-2 overflow-x-auto text-[12px] leading-relaxed font-mono text-infra-200 border border-infra-700"><code${lang}>${escapeHtml(codeBuffer.join('\n'))}</code></pre>\n`
        codeBuffer = []
        codeLang = ''
        inCodeBlock = false
      } else {
        inCodeBlock = true
        codeLang = line.slice(3).trim()
      }
      continue
    }

    if (inCodeBlock) {
      codeBuffer.push(line)
      continue
    }

    if (line.startsWith('#')) {
      const level = line.match(/^#+/)![0].length
      const text = line.replace(/^#+\s*/, '').replace(/\p{Emoji_Presentation}/gu, '').trim()
      const sizeClass = level === 1 ? 'text-lg font-bold text-infra-50 mt-5 mb-2'
        : level === 2 ? 'text-base font-bold text-accent-cyan mt-5 mb-1'
        : 'text-sm font-bold text-infra-100 mt-4 mb-1'
      html += `<h${Math.min(level, 3)} class="${sizeClass}">${escapeHtml(text)}</h${Math.min(level, 3)}>\n`
      continue
    }

    if (line.startsWith('```')) continue

    if (line.startsWith('> ')) {
      html += `<blockquote class="border-l-2 border-accent-cyan pl-4 my-2 text-infra-300 text-[13px] italic">${renderInline(line.slice(2))}</blockquote>\n`
      continue
    }

    if (line.startsWith('---')) {
      html += `<hr class="border-infra-700 my-4" />\n`
      continue
    }

    if (line.startsWith('- ')) {
      html += `<li class="text-infra-300 ml-4 list-disc text-[13px] leading-relaxed">${renderInline(line.slice(2))}</li>\n`
      continue
    }

    if (/^\d+\.\s/.test(line)) {
      html += `<li class="text-infra-300 ml-4 list-decimal text-[13px] leading-relaxed">${renderInline(line.replace(/^\d+\.\s*/, ''))}</li>\n`
      continue
    }

    if (line.startsWith('|')) {
      const cells = line.split('|').filter(Boolean).map(c => c.trim())
      if (cells.every(c => /^[-:]+$/.test(c))) continue
      html += `<tr>${cells.map(c => `<td class="border border-infra-700 px-3 py-1 text-[12px] text-infra-300">${renderInline(c)}</td>`).join('')}</tr>\n`
      continue
    }

    if (line.trim() === '') {
      continue
    }

    html += `<p class="text-infra-300 text-[13px] leading-relaxed mb-2">${renderInline(line)}</p>\n`
  }

  if (inCodeBlock) {
    html += `<pre class="bg-infra-800 rounded-lg p-4 my-2 overflow-x-auto text-[12px] leading-relaxed font-mono text-infra-200 border border-infra-700"><code>${escapeHtml(codeBuffer.join('\n'))}</code></pre>\n`
  }

  return html
}

function renderInline(text: string): string {
  let h = escapeHtml(text)
  h = h.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-accent-cyan underline hover:brightness-110" target="_blank" rel="noopener">$1</a>')
  h = h.replace(/\*\*(.+?)\*\*/g, '<strong class="text-infra-100">$1</strong>')
  h = h.replace(/`([^`]+)`/g, '<code class="text-accent-green bg-infra-800 px-1 rounded text-[11px] font-mono">$1</code>')
  return h
}

function DifficultyBadge({ difficulty }: { difficulty?: string }) {
  if (!difficulty) return null
  const color = difficultyColors[difficulty] || '#5a6e91'
  return (
    <span
      className="text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase tracking-wider"
      style={{ background: color + '20', color, border: `1px solid ${color}40` }}
    >
      {difficulty}
    </span>
  )
}

function WhatToReadNext({ frontmatter, onSelect }: { frontmatter: Frontmatter; currentPath: string; onSelect?: (path: string) => void }) {
  const hasLinks = (frontmatter.prerequisites && frontmatter.prerequisites.length > 0) ||
    (frontmatter.related && frontmatter.related.length > 0)

  if (!hasLinks) return null

  const handleClick = (e: React.MouseEvent, targetPath: string) => {
    e.preventDefault()
    if (onSelect) {
      onSelect(targetPath)
    }
  }

  return (
    <div className="mt-8 border-t border-infra-700 pt-5">
      <div className="text-[10px] font-mono text-accent-cyan uppercase tracking-wider mb-3">
        What to Read Next
      </div>
      <div className="flex flex-wrap gap-4">
        {frontmatter.prerequisites && frontmatter.prerequisites.length > 0 && (
          <div className="flex-1 min-w-[160px]">
            <div className="text-[10px] font-mono text-infra-400 mb-2 uppercase">Prerequisites</div>
            {frontmatter.prerequisites.map(p => (
              <a
                key={p}
                href="#"
                onClick={(e) => handleClick(e, p.endsWith('.md') ? p : p + '.md')}
                className="block text-[12px] text-infra-300 hover:text-accent-cyan transition-colors mb-1 truncate"
              >
                ← {p.split('/').pop()}
              </a>
            ))}
          </div>
        )}
        {frontmatter.related && frontmatter.related.length > 0 && (
          <div className="flex-1 min-w-[160px]">
            <div className="text-[10px] font-mono text-infra-400 mb-2 uppercase">Related</div>
            {frontmatter.related.map(r => (
              <a
                key={r}
                href="#"
                onClick={(e) => handleClick(e, r.endsWith('.md') ? r : r + '.md')}
                className="block text-[12px] text-infra-300 hover:text-accent-cyan transition-colors mb-1 truncate"
              >
                {r.split('/').pop()} →
              </a>
            ))}
          </div>
        )}
        {frontmatter.paths && frontmatter.paths.length > 0 && (
          <div className="flex-1 min-w-[160px]">
            <div className="text-[10px] font-mono text-infra-400 mb-2 uppercase">Part of</div>
            {frontmatter.paths.map(p => (
              <a
                key={p}
                href="#"
                onClick={(e) => handleClick(e, 'paths/' + p + '.md')}
                className="block text-[12px] text-infra-300 hover:text-accent-cyan transition-colors mb-1 truncate"
              >
                {p.replace(/-/g, ' ')} →
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export function FileContentViewer({ filePath, onSelect }: Props) {
  const [state, setState] = useState<'loading' | 'loaded' | 'error'>('loading')
  const [content, setContent] = useState('')
  const [frontmatter, setFrontmatter] = useState<Frontmatter>({})
  const prevPath = useRef<string | null>(null)
  const isHtml = filePath ? filePath.endsWith('.html') : false

  useEffect(() => {
    if (!filePath) return
    if (filePath === prevPath.current) return
    prevPath.current = filePath
    let cancelled = false
    fetchFile(filePath).then((res) => {
      if (!cancelled && res.content) {
        const { frontmatter: fm, body } = parseFrontmatter(res.content)
        setFrontmatter(fm)
        setContent(body)
        setState('loaded')
      }
    }).catch(() => {
      if (!cancelled) setState('error')
    })
    return () => { cancelled = true }
  }, [filePath])

  const html = useMemo(() => {
    if (!content || isHtml) return ''
    return renderMarkdown(content)
  }, [content, isHtml])

  if (!filePath) {
    return (
      <div className="flex items-center justify-center h-full text-infra-500 text-sm font-mono">
        Select a file from the sidebar to begin reading
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
        srcDoc={content}
        className="w-full border-0 rounded-lg"
        style={{ height: 'calc(100vh - 200px)', minHeight: 500, background: '#1a1a2e' }}
        title={filePath}
        sandbox="allow-scripts"
      />
    )
  }

  const timeEst = frontmatter.time || '30m'

  return (
    <div>
      {/* Metadata bar */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        {frontmatter.difficulty && <DifficultyBadge difficulty={frontmatter.difficulty} />}
        {frontmatter.topic && (
          <span className="text-[10px] font-mono text-infra-400 bg-infra-800 px-2 py-0.5 rounded">
            {frontmatter.topic}
          </span>
        )}
        <span className="text-[10px] font-mono text-infra-500">
          ~{timeEst} read
        </span>
      </div>

      {/* Rendered content */}
      <div
        className="max-w-none overflow-y-auto"
        style={{ height: 'calc(100vh - 300px)', minHeight: 400 }}
        dangerouslySetInnerHTML={{ __html: html }}
      />

      {/* Next steps */}
      <WhatToReadNext frontmatter={frontmatter} currentPath={filePath} onSelect={onSelect} />
    </div>
  )
}

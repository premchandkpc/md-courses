import { useEffect, useState } from 'react'
import { fetchTree } from '../../lib/api'
import type { FileNode } from '../../types'

interface Props {
  filePath: string | null
}

function findHtmlFiles(tree: FileNode[], selectedPath: string): { name: string; path: string }[] {
  const parts = selectedPath.split('/')
  if (parts.length <= 1) return []
  const dirPath = parts.slice(0, -1).join('/')

  function findNode(nodes: FileNode[], target: string): FileNode | null {
    for (const n of nodes) {
      if (n.path === target && n.type === 'dir') return n
      if (n.children) {
        const found = findNode(n.children, target)
        if (found) return found
      }
    }
    return null
  }

  let dirNode: FileNode | null = null
  for (const root of tree) {
    dirNode = findNode([root], dirPath)
    if (dirNode) break
    if (root.children) {
      dirNode = findNode(root.children, dirPath)
      if (dirNode) break
    }
  }

  if (!dirNode || !dirNode.children) return []

  return dirNode.children
    .filter((c) => c.type === 'file' && c.name.endsWith('.html') && c.path !== selectedPath)
    .map((c) => ({ name: c.name.replace('.html', ''), path: c.path }))
}

function formatName(name: string): string {
  return name
    .replace(/-/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function VisualizationGallery({ filePath }: Props) {
  const [visuals, setVisuals] = useState<{ name: string; path: string }[]>([])

  useEffect(() => {
    if (!filePath) return
    let cancelled = false
    fetchTree().then((tree) => {
      if (!cancelled) setVisuals(findHtmlFiles(tree, filePath))
    })
    return () => { cancelled = true }
  }, [filePath])

  if (visuals.length === 0) return null

  return (
    <div className="mt-6 border-t border-infra-700 pt-4">
      <div className="text-[10px] font-mono text-accent-cyan uppercase tracking-wider mb-3">
        Visualizations in this domain
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {visuals.map((v) => (
          <a
            key={v.path}
            href={`/view?path=${encodeURIComponent(v.path)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="block rounded-lg border border-infra-700 bg-infra-800/50 p-3 hover:border-accent-cyan/50 hover:bg-infra-800 transition-all group"
          >
            <div className="text-2xl mb-1">🎨</div>
            <div className="text-[12px] font-medium text-infra-200 group-hover:text-accent-cyan transition-colors truncate">
              {formatName(v.name)}
            </div>
            <div className="text-[9px] font-mono text-infra-500 mt-1 truncate">
              {v.path}
            </div>
            <div className="text-[10px] text-accent-cyan mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              Open ↗
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}

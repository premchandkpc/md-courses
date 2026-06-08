import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { fetchTree } from '../../lib/api'
import type { FileNode } from '../../types'

interface Props {
  onSelect: (path: string) => void
}

function TreeNode({ node, depth = 0, onSelect }: { node: FileNode; depth?: number; onSelect: (path: string) => void }) {
  const [open, setOpen] = useState(node.open ?? false)
  const isDir = node.type === 'dir'

  return (
    <div>
      <button
        onClick={() => isDir ? setOpen(!open) : onSelect(node.path)}
        className="w-full text-left px-2 py-1 rounded text-[11px] font-mono transition-colors hover:bg-infra-700"
        style={{ paddingLeft: 12 + depth * 14, color: isDir ? '#e3eaf0' : '#8a9bb8' }}
      >
        {isDir ? (open ? '▾ ' : '▸ ') : '  '}
        {node.name}
      </button>
      <AnimatePresence>
        {isDir && open && node.children && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            {node.children.map((child) => (
              <TreeNode key={child.path} node={child} depth={depth + 1} onSelect={onSelect} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export function FileTree({ onSelect }: Props) {
  const [tree, setTree] = useState<FileNode[]>([])

  useEffect(() => {
    fetchTree().then(setTree).catch(() => {})
  }, [])

  return (
    <div className="rounded-xl border border-infra-700 overflow-hidden">
      <div className="px-3 py-2 text-xs font-mono text-infra-400 border-b border-infra-700 bg-infra-900">
        Knowledge Tree
      </div>
      <div className="p-2 max-h-[500px] overflow-y-auto" style={{ background: '#0b0e14' }}>
        {tree.map((node) => (
          <TreeNode key={node.path} node={node} onSelect={onSelect} />
        ))}
      </div>
    </div>
  )
}

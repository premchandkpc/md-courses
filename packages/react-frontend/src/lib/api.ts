import type { FileNode } from '../types'

const BASE = '/api'

export async function fetchTree(): Promise<FileNode[]> {
  const res = await fetch(`${BASE}/tree`)
  const data = await res.json()
  return data.tree
}

export async function fetchFile(path: string): Promise<{ content: string; size: number; lastModified: number }> {
  const res = await fetch(`${BASE}/file?path=${encodeURIComponent(path)}`)
  if (!res.ok) throw new Error(`Failed to fetch ${path}`)
  return res.json()
}

export async function searchFiles(q: string): Promise<{ results: Array<{ path: string; name: string; matches: Array<{ line: number; text: string }> }> }> {
  const res = await fetch(`${BASE}/search?q=${encodeURIComponent(q)}`)
  return res.json()
}

export async function fetchStats(): Promise<Record<string, number | string>> {
  const res = await fetch(`${BASE}/stats`)
  return res.json()
}

export async function fetchGraph(): Promise<{ nodes: Array<{ id: string; name: string; path: string; type: string }>; edges: Array<{ source: string; target: string; label: string }>; nodeCount: number; edgeCount: number }> {
  const res = await fetch(`${BASE}/graph`)
  return res.json()
}

export async function fetchHealth(): Promise<{ status: string; uptime: number; cacheAge: string }> {
  const res = await fetch(`${BASE}/health`)
  return res.json()
}

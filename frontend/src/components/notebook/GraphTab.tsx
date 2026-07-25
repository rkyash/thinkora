import React, { useState } from 'react'
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  BookOpen,
  Info,
  Network,
  RefreshCw,
  Loader2,
  AlertCircle,
  Plus,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'
import { useParams } from 'react-router-dom'
import { useGraph, useRefreshGraph } from '@/hooks/useGenerate'
import type { GraphNode, GraphEdge, NodeType } from '@/types/api'

// ─── Node type styling ─────────────────────────────────────────────────────

const nodeTypeColors: Record<NodeType, { node: string; badge: string }> = {
  concept: {
    node: 'graph-node-concept text-indigo-300 border-indigo-500',
    badge: 'text-indigo-300 border-indigo-500/20 bg-indigo-500/5',
  },
  entity: {
    node: 'graph-node-entity text-pink-300 border-pink-500',
    badge: 'text-pink-300 border-pink-500/20 bg-pink-500/5',
  },
  topic: {
    node: 'graph-node-topic text-teal-300 border-teal-500',
    badge: 'text-teal-300 border-teal-500/20 bg-teal-500/5',
  },
  person: {
    node: 'graph-node-person text-amber-300 border-amber-500',
    badge: 'text-amber-300 border-amber-500/20 bg-amber-500/5',
  },
  place: {
    node: 'graph-node-entity text-cyan-300 border-cyan-500',
    badge: 'text-cyan-300 border-cyan-500/20 bg-cyan-500/5',
  },
  event: {
    node: 'graph-node-event text-red-300 border-red-500',
    badge: 'text-red-300 border-red-500/20 bg-red-500/5',
  },
}

const legendItems: { type: NodeType; label: string }[] = [
  { type: 'topic', label: 'Topic' },
  { type: 'concept', label: 'Concept' },
  { type: 'entity', label: 'Entity' },
  { type: 'person', label: 'Person' },
  { type: 'place', label: 'Place' },
  { type: 'event', label: 'Event' },
]

// ─── Coordinate helpers ────────────────────────────────────────────────────

/**
 * Convert backend x_pos/y_pos (pixel radial coords) to percentage
 * positions for the SVG canvas. We clamp to 5–95%.
 */
function toPercent(pos: number | null, range: number, size: number): number {
  if (pos === null) return 50
  // Map from [-range, range] → [5, 95]
  return Math.max(5, Math.min(95, ((pos + range) / (2 * range)) * (size - 10) + 5))
}

export function GraphTab() {
  const { id: notebookId = '' } = useParams<{ id: string }>()

  const { data: graph, isLoading, isError } = useGraph(notebookId)
  const refreshGraph = useRefreshGraph(notebookId)

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [zoomLevel, setZoomLevel] = useState(100)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const nodes: GraphNode[] = graph?.nodes ?? []
  const edges: GraphEdge[] = graph?.edges ?? []

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) ?? null

  // Compute coordinate range for normalization
  const xValues = nodes.map((n) => n.x_pos ?? 0)
  const yValues = nodes.map((n) => n.y_pos ?? 0)
  const xRange = Math.max(400, ...xValues.map(Math.abs))
  const yRange = Math.max(400, ...yValues.map(Math.abs))

  const getXPct = (n: GraphNode) => toPercent(n.x_pos, xRange, 100)
  const getYPct = (n: GraphNode) => toPercent(n.y_pos, yRange, 100)

  const getEdgeCoords = (edge: GraphEdge) => {
    const src = nodes.find((n) => n.id === edge.source_node)
    const tgt = nodes.find((n) => n.id === edge.target_node)
    return {
      x1: src ? getXPct(src) : 50,
      y1: src ? getYPct(src) : 50,
      x2: tgt ? getXPct(tgt) : 50,
      y2: tgt ? getYPct(tgt) : 50,
    }
  }

  // ─── Empty / error states ──────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center gap-2 text-muted-foreground text-sm">
        <Loader2 className="w-4 h-4 animate-spin text-primary" />
        Loading knowledge graph...
      </div>
    )
  }
  if (isError) {
    return (
      <div className="flex-1 flex items-center justify-center gap-2 text-destructive text-sm">
        <AlertCircle className="w-4 h-4" />
        Failed to load graph.
      </div>
    )
  }

  const isEmpty = nodes.length === 0

  return (
    <div className="flex-1 flex h-full relative overflow-hidden animate-fade-in">
      {/* Canvas Area */}
      <div
        className={cn(
          'flex-1 relative bg-background flex items-center justify-center transition-all duration-300',
          isFullscreen ? 'absolute inset-0 bg-background z-50' : 'h-full',
        )}
      >
        {/* Background grid */}
        <div className="absolute inset-0 bg-dots pointer-events-none opacity-40" />

        {/* Empty state */}
        {isEmpty && !refreshGraph.isPending && (
          <div className="flex flex-col items-center gap-4 text-center p-8 max-w-sm">
            <Network className="w-12 h-12 text-muted-foreground/40" />
            <div>
              <p className="text-sm font-semibold text-foreground">No graph yet</p>
              <p className="text-xs text-muted-foreground mt-1">
                Generate the knowledge graph from your notebook's source material.
              </p>
            </div>
            <Button
              onClick={() => refreshGraph.mutate()}
              className="btn-glow bg-primary hover:bg-violet-primary text-primary-foreground font-semibold text-xs px-4 h-9 flex items-center gap-2 active:scale-[0.98] transition-all duration-150"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Generate Graph
            </Button>
          </div>
        )}

        {refreshGraph.isPending && (
          <div className="flex flex-col items-center gap-3 text-muted-foreground text-sm">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
            <p>Extracting concepts and relationships...</p>
          </div>
        )}

        {!isEmpty && !refreshGraph.isPending && (
          <>
            {/* SVG Edges */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
              <defs>
                <marker
                  id="arrow"
                  markerWidth="6"
                  markerHeight="6"
                  refX="3"
                  refY="3"
                  orient="auto"
                >
                  <path d="M0,0 L0,6 L6,3 z" className="fill-primary/30" />
                </marker>
              </defs>
              {edges.map((edge) => {
                const { x1, y1, x2, y2 } = getEdgeCoords(edge)
                const mx = (x1 + x2) / 2
                const my = (y1 + y2) / 2
                return (
                  <g key={edge.id}>
                    <line
                      x1={`${x1}%`}
                      y1={`${y1}%`}
                      x2={`${x2}%`}
                      y2={`${y2}%`}
                      className="stroke-primary/15"
                      strokeWidth="1.5"
                      markerEnd="url(#arrow)"
                    />
                    {edge.label && (
                      <text
                        x={`${mx}%`}
                        y={`${my}%`}
                        textAnchor="middle"
                        dy="-4"
                        fontSize="9"
                        className="fill-primary/50"
                        fontFamily="monospace"
                      >
                        {edge.label}
                      </text>
                    )}
                  </g>
                )
              })}
            </svg>

            {/* Nodes */}
            <div className="absolute inset-0 z-10 w-full h-full">
              {nodes.map((node) => {
                const colors = nodeTypeColors[node.type] ?? nodeTypeColors.concept
                const xPct = getXPct(node)
                const yPct = getYPct(node)
                return (
                  <button
                    key={node.id}
                    onClick={() => setSelectedNodeId(node.id)}
                    className={cn(
                      'absolute -translate-x-1/2 -translate-y-1/2 rounded-full px-3 py-1.5 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all duration-350 cursor-pointer shadow-lg hover:scale-110',
                      colors.node,
                      selectedNodeId === node.id && 'scale-110 ring-2 ring-primary ring-offset-background ring-offset-2',
                    )}
                    style={{
                      top: `${yPct}%`,
                      left: `${xPct}%`,
                      transform: `translate(-50%, -50%) scale(${zoomLevel / 100})`,
                    }}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-current shrink-0" />
                    {node.label}
                  </button>
                )
              })}
            </div>
          </>
        )}

        {/* Controls */}
        <div className="absolute top-4 right-4 flex gap-2 z-25 bg-card p-1.5 rounded-xl border border-border backdrop-blur-md">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setZoomLevel((z) => Math.max(50, z - 10))}
            className="text-muted-foreground hover:text-foreground rounded-lg"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <span className="text-[10px] font-mono text-muted-foreground flex items-center justify-center px-1">
            {zoomLevel}%
          </span>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setZoomLevel((z) => Math.min(200, z + 10))}
            className="text-muted-foreground hover:text-foreground rounded-lg"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setIsFullscreen((f) => !f)}
            className="text-muted-foreground hover:text-foreground rounded-lg ml-1"
            title="Toggle fullscreen"
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => refreshGraph.mutate()}
            disabled={refreshGraph.isPending}
            className="text-muted-foreground hover:text-foreground rounded-lg ml-1"
            title="Regenerate graph"
          >
            {refreshGraph.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
          </Button>
        </div>

        {/* Legend */}
        {!isEmpty && (
          <div className="absolute bottom-4 left-4 glass-panel p-3.5 rounded-xl border border-border bg-card/70 backdrop-blur-md text-[10px] space-y-1.5 z-25">
            <p className="font-mono font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
              <Network className="w-3.5 h-3.5 text-primary" />
              Concept Types
            </p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 font-medium">
              {legendItems.map(({ type, label }) => {
                const colors = nodeTypeColors[type]
                return (
                  <div key={type} className={cn('flex items-center gap-1.5', colors.node.split(' ')[1])}>
                    <span className={cn('w-2.5 h-2.5 rounded-full border', `bg-${type}-500/20 border-${type}-500`)} />
                    {label}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Minimap placeholder */}
        {!isFullscreen && !isEmpty && (
          <div className="absolute bottom-4 right-4 w-28 h-20 rounded-xl bg-card border border-border backdrop-blur-sm z-20 flex items-center justify-center text-[8px] text-muted-foreground font-mono select-none">
            {nodes.length} nodes · {edges.length} edges
          </div>
        )}
      </div>

      {/* Node Inspector Sidebar */}
      {selectedNode && (
        <div className="w-80 border-l border-border bg-card h-full flex flex-col shrink-0 z-20 p-5 space-y-4">
          <div className="flex items-center gap-2 border-b border-border pb-3 shrink-0">
            <Info className="w-4 h-4 text-primary" />
            <h3 className="font-headline font-bold text-sm text-foreground">Concept Inspector</h3>
          </div>

          <div className="flex-1 overflow-y-auto space-y-4 pr-1">
            <div>
              <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">
                Name
              </span>
              <h4 className="font-headline font-bold text-base text-foreground mt-1">
                {selectedNode.label}
              </h4>
              <span
                className={cn(
                  'text-[9px] font-mono font-semibold uppercase px-2 py-0.5 rounded-md border mt-1.5 inline-block',
                  nodeTypeColors[selectedNode.type]?.badge ?? '',
                )}
              >
                {selectedNode.type}
              </span>
            </div>

            {/* Connected nodes */}
            {edges.filter(
              (e) => e.source_node === selectedNode.id || e.target_node === selectedNode.id,
            ).length > 0 && (
              <div>
                <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block mb-2">
                  Connections
                </span>
                <div className="space-y-1.5">
                  {edges
                    .filter(
                      (e) =>
                        e.source_node === selectedNode.id || e.target_node === selectedNode.id,
                    )
                    .map((edge) => {
                      const otherId =
                        edge.source_node === selectedNode.id
                          ? edge.target_node
                          : edge.source_node
                      const other = nodes.find((n) => n.id === otherId)
                      const isOutgoing = edge.source_node === selectedNode.id
                      return (
                        <button
                          key={edge.id}
                          onClick={() => setSelectedNodeId(otherId)}
                          className="w-full flex items-center gap-2 text-xs text-foreground font-medium bg-background border border-border rounded-lg p-2.5 hover:border-primary/20 transition-all text-left active:scale-[0.98] duration-150"
                        >
                          <BookOpen className="w-3.5 h-3.5 text-primary shrink-0" />
                          <div className="min-w-0">
                            <p className="truncate">{other?.label ?? otherId}</p>
                            {edge.label && (
                              <p className="text-[9px] text-muted-foreground font-mono truncate">
                                {isOutgoing ? '→ ' : '← '}
                                {edge.label}
                              </p>
                            )}
                          </div>
                        </button>
                      )
                    })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// Re-export Sparkles to satisfy import
function Sparkles(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
    </svg>
  )
}

import { useEffect, useRef } from 'react'
import { Application, Graphics, Text, TextStyle } from 'pixi.js'
import { useSimulationStore } from '../../stores/simulation-store'
import type { SimEntity } from '../../types'

const stateColors: Record<string, number> = {
  healthy: 0x3fb950,
  degraded: 0xf0883e,
  warning: 0xfbbf24,
  critical: 0xf85149,
  exhausted: 0xf85149,
  dead: 0x5a6e91,
}

function drawScene(app: Application, entities: Record<string, SimEntity>) {
  const stage = app.stage
  stage.removeChildren()

  const g = new Graphics()
  stage.addChild(g)

  const textStyle = new TextStyle({
    fontFamily: 'JetBrains Mono',
    fontSize: 10,
    fill: 0x8a9bb8,
  })

  const entityList = Object.values(entities)
  const w = app.renderer ? app.renderer.width : 600
  const h = app.renderer ? app.renderer.height : 400
  const centerX = w / 2
  const centerY = h / 2

  entityList.forEach((entity: SimEntity, i: number) => {
    const x = centerX + Math.cos(i / entityList.length * Math.PI * 2) * 120
    const y = centerY + Math.sin(i / entityList.length * Math.PI * 2) * 120
    const radius = Math.max(10, 20 - entity.pressure * 0.1)
    const color = stateColors[entity.state] || 0x00d4ff

    g.circle(x, y, radius)
    g.fill({ color, alpha: entity.health / 100 })

    g.circle(x, y, radius + 3)
    g.stroke({ color: 0x00d4ff, width: 1, alpha: 0.3 })

    if (entity.pressure > 0) {
      g.circle(x, y, radius + entity.pressure * 0.3)
      g.stroke({ color: 0xf85149, width: 1, alpha: entity.pressure / 200 })
    }

    const text = new Text({
      text: entity.id.substring(0, 12),
      style: textStyle,
    })
    text.anchor.set(0.5, 0)
    text.position.set(x, y + radius + 8)
    stage.addChild(text)
  })
}

export function InfrastructureCanvas() {
  const canvasRef = useRef<HTMLDivElement>(null)
  const appRef = useRef<Application | null>(null)
  const entities = useSimulationStore((s) => s.entities)
  const time = useSimulationStore((s) => s.time)
  const running = useSimulationStore((s) => s.running)

  useEffect(() => {
    if (!canvasRef.current || appRef.current) return

    const app = new Application()
    appRef.current = app

    let destroyed = false

    ;(async () => {
      try {
        await app.init({
          resizeTo: canvasRef.current!,
          background: 0x0b0e14,
          antialias: true,
          resolution: window.devicePixelRatio || 1,
          autoDensity: true,
        })
        if (destroyed) return
        canvasRef.current?.appendChild(app.canvas as HTMLCanvasElement)
        const state = useSimulationStore.getState()
        drawScene(app, state.entities)
      } catch {
        // init failed
      }
    })()

    return () => {
      destroyed = true
      if (app.renderer) {
        app.destroy(true)
      }
      appRef.current = null
    }
  }, [])

  useEffect(() => {
    const app = appRef.current
    if (app?.renderer) {
      drawScene(app, entities)
    }
  }, [entities, time])

  return (
    <div className="rounded-xl overflow-hidden border border-infra-700">
      <div className="px-4 py-2 text-xs font-mono text-infra-300 border-b border-infra-700 flex items-center justify-between">
        <span>Infrastructure Canvas</span>
        <span className={running ? 'text-accent-green' : 'text-infra-500'}>
          {running ? '● live' : '○ paused'}
        </span>
      </div>
      <div ref={canvasRef} style={{ width: '100%', height: 400 }} />
    </div>
  )
}
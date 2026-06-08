import ReactEChartsCore from 'echarts-for-react'
import { useSimulationStore } from '../../stores/simulation-store'

export function LatencyChart() {
  const entities = useSimulationStore((s) => s.entities)

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' as const },
    grid: { left: 40, right: 10, top: 20, bottom: 25 },
    xAxis: {
      type: 'category' as const,
      data: Object.keys(entities).slice(0, 10),
      axisLabel: { color: '#8a9bb8', fontSize: 10 },
      axisLine: { lineStyle: { color: '#253045' } },
    },
    yAxis: {
      type: 'value' as const,
      name: 'ms',
      nameTextStyle: { color: '#5a6e91', fontSize: 10 },
      axisLabel: { color: '#8a9bb8', fontSize: 10 },
      splitLine: { lineStyle: { color: '#1a2332' } },
    },
    series: [{
      type: 'bar',
      data: Object.values(entities).slice(0, 10).map((e) => e.pressure),
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#00d4ff' },
            { offset: 1, color: '#3a4a66' },
          ],
        },
        borderRadius: [2, 2, 0, 0],
      },
    }],
  }

  return <ReactEChartsCore option={option} style={{ height: 200 }} notMerge />
}

export function ThroughputGauge() {
  const resources = useSimulationStore((s) => s.resources)
  const firstResource = Object.values(resources)[0]

  const option = {
    backgroundColor: 'transparent',
    series: [{
      type: 'gauge',
      startAngle: 220,
      endAngle: -40,
      radius: '80%',
      center: ['50%', '55%'],
      axisLine: {
        lineStyle: {
          width: 15,
          color: [
            [0.5, '#3fb950'],
            [0.8, '#fbbf24'],
            [1, '#f85149'],
          ],
        },
      },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: {
        fontSize: 18,
        color: '#e3eaf0',
        fontFamily: 'JetBrains Mono',
        formatter: '{value}%',
      },
      data: [{ value: firstResource?.utilization ?? 0, name: '' }],
    }],
  }

  return <ReactEChartsCore option={option} style={{ height: 200 }} notMerge />
}

export function CausalityTimeline() {
  const causalityChain = useSimulationStore((s) => s.causalityChain)

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' as const, formatter: (params: Array<{ value: number }>) => `Event #${params[0]?.value}` },
    grid: { left: 50, right: 10, top: 20, bottom: 30 },
    xAxis: {
      type: 'value' as const,
      name: 'tick',
      nameTextStyle: { color: '#5a6e91', fontSize: 10 },
      axisLabel: { color: '#8a9bb8', fontSize: 10 },
      splitLine: { lineStyle: { color: '#1a2332' } },
    },
    yAxis: {
      type: 'category' as const,
      data: causalityChain.slice(-20).map((c) => c.event.substring(0, 30)),
      axisLabel: { color: '#8a9bb8', fontSize: 9 },
    },
    series: [{
      type: 'bar',
      data: causalityChain.slice(-20).map((c) => c.chain),
      itemStyle: {
        color: (params: { value: number }) =>
          params.value > 80 ? '#f85149' : params.value > 40 ? '#fbbf24' : '#00d4ff',
        borderRadius: [0, 2, 2, 0],
      },
    }],
  }

  return <ReactEChartsCore option={option} style={{ height: 250 }} notMerge />
}

import React, { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Line, Html } from '@react-three/drei'
import * as THREE from 'three'
import { useAgentStore, AGENT_STATUS } from '../store/agentStore'

const STATUS_COLOR = {
  [AGENT_STATUS.IDLE]: '#475569',
  [AGENT_STATUS.THINKING]: '#F5A623',
  [AGENT_STATUS.ACTIVE]: '#5EEAD4',
  [AGENT_STATUS.ERROR]: '#F0654A'
}

function AgentNode({ agent, onSelect, isSelected }) {
  const meshRef = useRef()
  const ringRef = useRef()
  const color = STATUS_COLOR[agent.status] ?? STATUS_COLOR.idle
  const isLive = agent.status === AGENT_STATUS.ACTIVE || agent.status === AGENT_STATUS.THINKING

  useFrame(({ clock }) => {
    if (!meshRef.current) return
    const t = clock.getElapsedTime()
    if (isLive) {
      const pulse = 1 + Math.sin(t * (agent.status === AGENT_STATUS.ACTIVE ? 3 : 1.6)) * 0.08
      meshRef.current.scale.setScalar(pulse)
    } else {
      meshRef.current.scale.setScalar(1)
    }
    if (ringRef.current) {
      ringRef.current.rotation.z = t * 0.4
    }
  })

  return (
    <group position={agent.position}>
      <mesh
        ref={meshRef}
        onClick={(e) => {
          e.stopPropagation()
          onSelect(agent.id)
        }}
      >
        <icosahedronGeometry args={[0.42, 1]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={isLive ? 0.9 : 0.25}
          roughness={0.35}
          metalness={0.2}
          wireframe={agent.role === 'planner'}
        />
      </mesh>

      {isLive && (
        <mesh ref={ringRef}>
          <torusGeometry args={[0.62, 0.012, 8, 48]} />
          <meshBasicMaterial color={color} transparent opacity={0.5} />
        </mesh>
      )}

      {isSelected && (
        <mesh>
          <torusGeometry args={[0.74, 0.01, 8, 48]} />
          <meshBasicMaterial color="#E2E8F0" transparent opacity={0.6} />
        </mesh>
      )}

      <Html distanceFactor={8} position={[0, -0.78, 0]} center occlude>
        <div
          style={{
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: '11px',
            color: isLive ? color : '#8B96A5',
            whiteSpace: 'nowrap',
            textAlign: 'center',
            userSelect: 'none',
            letterSpacing: '0.02em'
          }}
        >
          {agent.name}
        </div>
      </Html>
    </group>
  )
}

function Connections({ agents }) {
  const planner = agents.find((a) => a.role === 'planner')
  if (!planner) return null
  const others = agents.filter((a) => a.role !== 'planner')

  return (
    <>
      {others.map((agent) => {
        const isLive = agent.status === AGENT_STATUS.ACTIVE || agent.status === AGENT_STATUS.THINKING
        return (
          <Line
            key={agent.id}
            points={[planner.position, agent.position]}
            color={isLive ? STATUS_COLOR[agent.status] : '#1F2733'}
            lineWidth={isLive ? 1.6 : 1}
            transparent
            opacity={isLive ? 0.65 : 0.35}
          />
        )
      })}
    </>
  )
}

function FlowParticles({ agents }) {
  const planner = agents.find((a) => a.role === 'planner')
  const activeAgents = useMemo(
    () => agents.filter((a) => a.role !== 'planner' && a.status === AGENT_STATUS.ACTIVE),
    [agents]
  )
  const refs = useRef([])

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime()
    activeAgents.forEach((agent, i) => {
      const mesh = refs.current[i]
      if (!mesh || !planner) return
      const speed = 0.6
      const progress = (t * speed + i * 0.33) % 1
      mesh.position.lerpVectors(
        new THREE.Vector3(...planner.position),
        new THREE.Vector3(...agent.position),
        progress
      )
    })
  })

  if (!planner) return null

  return (
    <>
      {activeAgents.map((agent, i) => (
        <mesh key={agent.id} ref={(el) => (refs.current[i] = el)}>
          <sphereGeometry args={[0.045, 8, 8]} />
          <meshBasicMaterial color={STATUS_COLOR[agent.status]} />
        </mesh>
      ))}
    </>
  )
}

function GridFloor() {
  return (
    <gridHelper
      args={[14, 28, '#1F2733', '#161C26']}
      position={[0, -2.6, 0]}
    />
  )
}

export default function AgentGraph3D() {
  const agents = useAgentStore((s) => s.agents)
  const selectedAgentId = useAgentStore((s) => s.selectedAgentId)
  const setSelectedAgent = useAgentStore((s) => s.setSelectedAgent)

  return (
    <div className="relative w-full h-full">
      <Canvas
        camera={{ position: [0, 0.6, 6.5], fov: 42 }}
        gl={{ antialias: true, alpha: true }}
        onPointerMissed={() => setSelectedAgent(null)}
      >
        <ambientLight intensity={0.5} />
        <pointLight position={[4, 4, 4]} intensity={0.7} color="#5EEAD4" />
        <pointLight position={[-4, -2, 2]} intensity={0.4} color="#7C7AED" />

        <GridFloor />
        <Connections agents={agents} />
        <FlowParticles agents={agents} />

        {agents.map((agent) => (
          <AgentNode
            key={agent.id}
            agent={agent}
            onSelect={setSelectedAgent}
            isSelected={selectedAgentId === agent.id}
          />
        ))}

        <OrbitControls
          enablePan={false}
          minDistance={4}
          maxDistance={10}
          autoRotate
          autoRotateSpeed={0.35}
          maxPolarAngle={Math.PI * 0.65}
          minPolarAngle={Math.PI * 0.25}
        />
      </Canvas>

      <div className="absolute top-4 left-4 text-[11px] text-slate-faint tracking-wide pointer-events-none">
        <span className="text-signal/70">drag</span> to orbit · <span className="text-signal/70">click</span> a node to inspect
      </div>
    </div>
  )
}

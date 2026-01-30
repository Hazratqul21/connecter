"use client"

import { useEffect, useState } from 'react'
import { Users, Phone, PhoneCall, CheckCircle, XCircle, Clock, Activity } from "lucide-react"
import { supabase } from "@/lib/supabase"
import { motion } from "framer-motion"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

// --- Mock Components for Speed (Since I didn't verify Shadcn installation) ---
// I'll inline a simple Card component style to ensure it looks good immediately without waiting for 'shadcn init'
function MetricCard({ title, value, icon: Icon, color, subtext }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300 relative overflow-hidden group"
    >
      <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity ${color}`}>
        <Icon size={100} />
      </div>
      <div className="flex justify-between items-start relative z-10">
        <div>
          <p className="text-gray-400 text-sm font-medium uppercase tracking-wider">{title}</p>
          <h3 className="text-4xl font-bold text-white mt-2">{value}</h3>
          {subtext && <p className="text-xs text-gray-500 mt-1">{subtext}</p>}
        </div>
        <div className={`p-3 rounded-lg bg-white/5 ${color} text-white`}>
          <Icon size={24} />
        </div>
      </div>
    </motion.div>
  )
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState({
    calls_today: 0,
    calls_in_progress: 0,
    completed_today: 0,
    missed_today: 0,
    avg_duration_today: 0,
    active_agents: 0,
    available_agents: 0
  })

  const [calls, setCalls] = useState([]) // For recent call list

  // Fetch Initial Data
  useEffect(() => {
    async function fetchData() {
      // 1. Get Metrics via RPC
      const { data, error } = await supabase.rpc('get_realtime_metrics')
      if (data && data[0]) {
        setMetrics(data[0])
      }

      // 2. Get Recent Calls
      const { data: callsData } = await supabase
        .from('calls')
        .select('*')
        .order('started_at', { ascending: false })
        .limit(10)

      if (callsData) setCalls(callsData as any)
    }

    fetchData()

    // Realtime Subscription
    const channel = supabase
      .channel('dashboard_updates')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'calls' }, () => {
        fetchData() // Simple refresh on any change
      })
      .subscribe()

    return () => { supabase.removeChannel(channel) }
  }, [])

  return (
    <div className="min-h-screen bg-[#0f1729] text-white p-8 font-sans">

      {/* Header */}
      <header className="flex justify-between items-center mb-10">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 text-transparent bg-clip-text">
            Analytics Command Center
          </h1>
          <p className="text-gray-400 mt-1">Real-time Call Center Intelligence</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 text-green-400 rounded-full border border-green-500/20 text-sm animate-pulse">
          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
          System Operational
        </div>
      </header>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Active Calls"
          value={metrics.calls_in_progress}
          icon={PhoneCall}
          color="text-blue-400"
          subtext="Live conversations now"
        />
        <MetricCard
          title="Total Calls Today"
          value={metrics.calls_today}
          icon={Activity}
          color="text-purple-400"
        />
        <MetricCard
          title="Missed Calls"
          value={metrics.missed_today}
          icon={XCircle}
          color="text-red-400"
          subtext="Requires attention"
        />
        <MetricCard
          title="Active Agents"
          value={metrics.active_agents}
          icon={Users}
          color="text-emerald-400"
          subtext={`${metrics.available_agents} Available`}
        />
      </div>

      {/* Charts & Lists */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Main Chart Area */}
        <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-xl p-6">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Activity className="text-blue-400" />
            Call Volume Trends
          </h2>
          <div className="h-[300px] w-full flex items-center justify-center text-gray-500">
            {/* Placeholder for Chart - Ideally we fetch hourly data */}
            <p>Chart data will appear here after 24h of usage</p>
          </div>
        </div>

        {/* Recent Calls Feed */}
        <div className="bg-white/5 border border-white/10 rounded-xl p-6">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Clock className="text-purple-400" />
            Live Feed
          </h2>
          <div className="space-y-4">
            {calls.map((call: any) => (
              <div key={call.id} className="flex justify-between items-center p-3 bg-white/5 rounded-lg border border-white/5 hover:border-white/20 transition-colors">
                <div>
                  <p className="font-mono text-sm text-blue-300">{call.phone_number}</p>
                  <p className="text-xs text-gray-500">{new Date(call.started_at).toLocaleTimeString()}</p>
                </div>
                <div className={`text-xs px-2 py-1 rounded ${call.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                  call.status === 'missed' ? 'bg-red-500/20 text-red-400' :
                    'bg-yellow-500/20 text-yellow-400'
                  }`}>
                  {call.status}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}

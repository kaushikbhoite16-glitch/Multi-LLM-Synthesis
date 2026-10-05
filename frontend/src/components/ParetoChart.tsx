import React from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Line,
  ComposedChart
} from 'recharts';

interface ParetoPoint {
  name: string;
  provider: string;
  cost: number;
  quality: number;
  tokens: number;
  latency: number;
  is_pareto?: boolean;
}

interface ParetoChartProps {
  data: ParetoPoint[];
}

export const ParetoChart: React.FC<ParetoChartProps> = ({ data }) => {
  // Sort pareto points by cost to draw the frontier line
  const paretoPoints = data.filter(d => d.is_pareto).sort((a, b) => a.cost - b.cost);

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <h4 className="font-semibold text-white text-xs sm:text-sm">Quality vs. Cost Trade-off & Pareto Frontier</h4>
          <p className="text-[11px] text-slate-400">
            Frontier curves identify responses with optimal quality-to-cost efficiency
          </p>
        </div>
        <div className="flex items-center space-x-3 text-xs font-mono">
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
            <span className="text-slate-300">Pareto Optimal</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-400"></span>
            <span className="text-slate-400">Standard Model</span>
          </span>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            margin={{ top: 20, right: 30, bottom: 20, left: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              type="number"
              dataKey="cost"
              name="API Cost"
              unit="$"
              domain={['auto', 'auto']}
              tickFormatter={(v) => `$${v.toFixed(4)}`}
              stroke="#64748b"
              fontSize={11}
            />
            <YAxis
              type="number"
              dataKey="quality"
              name="Quality Score"
              domain={[7.0, 10.0]}
              stroke="#64748b"
              fontSize={11}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload as ParetoPoint;
                  return (
                    <div className="bg-slate-900 border border-slate-700 p-3 rounded-xl shadow-xl text-xs space-y-1 font-mono">
                      <p className="font-bold text-white text-sm">{d.name}</p>
                      <p className="text-slate-400">Provider: {d.provider}</p>
                      <div className="pt-1 border-t border-slate-800 space-y-0.5">
                        <p className="text-sky-400">Quality: {d.quality.toFixed(2)}/10</p>
                        <p className="text-emerald-400">Cost: ${d.cost.toFixed(5)}</p>
                        <p className="text-slate-300">Tokens: {d.tokens}</p>
                        <p className="text-slate-400">Latency: {d.latency} ms</p>
                        {d.is_pareto && (
                          <span className="inline-block mt-1 text-[10px] bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded border border-emerald-800">
                            Pareto Efficient
                          </span>
                        )}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            {/* Draw frontier connecting line */}
            <Line
              type="monotone"
              data={paretoPoints}
              dataKey="quality"
              stroke="#10b981"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
              isAnimationActive={false}
            />
            {/* Scatter points */}
            <Scatter name="Models" data={data}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.is_pareto ? '#10b981' : '#38bdf8'}
                  stroke={entry.is_pareto ? '#059669' : '#0284c7'}
                  strokeWidth={2}
                  r={entry.name.includes('Synthesized') ? 8 : 6}
                />
              ))}
            </Scatter>
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

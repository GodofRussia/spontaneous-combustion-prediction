import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

const MetricsChart = ({ metrics }) => {
  if (!metrics) return null;

  const data = [
    {
      name: '±1 день',
      accuracy: (metrics.accuracy_pm1 * 100).toFixed(1),
    },
    {
      name: '±2 дня',
      accuracy: (metrics.accuracy_pm2 * 100).toFixed(1),
      target: true,
    },
    {
      name: '±3 дня',
      accuracy: (metrics.accuracy_pm3 * 100).toFixed(1),
    },
  ];

  return (
    <div className="metrics-chart">
      <h3>Точность по допуску</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[0, 100]} label={{ value: 'Точность (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip formatter={(value) => `${value}%`} />
          <Legend />
          <ReferenceLine y={70} stroke="#c92a2a" strokeDasharray="3 3" label="Целевая точность (70%)" />
          <Bar dataKey="accuracy" fill="#4c6ef5" name="Точность" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default MetricsChart;
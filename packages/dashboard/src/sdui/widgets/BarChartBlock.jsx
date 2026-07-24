import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const VARIANT_COLORS = ['var(--accent)', '#64748b'];

export default function BarChartBlock({
  title,
  yLabel,
  mode = 'simple',
  series = [],
  categories = [],
  groupedSeries = [],
}) {
  if (mode === 'grouped' && categories.length && groupedSeries.length) {
    const data = categories.map((cat, index) => {
      const point = { name: cat };
      groupedSeries.forEach((variant) => {
        point[variant.name] = variant.values[index] ?? 0;
      });
      return point;
    });

    return (
      <div className="sdui-chart sdui-bar-chart">
        {title && <h4 className="sdui-chart-title">{title}</h4>}
        {yLabel && <p className="sdui-chart-ylabel">{yLabel}</p>}
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={60} />
            <YAxis tick={{ fontSize: 12 }} width={40} />
            <Tooltip formatter={(v) => [v, yLabel || 'count']} />
            <Legend />
            {groupedSeries.map((variant, index) => (
              <Bar
                key={variant.name}
                dataKey={variant.name}
                fill={VARIANT_COLORS[index % VARIANT_COLORS.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (!series.length) return null;
  const data = series.map((s) => ({ name: s.name, value: s.value }));

  return (
    <div className="sdui-chart sdui-bar-chart">
      {title && <h4 className="sdui-chart-title">{title}</h4>}
      {yLabel && <p className="sdui-chart-ylabel">{yLabel}</p>}
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} width={40} />
          <Tooltip formatter={(v) => [v, yLabel || 'value']} />
          <Bar dataKey="value" fill="var(--accent)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

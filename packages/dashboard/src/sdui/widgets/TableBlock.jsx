export default function TableBlock({ title, columns = [], rows = [] }) {
  if (!columns.length || !rows.length) return null;

  return (
    <div className="sdui-table-wrap">
      {title && <h4 className="sdui-chart-title">{title}</h4>}
      <div className="sdui-table-scroll">
        <table className="sdui-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

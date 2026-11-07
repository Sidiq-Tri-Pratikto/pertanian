import { useId, type CSSProperties } from 'react';

import type { ChartDataTableProps } from '@/components/hd/HDChartDataTable';
import { tokens } from '@/design/tokens.generated';

import './HDChartDataTable.css';

const style = {
  '--chart-table-text': tokens.color.textPrimary,
  '--chart-table-secondary': tokens.color.textSecondary,
  '--chart-table-border': tokens.color.borderDecorative,
  '--chart-table-padding': `${tokens.space.stackTight}px`,
} as CSSProperties;

/** Explicit roles and header IDs preserve table navigation when CSS stacks the rows. */
export function HDChartDataTable({ caption, columns, rows }: ChartDataTableProps) {
  const id = useId();
  const captionId = `${id}-caption`;
  return (
    <table className="hd-chart-data-table" role="table" aria-labelledby={captionId} style={style}>
      <caption id={captionId}>{caption}</caption>
      <thead role="rowgroup">
        <tr role="row">
          {columns.map((column) => (
            <th key={column.key} id={`${id}-col-${column.key}`} role="columnheader" scope="col">{column.label}</th>
          ))}
        </tr>
      </thead>
      <tbody role="rowgroup">
        {rows.map((row, index) => {
          const rowId = `${id}-row-${index}`;
          return (
            <tr key={rowId} role="row">
              {columns.map((column, columnIndex) => {
                const header = `${id}-col-${column.key}`;
                const contents = (
                  <>
                    <span className="hd-chart-data-label" aria-hidden="true">{column.label}</span>
                    <span>{row[column.key] || 'Tidak ada data'}</span>
                  </>
                );
                return columnIndex === 0
                  ? <th key={column.key} id={rowId} role="rowheader" scope="row" headers={header}>{contents}</th>
                  : <td key={column.key} role="cell" headers={`${rowId} ${header}`}>{contents}</td>;
              })}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

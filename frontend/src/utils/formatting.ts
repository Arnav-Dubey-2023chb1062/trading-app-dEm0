export function formatCurrency(value: number | undefined | null, currencySymbol: string = '$'): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return `${currencySymbol}${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatNumber(value: number | undefined | null, minimumFractionDigits: number = 0, maximumFractionDigits: number = 2 ): string {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A';
  }
  return value.toLocaleString(undefined, { minimumFractionDigits, maximumFractionDigits });
}

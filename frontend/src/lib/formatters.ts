// Memoized formatters to avoid recreating Intl instances on every render

const currencyFormatter = new Intl.NumberFormat('es-CL', {
  style: 'currency',
  currency: 'CLP',
  minimumFractionDigits: 0,
});

const shortDateFormatter = new Intl.DateTimeFormat('es-CL', {
  day: 'numeric',
  month: 'short',
});

const mediumDateFormatter = new Intl.DateTimeFormat('es-CL', {
  month: 'short',
  year: 'numeric',
});

const longDateFormatter = new Intl.DateTimeFormat('es-CL', {
  month: 'long',
  year: 'numeric',
});

export function formatCurrency(amount: number): string {
  return currencyFormatter.format(amount);
}

export function formatShortDate(dateStr: string): string {
  return shortDateFormatter.format(new Date(dateStr));
}

export function formatMediumDate(dateStr: string): string {
  return mediumDateFormatter.format(new Date(dateStr));
}

export function formatLongDate(dateStr: string): string {
  return longDateFormatter.format(new Date(dateStr));
}

interface FizkoLogoProps {
  className?: string;
}

export function FizkoLogo({ className = "h-5 w-5" }: FizkoLogoProps) {
  return (
    <img
      src="/encabezado.png"
      alt="Fizko"
      className={className}
      style={{ objectFit: 'contain' }}
    />
  );
}

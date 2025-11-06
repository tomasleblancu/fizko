interface HeartbeatLogoProps {
  className?: string;
}

export function HeartbeatLogo({ className = "h-12 w-12" }: HeartbeatLogoProps) {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <style>{`
        @keyframes heartbeat-left {
          0%, 100% {
            transform: translateX(-8px);
          }
          15% {
            transform: translateX(-20px);
          }
          30% {
            transform: translateX(-8px);
          }
          45% {
            transform: translateX(-24px);
          }
          60% {
            transform: translateX(-8px);
          }
        }

        @keyframes heartbeat-right {
          0%, 100% {
            transform: translateX(8px);
          }
          15% {
            transform: translateX(20px);
          }
          30% {
            transform: translateX(8px);
          }
          45% {
            transform: translateX(24px);
          }
          60% {
            transform: translateX(8px);
          }
        }

        .animate-heartbeat-left {
          animation: heartbeat-left 1.5s ease-in-out infinite;
        }

        .animate-heartbeat-right {
          animation: heartbeat-right 1.5s ease-in-out infinite;
        }
      `}</style>
      {/* Left parenthesis - animates to the left */}
      <img
        src="/parentesis_izq.svg"
        alt="("
        className="h-full w-auto animate-heartbeat-left"
        style={{ objectFit: 'contain' }}
      />
      {/* Right parenthesis - animates to the right */}
      <img
        src="/parentesis_der.svg"
        alt=")"
        className="h-full w-auto animate-heartbeat-right"
        style={{ objectFit: 'contain' }}
      />
    </div>
  );
}

export default function FullScreenLoader({ label = 'Loading...' }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-0">
      <p className="label-eyebrow">{label}</p>
    </div>
  );
}

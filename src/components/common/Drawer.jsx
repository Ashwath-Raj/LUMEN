/**
 * Right-hand slide-over used for "Inspector Details" (Reconstruction Board)
 * and similar contextual detail panels that float above a workspace.
 */
export default function Drawer({ isOpen, onClose, title, children }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <button
        type="button"
        aria-label="Close panel"
        onClick={onClose}
        className="absolute inset-0 bg-black/50"
      />
      <div className="relative w-96 h-full bg-surface-1 border-l border-border-subtle p-4 overflow-y-auto">
        {title && <h2 className="font-display text-xl mb-4">{title}</h2>}
        {children}
      </div>
    </div>
  );
}

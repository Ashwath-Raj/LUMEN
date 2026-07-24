/**
 * "03:45 AM - Oct 12 / Signal Lost / Subject's burner device went
 * offline..." entry used on the Timeline tab of the Case Board.
 */
export default function TimelineNode({ timestamp, title, description }) {
  return (
    <div className="border-l-2 border-accent-gold pl-4 py-2">
      <p className="label-eyebrow">{timestamp}</p>
      <p className="font-display">{title}</p>
      <p className="text-ink-secondary text-sm">{description}</p>
    </div>
  );
}

import { useCallback, useState } from 'react';

/**
 * Reused by FIR Upload (Operations) and FIR Intelligence document viewer
 * (Investigation). Handles drag state only — actual upload wiring happens
 * via the `onFiles` callback + relevant service module.
 */
export default function UploadDropzone({ onFiles, accept, label = 'Drag & drop a file here' }) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragOver(false);
      onFiles?.(Array.from(e.dataTransfer.files));
    },
    [onFiles]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      className={`border border-dashed rounded-md p-8 text-center text-sm ${
        isDragOver ? 'border-accent-gold text-accent-gold' : 'border-border-strong text-ink-muted'
      }`}
    >
      <input
        type="file"
        accept={accept}
        className="hidden"
        id="upload-dropzone-input"
        onChange={(e) => onFiles?.(Array.from(e.target.files))}
      />
      <label htmlFor="upload-dropzone-input" className="cursor-pointer">
        {label}
      </label>
    </div>
  );
}

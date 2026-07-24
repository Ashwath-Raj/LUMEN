import { useState } from 'react';
import { FileWarning } from 'lucide-react';
import { submitFirUpload, fetchSuspectPreviousRecords } from '@/services/api/operationsService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import FormField from '@/components/common/FormField.jsx';
import UploadDropzone from '@/components/common/UploadDropzone.jsx';
import Button from '@/components/common/Button.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';

const REQUIRED_FIELDS = ['name', 'address', 'contact', 'incidentLocation', 'incidentDateTime'];

export default function FirUploadPage() {
  const [form, setForm] = useState({
    name: '',
    address: '',
    contact: '',
    incidentLocation: '',
    incidentDateTime: '',
    firSection: '',
  });
  const [errors, setErrors] = useState({});
  const [file, setFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  const [previousRecords, setPreviousRecords] = useState(null);
  const [isLookingUp, setIsLookingUp] = useState(false);

  const setField = (key) => (e) => setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const validate = () => {
    const next = {};
    REQUIRED_FIELDS.forEach((key) => {
      if (!form[key].trim()) next[key] = 'This field is required.';
    });
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleLookup = async () => {
    if (!form.name.trim()) {
      setErrors((prev) => ({ ...prev, name: 'Enter a name to look up prior records.' }));
      return;
    }
    setIsLookingUp(true);
    try {
      const records = await fetchSuspectPreviousRecords(form.name);
      setPreviousRecords(records);
    } finally {
      setIsLookingUp(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const formData = new FormData();
      Object.entries(form).forEach(([key, value]) => formData.append(key, value));
      if (file) formData.append('scan', file);
      await submitFirUpload(formData);
      setSubmitted(true);
    } catch (err) {
      setSubmitError(err?.message ?? 'Submission failed. Try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="p-8 max-w-[900px] mx-auto">
        <EmptyState
          icon={FileWarning}
          title="FIR submitted successfully"
          message="The report has been logged and routed for review."
          action={
            <Button variant="ghost" onClick={() => setSubmitted(false)} className="mt-2">
              Submit another FIR
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-[1300px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Operations"
        title="FIR Upload"
        description="Submit a First Information Report for structured intake and cross-reference against existing records."
      />

      <form onSubmit={handleSubmit} noValidate className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
        <div className="panel p-5 flex flex-col gap-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField label="Full Name" htmlFor="name" error={errors.name}>
              <input
                id="name"
                value={form.name}
                onChange={setField('name')}
                className="bg-surface-2 border border-border-subtle rounded-sm px-3 py-2 text-sm text-ink-primary focus:border-accent-gold outline-none transition-colors"
              />
            </FormField>
            <FormField label="Contact Number" htmlFor="contact" error={errors.contact}>
              <input
                id="contact"
                value={form.contact}
                onChange={setField('contact')}
                className="bg-surface-2 border border-border-subtle rounded-sm px-3 py-2 text-sm text-ink-primary focus:border-accent-gold outline-none transition-colors"
              />
            </FormField>
          </div>

          <FormField label="Address" htmlFor="address" error={errors.address}>
            <input
              id="address"
              value={form.address}
              onChange={setField('address')}
              className="bg-surface-2 border border-border-subtle rounded-sm px-3 py-2 text-sm text-ink-primary focus:border-accent-gold outline-none transition-colors"
            />
          </FormField>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField label="Incident Location" htmlFor="incidentLocation" error={errors.incidentLocation}>
              <input
                id="incidentLocation"
                value={form.incidentLocation}
                onChange={setField('incidentLocation')}
                className="bg-surface-2 border border-border-subtle rounded-sm px-3 py-2 text-sm text-ink-primary focus:border-accent-gold outline-none transition-colors"
              />
            </FormField>
            <FormField label="Incident Date & Time" htmlFor="incidentDateTime" error={errors.incidentDateTime}>
              <input
                id="incidentDateTime"
                type="datetime-local"
                value={form.incidentDateTime}
                onChange={setField('incidentDateTime')}
                className="bg-surface-2 border border-border-subtle rounded-sm px-3 py-2 text-sm text-ink-primary focus:border-accent-gold outline-none transition-colors"
              />
            </FormField>
          </div>

          <FormField label="Known FIR Section(s)" htmlFor="firSection">
            <input
              id="firSection"
              value={form.firSection}
              onChange={setField('firSection')}
              placeholder="e.g. Section 154 CR.P.C."
              className="bg-surface-2 border border-border-subtle rounded-sm px-3 py-2 text-sm text-ink-primary placeholder:text-ink-muted focus:border-accent-gold outline-none transition-colors"
            />
          </FormField>

          <div>
            <p className="label-eyebrow mb-2">FIR Scan / Photo</p>
            <UploadDropzone onFiles={(files) => setFile(files[0] ?? null)} accept=".pdf,.jpg,.png" />
            {file && <p className="text-xs text-ink-muted mt-1.5">Selected: {file.name}</p>}
          </div>

          {submitError && <p className="text-status-critical text-sm">{submitError}</p>}

          <div className="flex justify-end gap-3 mt-2">
            <Button type="button" variant="ghost" onClick={handleLookup} disabled={isLookingUp}>
              {isLookingUp ? 'Looking up...' : 'Check Previous Records'}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Submitting...' : 'Submit FIR'}
            </Button>
          </div>
        </div>

        <div className="panel p-4 h-fit">
          <h3 className="font-display text-lg mb-3">Suspect Previous Records</h3>
          {!previousRecords ? (
            <p className="text-ink-muted text-sm">
              Enter a name and click &quot;Check Previous Records&quot; to search existing files.
            </p>
          ) : previousRecords.length === 0 ? (
            <p className="text-ink-muted text-sm">No prior records found.</p>
          ) : (
            <ul className="flex flex-col divide-y divide-border-subtle">
              {previousRecords.map((rec) => (
                <li key={rec.id} className="py-2.5 text-sm">
                  <div className="flex justify-between">
                    <span className="text-ink-primary">{rec.charge}</span>
                    <span className="text-xs text-ink-muted">{rec.date}</span>
                  </div>
                  <p className="text-xs text-ink-muted mt-0.5">Outcome: {rec.outcome}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </form>
    </div>
  );
}

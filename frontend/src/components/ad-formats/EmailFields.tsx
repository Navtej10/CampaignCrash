import { useState } from "react";

interface Props {
  value: { subject: string; preview_text: string; body: string };
  onChange: (value: any) => void;
}

export default function EmailFields({ value, onChange }: Props) {
  return (
    <div className="field-group">
      <div className="field">
        <label>Subject</label>
        <input
          type="text"
          value={value.subject || ""}
          onChange={(e) => onChange({ ...value, subject: e.target.value })}
          required
        />
      </div>
      <div className="field">
        <label>Preview Text</label>
        <input
          type="text"
          value={value.preview_text || ""}
          onChange={(e) => onChange({ ...value, preview_text: e.target.value })}
          required
        />
      </div>
      <div className="field">
        <label>Body</label>
        <textarea
          rows={5}
          value={value.body || ""}
          onChange={(e) => onChange({ ...value, body: e.target.value })}
          required
        />
      </div>
    </div>
  );
}

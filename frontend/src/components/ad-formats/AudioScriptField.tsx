import { useState } from "react";

interface Props {
  value: { script: string; audio_platform: "podcast_preroll" | "radio" | "other" };
  onChange: (value: any) => void;
}

export default function AudioScriptField({ value, onChange }: Props) {
  return (
    <div className="field-group">
      <div className="field">
        <label>Platform</label>
        <select
          value={value.audio_platform || "podcast_preroll"}
          onChange={(e) => onChange({ ...value, audio_platform: e.target.value })}
        >
          <option value="podcast_preroll">Podcast Preroll</option>
          <option value="radio">Radio</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div className="field">
        <label>Script</label>
        <textarea
          rows={5}
          value={value.script || ""}
          onChange={(e) => onChange({ ...value, script: e.target.value })}
          required
        />
      </div>
    </div>
  );
}

import { useState } from "react";

interface Props {
  value: { headlines: string[]; descriptions: string[] };
  onChange: (value: any) => void;
}

export default function SearchAdFields({ value, onChange }: Props) {
  const headlines = value.headlines || [""];
  const descriptions = value.descriptions || [""];

  function updateHeadline(idx: number, val: string) {
    const newHeadlines = [...headlines];
    newHeadlines[idx] = val;
    onChange({ ...value, headlines: newHeadlines });
  }

  function updateDescription(idx: number, val: string) {
    const newDescriptions = [...descriptions];
    newDescriptions[idx] = val;
    onChange({ ...value, descriptions: newDescriptions });
  }

  function addHeadline() {
    if (headlines.length < 3) onChange({ ...value, headlines: [...headlines, ""] });
  }

  function addDescription() {
    if (descriptions.length < 2) onChange({ ...value, descriptions: [...descriptions, ""] });
  }

  return (
    <div className="field-group">
      <div className="field">
        <label>Headlines (Max 3, 30 chars each)</label>
        {headlines.map((h, i) => (
          <div key={i} style={{ display: "flex", gap: "8px", marginBottom: "4px" }}>
            <input
              type="text"
              value={h}
              maxLength={30}
              onChange={(e) => updateHeadline(i, e.target.value)}
              required
            />
            <span style={{ fontSize: "0.8rem", color: h.length > 30 ? "red" : "#666", alignSelf: "center" }}>
              {h.length}/30
            </span>
          </div>
        ))}
        {headlines.length < 3 && (
          <button type="button" onClick={addHeadline} style={{ fontSize: "0.8rem" }}>+ Add Headline</button>
        )}
      </div>

      <div className="field">
        <label>Descriptions (Max 2, 90 chars each)</label>
        {descriptions.map((d, i) => (
          <div key={i} style={{ display: "flex", gap: "8px", marginBottom: "4px" }}>
            <textarea
              rows={2}
              value={d}
              maxLength={90}
              onChange={(e) => updateDescription(i, e.target.value)}
              required
            />
            <span style={{ fontSize: "0.8rem", color: d.length > 90 ? "red" : "#666", alignSelf: "center" }}>
              {d.length}/90
            </span>
          </div>
        ))}
        {descriptions.length < 2 && (
          <button type="button" onClick={addDescription} style={{ fontSize: "0.8rem" }}>+ Add Description</button>
        )}
      </div>
    </div>
  );
}

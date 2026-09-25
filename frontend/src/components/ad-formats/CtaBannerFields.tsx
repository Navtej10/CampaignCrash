import { ChangeEvent } from "react";

interface Props {
  value: { headline: string; subtext: string; button_text: string };
  onChange: (value: any) => void;
}

export default function CtaBannerFields({ value, onChange }: Props) {
  return (
    <div className="field-group">
      <div className="field">
        <label>Headline</label>
        <input
          type="text"
          value={value.headline || ""}
          onChange={(e) => onChange({ ...value, headline: e.target.value })}
          required
        />
      </div>
      <div className="field">
        <label>Subtext</label>
        <input
          type="text"
          value={value.subtext || ""}
          onChange={(e) => onChange({ ...value, subtext: e.target.value })}
          required
        />
      </div>
      <div className="field">
        <label>Button Text</label>
        <input
          type="text"
          value={value.button_text || ""}
          onChange={(e) => onChange({ ...value, button_text: e.target.value })}
          required
        />
      </div>
    </div>
  );
}

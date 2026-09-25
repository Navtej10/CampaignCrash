import { ChangeEvent } from "react";

interface Props {
  value: { text: string };
  onChange: (value: { text: string }) => void;
}

export default function TextCopyFields({ value, onChange }: Props) {
  return (
    <div className="field">
      <label>Ad Copy</label>
      <textarea
        rows={5}
        placeholder="Paste the ad copy..."
        value={value.text || ""}
        onChange={(e) => onChange({ ...value, text: e.target.value })}
        required
      />
    </div>
  );
}

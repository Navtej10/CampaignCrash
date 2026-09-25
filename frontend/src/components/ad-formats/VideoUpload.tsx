interface Props {
  value: { upload_id: string; platform: string };
  onChange: (value: any) => void;
}

export default function VideoUpload({ value, onChange }: Props) {
  return (
    <div className="field-group">
      <div className="field">
        <label>Platform (e.g. TikTok, YouTube)</label>
        <input
          type="text"
          value={value.platform || ""}
          onChange={(e) => onChange({ ...value, platform: e.target.value })}
          required
        />
      </div>
      <div className="field">
        <label>Video Upload ID</label>
        <input
          type="text"
          placeholder="Mock ID for now"
          value={value.upload_id || ""}
          onChange={(e) => onChange({ ...value, upload_id: e.target.value })}
          required
        />
      </div>
    </div>
  );
}

import { useState, ChangeEvent } from "react";

interface Props {
  value: { upload_id: string; platform: string };
  onChange: (value: any) => void;
}

export default function VideoUpload({ value, onChange }: Props) {
  const [uploading, setUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  async function handleVideoUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    
    // Create preview
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/api/campaigns/upload-video", {
        method: "POST",
        body: formData,
      });
      if (response.ok) {
        const data = await response.json();
        onChange({ ...value, upload_id: data.upload_id });
      } else {
        alert("Upload failed.");
      }
    } catch (error) {
      console.error(error);
      alert("Error uploading video.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="field-group">
      <div className="field">
        <label>Platform</label>
        <select
          value={value.platform || ""}
          onChange={(e) => onChange({ ...value, platform: e.target.value })}
          required
        >
          <option value="" disabled>Select platform...</option>
          <option value="reels">Reels</option>
          <option value="tiktok_style">TikTok-style</option>
          <option value="youtube_instream">YouTube In-Stream</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div className="field">
        <label>Video Ad</label>
        <input type="file" accept="video/*" onChange={handleVideoUpload} required={!value.upload_id} />
        {uploading && <p style={{ marginTop: "8px", fontSize: "0.9em", color: "#666" }}>Uploading video...</p>}
        {previewUrl && !uploading && (
          <div style={{ marginTop: "8px" }}>
            <video 
              src={previewUrl} 
              controls
              style={{ maxWidth: "100%", maxHeight: "200px", border: "1px solid #ddd", borderRadius: "4px" }} 
            />
            {value.upload_id && <p style={{ fontSize: "0.8em", color: "#666", marginTop: "4px" }}>Upload ID: {value.upload_id}</p>}
          </div>
        )}
      </div>
    </div>
  );
}

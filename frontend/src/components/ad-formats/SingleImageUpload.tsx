import { ChangeEvent } from "react";

interface Props {
  value: { image: string; image_media_type: string; ad_platform: string };
  onChange: (value: any) => void;
}

export default function SingleImageUpload({ value, onChange }: Props) {
  function handleImageUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result as string;
      if (dataUrl) {
        const [prefix, base64] = dataUrl.split(",");
        const mediaType = prefix.split(":")[1].split(";")[0];
        onChange({ ...value, image: base64, image_media_type: mediaType });
      }
    };
    reader.readAsDataURL(file);
  }

  return (
    <div className="field-group">
      <div className="field">
        <label>Platform (e.g. Instagram, LinkedIn)</label>
        <select
          value={value.ad_platform || ""}
          onChange={(e) => onChange({ ...value, ad_platform: e.target.value })}
          required
        >
          <option value="" disabled>Select platform...</option>
          <option value="instagram_feed">Instagram Feed</option>
          <option value="instagram_story">Instagram Story</option>
          <option value="facebook_feed">Facebook Feed</option>
          <option value="youtube_thumbnail">YouTube Thumbnail</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div className="field">
        <label>Ad Image</label>
        <input type="file" accept="image/*" onChange={handleImageUpload} required={!value.image} />
        {value.image && (
          <div style={{ marginTop: "8px" }}>
            <img 
              src={`data:${value.image_media_type || 'image/png'};base64,${value.image}`} 
              alt="Ad preview" 
              style={{ maxWidth: "100%", maxHeight: "150px", objectFit: "contain", border: "1px solid #ddd", borderRadius: "4px" }} 
            />
          </div>
        )}
      </div>
    </div>
  );
}

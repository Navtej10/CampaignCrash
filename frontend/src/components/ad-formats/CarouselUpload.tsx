import { ChangeEvent, useEffect } from "react";

interface Props {
  value: { images: string[]; image_media_type: string; ad_platform: string };
  onChange: (value: any) => void;
}

export default function CarouselUpload({ value, onChange }: Props) {
  const images = value.images || ["", ""];

  useEffect(() => {
    if (!value.images || value.images.length < 2) {
      onChange({ ...value, images: ["", ""] });
    }
  }, []);

  function handleImageUpload(idx: number, e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result as string;
      if (dataUrl) {
        const [prefix, base64] = dataUrl.split(",");
        const mediaType = prefix.split(":")[1].split(";")[0];
        
        const newImages = [...images];
        newImages[idx] = base64;
        onChange({ ...value, images: newImages, image_media_type: mediaType });
      }
    };
    reader.readAsDataURL(file);
  }

  function addSlot() {
    if (images.length < 10) onChange({ ...value, images: [...images, ""] });
  }

  function removeSlot(idx: number) {
    if (images.length > 2) {
      const newImages = images.filter((_, i) => i !== idx);
      onChange({ ...value, images: newImages });
    }
  }

  return (
    <div className="field-group">
      <div className="field">
        <label>Platform</label>
        <input
          type="text"
          value={value.ad_platform || ""}
          onChange={(e) => onChange({ ...value, ad_platform: e.target.value })}
          required
        />
      </div>
      
      <div className="field">
        <label>Carousel Images (2-10 cards)</label>
        {images.map((img, idx) => (
          <div key={idx} style={{ marginBottom: "16px", padding: "8px", border: "1px solid #eee", borderRadius: "4px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
              <span>Card {idx + 1}</span>
              {images.length > 2 && (
                <button type="button" onClick={() => removeSlot(idx)} style={{ fontSize: "0.8rem", color: "red", background: "none", border: "none", cursor: "pointer" }}>Remove</button>
              )}
            </div>
            <input type="file" accept="image/*" onChange={(e) => handleImageUpload(idx, e)} required={!img} />
            {img && (
              <div style={{ marginTop: "8px" }}>
                <img 
                  src={`data:${value.image_media_type || 'image/png'};base64,${img}`} 
                  alt={`Card ${idx + 1}`} 
                  style={{ maxWidth: "100%", maxHeight: "150px", objectFit: "contain", border: "1px solid #ddd", borderRadius: "4px" }} 
                />
              </div>
            )}
          </div>
        ))}
        
        {images.length < 10 && (
          <button type="button" onClick={addSlot} style={{ fontSize: "0.8rem", padding: "4px 8px" }}>+ Add Card</button>
        )}
      </div>
    </div>
  );
}

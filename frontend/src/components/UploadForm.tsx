import { ChangeEvent, FormEvent, useState } from "react";
import type { CampaignInput, AdFormat } from "../types";
import TextCopyFields from "./ad-formats/TextCopyFields";
import CtaBannerFields from "./ad-formats/CtaBannerFields";
import SingleImageUpload from "./ad-formats/SingleImageUpload";
import CarouselUpload from "./ad-formats/CarouselUpload";
import VideoUpload from "./ad-formats/VideoUpload";
import SearchAdFields from "./ad-formats/SearchAdFields";
import EmailFields from "./ad-formats/EmailFields";
import AudioScriptField from "./ad-formats/AudioScriptField";

interface Props {
  onSubmit: (input: CampaignInput) => void;
  isRunning: boolean;
}

const emptyForm: CampaignInput = {
  ad_format: "text_copy",
  advertisement_content: {},
  landing_page: "",
  target_audience: "",
  campaign_objective: "",
};

export default function UploadForm({ onSubmit, isRunning }: Props) {
  const [form, setForm] = useState<CampaignInput>(emptyForm);
  const [inputType, setInputType] = useState<"text" | "image" | "skip">("text");

  function handleImageUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result as string;
      if (dataUrl) {
        const [prefix, base64] = dataUrl.split(",");
        const mediaType = prefix.split(":")[1].split(";")[0];
        
        setForm((prev) => ({
          ...prev,
          landing_page: undefined,
          landing_page_image: base64,
          landing_page_image_media_type: mediaType,
        }));
      }
    };
    reader.readAsDataURL(file);
  }

  function update<K extends keyof CampaignInput>(key: K, value: CampaignInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit(form);
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="ad_format">Advertisement Format</label>
        <select
          id="ad_format"
          value={form.ad_format}
          onChange={(e) => {
            setForm((prev) => ({
              ...prev,
              ad_format: e.target.value as AdFormat,
              advertisement_content: {} // Reset content on format change
            }));
          }}
          style={{ width: "100%", padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
        >
          <option value="text_copy">Text/Copy Ad</option>
          <option value="cta_banner">CTA Banner</option>
          <option value="single_image">Single Image</option>
          <option value="carousel">Carousel</option>
          <option value="video">Video</option>
          <option value="search_ad">Search Ad</option>
          <option value="email">Email</option>
          <option value="audio">Audio Script</option>
        </select>
      </div>

      <div className="format-fields" style={{ padding: "16px", background: "#f9f9f9", borderRadius: "4px", marginBottom: "16px" }}>
        {form.ad_format === "text_copy" && <TextCopyFields value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />}
        {form.ad_format === "cta_banner" && <CtaBannerFields value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />}
        {form.ad_format === "single_image" && <SingleImageUpload value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />}
        {form.ad_format === "carousel" && <CarouselUpload value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />}
        {form.ad_format === "video" && <VideoUpload value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />}
        {form.ad_format === "search_ad" && <SearchAdFields value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />}
        {form.ad_format === "email" && <EmailFields value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />}
        {form.ad_format === "audio" && <AudioScriptField value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />}
      </div>

      <div className="field">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <label htmlFor="landing_page" style={{ margin: 0 }}>Landing page (Optional)</label>
          <div style={{ display: "flex", gap: "8px" }}>
            <button 
              type="button"
              onClick={() => { setInputType("text"); update("landing_page_image", undefined); update("landing_page_image_media_type", undefined); }}
              style={{ fontSize: "0.85rem", padding: "4px 8px", background: inputType === "text" ? "#eee" : "transparent", border: "1px solid #ccc", borderRadius: "4px", cursor: "pointer", color: "black" }}
            >Paste text</button>
            <button 
              type="button"
              onClick={() => { setInputType("image"); update("landing_page", undefined); }}
              style={{ fontSize: "0.85rem", padding: "4px 8px", background: inputType === "image" ? "#eee" : "transparent", border: "1px solid #ccc", borderRadius: "4px", cursor: "pointer", color: "black" }}
            >Upload screenshot</button>
            <button 
              type="button"
              onClick={() => { setInputType("skip"); update("landing_page", undefined); update("landing_page_image", undefined); update("landing_page_image_media_type", undefined); }}
              style={{ fontSize: "0.85rem", padding: "4px 8px", background: inputType === "skip" ? "#eee" : "transparent", border: "1px solid #ccc", borderRadius: "4px", cursor: "pointer", color: "black" }}
            >Skip</button>
          </div>
        </div>
        
        {inputType === "text" && (
          <textarea
            id="landing_page"
            rows={6}
            placeholder="Paste the landing page copy the ad sends people to..."
            value={form.landing_page || ""}
            onChange={(e) => update("landing_page", e.target.value)}
            required={inputType === "text"}
          />
        )}
        {inputType === "image" && (
          <div>
            <input 
              type="file" 
              accept="image/*" 
              onChange={handleImageUpload} 
              required={inputType === "image" && !form.landing_page_image}
            />
            {form.landing_page_image && (
              <div style={{ marginTop: "8px" }}>
                <img 
                  src={`data:${form.landing_page_image_media_type};base64,${form.landing_page_image}`} 
                  alt="Landing page preview" 
                  style={{ maxWidth: "100%", maxHeight: "150px", objectFit: "contain", border: "1px solid #ddd", borderRadius: "4px" }} 
                />
              </div>
            )}
          </div>
        )}
      </div>

      <div className="field">
        <label htmlFor="target_audience">Target audience</label>
        <input
          id="target_audience"
          type="text"
          placeholder="Who you think this is for"
          value={form.target_audience}
          onChange={(e) => update("target_audience", e.target.value)}
          required
        />
      </div>

      <div className="field">
        <label htmlFor="campaign_objective">Campaign objective</label>
        <input
          id="campaign_objective"
          type="text"
          placeholder="What this campaign needs to do"
          value={form.campaign_objective}
          onChange={(e) => update("campaign_objective", e.target.value)}
          required
        />
      </div>

      <button type="submit" className="run-button" disabled={isRunning}>
        {isRunning ? "Running the crash test…" : "Run crash test"}
      </button>
    </form>
  );
}

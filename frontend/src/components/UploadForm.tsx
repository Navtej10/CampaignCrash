import { ChangeEvent, FormEvent, useState } from "react";
import type { AdFormat, CampaignInput, Platform } from "../types";
import TextCopyFields from "./ad-formats/TextCopyFields";
import CtaBannerFields from "./ad-formats/CtaBannerFields";
import SingleImageUpload from "./ad-formats/SingleImageUpload";
import CarouselUpload from "./ad-formats/CarouselUpload";
import VideoUpload from "./ad-formats/VideoUpload";
import SearchAdFields from "./ad-formats/SearchAdFields";
import EmailFields from "./ad-formats/EmailFields";
import AudioScriptField from "./ad-formats/AudioScriptField";

const PLATFORM_LABELS: Record<Platform, string> = {
  instagram_feed: "Instagram Feed",
  instagram_story: "Instagram Story",
  facebook_feed: "Facebook Feed",
  youtube: "YouTube",
  google_search: "Google Search",
  email_inbox: "Email Inbox",
  linkedin_feed: "LinkedIn Feed",
  other: "Other",
};

export const COMPATIBLE_PLATFORMS: Record<AdFormat, Platform[]> = {
  text_copy: ["linkedin_feed", "facebook_feed", "instagram_feed", "other"],
  cta_banner: ["other", "linkedin_feed", "facebook_feed"],
  single_image: ["instagram_feed", "instagram_story", "facebook_feed", "linkedin_feed", "youtube", "other"],
  carousel: ["instagram_feed", "facebook_feed", "linkedin_feed", "other"],
  video: ["youtube", "instagram_story", "instagram_feed", "facebook_feed", "linkedin_feed", "other"],
  search_ad: ["google_search", "other"],
  email: ["email_inbox", "other"],
  audio: ["youtube", "other"],
};

interface Props {
  form: CampaignInput;
  onChange: (form: CampaignInput) => void;
  onSubmit: (input: CampaignInput) => void;
  onRetest?: () => void;
  canRetest?: boolean;
  isRunning: boolean;
  isRetesting?: boolean;
}

export default function UploadForm({
  form,
  onChange,
  onSubmit,
  onRetest,
  canRetest,
  isRunning,
  isRetesting,
}: Props) {
  const [inputType, setInputType] = useState<"text" | "image" | "skip">("text");

  const compatiblePlatforms = COMPATIBLE_PLATFORMS[form.ad_format] ?? ["other"];

  function handleImageUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result as string;
      if (dataUrl) {
        const [prefix, base64] = dataUrl.split(",");
        const mediaType = prefix.split(":")[1].split(";")[0];

        onChange({
          ...form,
          landing_page: undefined,
          landing_page_image: base64,
          landing_page_image_media_type: mediaType,
        });
      }
    };
    reader.readAsDataURL(file);
  }

  function update<K extends keyof CampaignInput>(key: K, value: CampaignInput[K]) {
    onChange({ ...form, [key]: value });
  }

  function handleFormatChange(newFormat: AdFormat) {
    const allowed = COMPATIBLE_PLATFORMS[newFormat] ?? ["other"];
    const nextPlatform = allowed.includes(form.platform) ? form.platform : allowed[0];
    onChange({
      ...form,
      ad_format: newFormat,
      platform: nextPlatform,
      advertisement_content: {},
    });
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit(form);
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <div className="format-platform-row">
        <div className="field">
          <label htmlFor="ad_format">Format</label>
          <select
            id="ad_format"
            value={form.ad_format}
            onChange={(e) => handleFormatChange(e.target.value as AdFormat)}
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

        <div className="field">
          <label htmlFor="platform">Platform</label>
          <select
            id="platform"
            value={compatiblePlatforms.includes(form.platform) ? form.platform : compatiblePlatforms[0]}
            onChange={(e) => update("platform", e.target.value as Platform)}
          >
            {compatiblePlatforms.map((p) => (
              <option key={p} value={p}>
                {PLATFORM_LABELS[p]}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="format-fields">
        {form.ad_format === "text_copy" && (
          <TextCopyFields value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />
        )}
        {form.ad_format === "cta_banner" && (
          <CtaBannerFields value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />
        )}
        {form.ad_format === "single_image" && (
          <SingleImageUpload value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />
        )}
        {form.ad_format === "carousel" && (
          <CarouselUpload value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />
        )}
        {form.ad_format === "video" && (
          <VideoUpload value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />
        )}
        {form.ad_format === "search_ad" && (
          <SearchAdFields value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />
        )}
        {form.ad_format === "email" && (
          <EmailFields value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />
        )}
        {form.ad_format === "audio" && (
          <AudioScriptField value={form.advertisement_content} onChange={(v) => update("advertisement_content", v)} />
        )}
      </div>

      <div className="field">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <label htmlFor="landing_page" style={{ margin: 0 }}>Landing page (Optional)</label>
          <div style={{ display: "flex", gap: "6px" }}>
            <button
              type="button"
              className={`lp-toggle ${inputType === "text" ? "lp-toggle--active" : ""}`}
              onClick={() => {
                setInputType("text");
                onChange({ ...form, landing_page_image: undefined, landing_page_image_media_type: undefined });
              }}
            >
              Paste text
            </button>
            <button
              type="button"
              className={`lp-toggle ${inputType === "image" ? "lp-toggle--active" : ""}`}
              onClick={() => {
                setInputType("image");
                onChange({ ...form, landing_page: undefined });
              }}
            >
              Screenshot
            </button>
            <button
              type="button"
              className={`lp-toggle ${inputType === "skip" ? "lp-toggle--active" : ""}`}
              onClick={() => {
                setInputType("skip");
                onChange({
                  ...form,
                  landing_page: undefined,
                  landing_page_image: undefined,
                  landing_page_image_media_type: undefined,
                });
              }}
            >
              Skip
            </button>
          </div>
        </div>

        {inputType === "text" && (
          <textarea
            id="landing_page"
            rows={5}
            placeholder="Paste the landing page copy the ad sends people to..."
            value={form.landing_page || ""}
            onChange={(e) => update("landing_page", e.target.value)}
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
                  style={{ maxWidth: "100%", maxHeight: "150px", objectFit: "contain", border: "1px solid #444", borderRadius: "4px" }}
                />
              </div>
            )}
          </div>
        )}
      </div>

      <div className="field">
        <label htmlFor="target_audience">Target audience (Optional)</label>
        <input
          id="target_audience"
          type="text"
          placeholder="Who you think this is for (defaults if blank)"
          value={form.target_audience}
          onChange={(e) => update("target_audience", e.target.value)}
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

      <div className="form-actions">
        <button type="submit" className="run-button" disabled={isRunning || isRetesting}>
          {isRunning ? "Running the crash test…" : "Run crash test"}
        </button>
        {canRetest && onRetest && (
          <button
            type="button"
            className="retest-button"
            onClick={onRetest}
            disabled={isRunning || isRetesting}
          >
            {isRetesting ? "Re-testing…" : "Re-test"}
          </button>
        )}
      </div>
    </form>
  );
}

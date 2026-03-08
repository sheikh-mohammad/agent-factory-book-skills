---
name: video-generator
description: AI video production workflow using Remotion. Use when creating videos, short films, commercials, or motion graphics. Triggers on requests to make promotional videos, product demos, social media videos, animated explainers, or any programmatic video content. Produces polished motion graphics, not slideshows.
---

# Video Generator (Remotion)

Create professional motion graphics videos programmatically with React and Remotion.

## Default Workflow (ALWAYS follow this)

1. **Scrape brand data** (if featuring a product) using Firecrawl
2. **Create the project** in `output/<project-name>/`
3. **Build all scenes** with proper motion graphics
4. **Install dependencies** with `npm install`
5. **Fix package.json scripts** to use `npx remotion` (not `bun`):
   ```json
   "scripts": {
     "dev": "npx remotion studio",
     "build": "npx remotion bundle"
   }
   ```
6. **Start Remotion Studio** as a background process:
   ```bash
   cd output/<project-name> && npm run dev
   ```
   Wait for "Server ready" on port 3000.
7. **Expose via Cloudflare tunnel** so user can access it:
   ```bash
   bash skills/cloudflare-tunnel/scripts/tunnel.sh start 3000
   ```
8. **Send the user the public URL** (e.g. `https://xxx.trycloudflare.com`)

The user will preview in their browser, request changes, and you edit the source files. Remotion hot-reloads automatically.

### Rendering (only when user explicitly asks to export):

```bash
cd output/<project-name>
npx remotion render CompositionName out/video.mp4
```

## Quick Start

**IMPORTANT:** `create-video@latest` has an interactive CLI that blocks in non-TTY environments. Use manual scaffolding instead:

```bash
mkdir -p output/my-video/src/scenes output/my-video/public/audio output/my-video/public/images
cd output/my-video

# Create package.json manually
cat > package.json << 'EOF'
{
  "name": "my-video",
  "scripts": {
    "dev": "npx remotion studio",
    "build": "npx remotion bundle",
    "render": "npx remotion render"
  },
  "dependencies": {
    "@remotion/cli": "4.0.293",
    "react": "^19",
    "react-dom": "^19",
    "remotion": "4.0.293",
    "lucide-react": "^0.400"
  },
  "devDependencies": {
    "@types/react": "^19",
    "typescript": "^5"
  }
}
EOF

# Create tsconfig.json, remotion.config.ts, src/index.ts, src/Root.tsx
# (see File Structure section below for templates)

npm install

# Start dev server
npm run dev

# Expose publicly
bash skills/cloudflare-tunnel/scripts/tunnel.sh start 3000
```

## Fetching Brand Data with Firecrawl

**MANDATORY:** When a video mentions or features any product/company, use Firecrawl to scrape the product's website for brand data, colors, screenshots, and copy BEFORE designing the video. This ensures visual accuracy and brand consistency.

API Key: Set `FIRECRAWL_API_KEY` in `.env` (see TOOLS.md).

### Usage

```bash
bash scripts/firecrawl.sh "https://example.com"
```

Returns structured brand data: brandName, tagline, headline, description, features, logoUrl, faviconUrl, primaryColors, ctaText, socialLinks, plus screenshot URL and OG image URL.

### Download Assets After Scraping

```bash
mkdir -p public/images/brand
curl -s "https://example.com/favicon.svg" -o public/images/brand/logo.svg
curl -s "${OG_IMAGE_URL}" -o public/images/brand/og-image.png
curl -sL "${SCREENSHOT_URL}" -o public/images/brand/screenshot.png
```

## Core Architecture

### Scene Management

Use scene-based architecture with proper transitions:

```tsx
const SCENE_DURATIONS: Record<string, number> = {
  intro: 3000, // 3s hook
  problem: 4000, // 4s dramatic
  solution: 3500, // 3.5s reveal
  features: 5000, // 5s showcase
  cta: 3000, // 3s close
};
```

### Video Structure Pattern

```tsx
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Img,
  staticFile,
  Audio,
} from "remotion";

export const MyVideo = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  return (
    <AbsoluteFill>
      {/* Background music */}
      <Audio src={staticFile("audio/bg-music.mp3")} volume={0.35} />

      {/* Persistent background layer - OUTSIDE sequences */}
      <AnimatedBackground frame={frame} />

      {/* Scene sequences */}
      <Sequence from={0} durationInFrames={90}>
        <IntroScene />
      </Sequence>
      <Sequence from={90} durationInFrames={120}>
        <FeatureScene />
      </Sequence>
    </AbsoluteFill>
  );
};
```

## Motion Graphics Principles

### AVOID (Slideshow patterns)

- Fading to black between scenes
- Centered text on solid backgrounds
- Same transition for everything
- Linear/robotic animations
- Static screens
- `slideLeft`, `slideRight`, `crossDissolve`, `fadeBlur` presets
- Emoji icons — NEVER use emoji, always use Lucide React icons

### PURSUE (Motion graphics)

- Overlapping transitions (next starts BEFORE current ends)
- Layered compositions (background/midground/foreground)
- Spring physics for organic motion
- Varied timing (2-5s scenes, mixed rhythms)
- Continuous visual elements across scenes
- Custom transitions with clipPath, 3D transforms, morphs
- Lucide React for ALL icons (`npm install lucide-react`) — never emoji

## Transition Techniques

1. **Morph/Scale** - Element scales up to fill screen, becomes next scene's background
2. **Wipe** - Colored shape sweeps across, revealing next scene
3. **Zoom-through** - Camera pushes into element, emerges into new scene
4. **Clip-path reveal** - Circle/polygon grows from point to reveal
5. **Persistent anchor** - One element stays while surroundings change
6. **Directional flow** - Scene 1 exits right, Scene 2 enters from right
7. **Split/unfold** - Screen divides, panels slide apart
8. **Perspective flip** - Scene rotates on Y-axis in 3D

## Animation Timing Reference

```tsx
// Timing values (in seconds)
const timing = {
  micro: 0.1 - 0.2, // Small shifts, subtle feedback
  snappy: 0.2 - 0.4, // Element entrances, position changes
  standard: 0.5 - 0.8, // Scene transitions, major reveals
  dramatic: 1.0 - 1.5, // Hero moments, cinematic reveals
};

// Spring configs
const springs = {
  snappy: { stiffness: 400, damping: 30 },
  bouncy: { stiffness: 300, damping: 15 },
  smooth: { stiffness: 120, damping: 25 },
};
```

## Visual Style Guidelines

### Typography

- One display font + one body font max
- Massive headlines, tight tracking
- Mix weights for hierarchy
- Keep text SHORT (viewers can't pause)

### Colors

- **Use brand colors from Firecrawl scrape** as the primary palette — match the product's actual look
- **Avoid purple/indigo gradients** unless the brand uses them or the user explicitly requests them
- Simple, clean backgrounds are generally best — a single dark tone or subtle gradient beats layered textures
- Intentional accent colors pulled from the brand

### Layout

- Use asymmetric layouts, off-center type
- Edge-aligned elements create visual tension
- Generous whitespace as design element
- Use depth sparingly — a subtle backdrop blur or single gradient, not stacked textures

## Remotion Essentials

### Interpolation

```tsx
const opacity = interpolate(frame, [0, 30], [0, 1], {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
});

const scale = spring({
  frame,
  fps,
  from: 0.8,
  to: 1,
  durationInFrames: 30,
  config: { damping: 12 },
});
```

### Sequences with Overlap

```tsx
<Sequence from={0} durationInFrames={100}>
  <Scene1 />
</Sequence>
<Sequence from={80} durationInFrames={100}>
  <Scene2 />
</Sequence>
```

### Cross-Scene Continuity

Place persistent elements OUTSIDE Sequence blocks:

```tsx
const PersistentShape = ({ currentScene }: { currentScene: number }) => {
  const positions = {
    0: { x: 100, y: 100, scale: 1, opacity: 0.3 },
    1: { x: 800, y: 200, scale: 2, opacity: 0.5 },
    2: { x: 400, y: 600, scale: 0.5, opacity: 1 },
  };

  return (
    <motion.div
      animate={positions[currentScene]}
      transition={{ duration: 0.8, ease: "easeInOut" }}
      className="absolute w-32 h-32 rounded-full bg-gradient-to-r from-coral to-orange"
    />
  );
};
```

## Quality Tests

Before delivering, verify:

- **Mute test:** Story follows visually without sound?
- **Squint test:** Hierarchy visible when squinting?
- **Timing test:** Motion feels natural, not robotic?
- **Consistency test:** Similar elements behave similarly?
- **Slideshow test:** Does NOT look like PowerPoint?
- **Loop test:** Video loops smoothly back to start?

## Implementation Steps

1. **Firecrawl brand scrape** — If featuring a product, scrape its site first
2. **Director's treatment** — Write vibe, camera style, emotional arc
3. **Visual direction** — Colors, fonts, brand feel, animation style
4. **Scene breakdown** — List every scene with description, duration, text, transitions
5. **Define durations** — Vary pacing (2-3s punchy, 4-5s dramatic)
6. **Create styles.ts** — Unified type scale, colors, fonts (prevents sizing inconsistency)
7. **Build persistent layer** — Animated background outside scenes
8. **Build scenes** — Each with enter/exit animations, 3-5 timed moments
9. **Start Remotion Studio** — `npm run dev`, expose via tunnel, send URL
10. **Iterate with user** — Edit source, hot-reload, repeat
11. **Generate voiceover** — Gemini TTS (see AI Voiceover section)
12. **Add transcription** — Timed captions synced to audio
13. **Sync audio-visual** — Match scene timings to voiceover duration
14. **Render** — Only when user says to export: `npx remotion render CompositionName out/video.mp4`

## File Structure

```
my-video/
├── src/
│   ├── Root.tsx              # Composition definitions (fps, resolution, duration)
│   ├── index.ts              # Entry point (export Root)
│   ├── styles.ts             # Shared colors, fonts, type scale (CRITICAL)
│   ├── MyVideo.tsx           # Main composition (background + sequences + overlay)
│   ├── Transcription.tsx     # Timed caption overlay (if voiceover exists)
│   └── scenes/               # One file per scene
│       ├── TitleScene.tsx
│       ├── HookScene.tsx
│       ├── FeatureScene.tsx
│       └── CTAScene.tsx
├── public/
│   ├── images/
│   │   └── brand/            # Firecrawl-scraped assets
│   └── audio/
│       └── voiceover.wav     # Gemini TTS output
├── out/                      # Rendered output (gitignored)
│   └── video.mp4
├── remotion.config.ts
└── package.json
```

## Common Components

See `references/components.md` for reusable:

- Animated backgrounds
- Terminal windows
- Feature cards
- Stats displays
- CTA buttons
- Text reveal animations

## AI Voiceover with Gemini TTS

Generate human-quality voiceovers using Google's Gemini TTS models.

### Available TTS Models

| Model                          | Quality | Speed  | Use Case          |
| ------------------------------ | ------- | ------ | ----------------- |
| `gemini-2.5-flash-preview-tts` | Good    | Fast   | Drafts, iteration |
| `gemini-2.5-pro-preview-tts`   | Best    | Slower | Final renders     |

**Note:** Standard Gemini models (`gemini-2.0-flash`, etc.) do NOT support audio output. You must use the dedicated `-tts` models.

### Voice Options

Orus, Kore, Puck, Charon, Fenrir, Leda, Aoede, Zephyr — each with distinct personality.
Best for professional narration: **Orus** (warm, authoritative) or **Kore** (clear, friendly).

### Generation Script

```bash
# Set API key
export GEMINI_API_KEY="your-key"

# Generate voiceover (returns raw PCM audio)
curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-tts:generateContent?key=$GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{"parts": [{"text": "Your narration script here..."}]}],
    "generationConfig": {
      "response_modalities": ["AUDIO"],
      "speech_config": {
        "voiceConfig": {
          "prebuiltVoiceConfig": { "voiceName": "Orus" }
        }
      }
    }
  }' | python3 -c "
import json, sys, base64
r = json.load(sys.stdin)
audio = r['candidates'][0]['content']['parts'][0]['inlineData']['data']
sys.stdout.buffer.write(base64.b64decode(audio))
" > voiceover_raw.pcm

# Convert PCM to WAV (Gemini outputs s16le, 24kHz, mono)
ffmpeg -f s16le -ar 24000 -ac 1 -i voiceover_raw.pcm public/audio/voiceover.wav
rm voiceover_raw.pcm

# Check duration
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 public/audio/voiceover.wav
```

### Audio-Visual Sync

Add a small delay so visuals appear before the voice starts:

```tsx
const AUDIO_OFFSET = 15; // 0.5s at 30fps

// In the main composition:
<Sequence from={AUDIO_OFFSET}>
  <Audio src={staticFile("audio/voiceover.wav")} volume={0.9} />
</Sequence>;
```

Calculate total frames from audio duration: `totalFrames = Math.ceil(duration * fps) + AUDIO_OFFSET`

## Transcription Overlay

Add timed captions synced to voiceover:

```tsx
const LINES: { start: number; end: number; text: string }[] = [
  { start: 20, end: 140, text: "First caption line." },
  { start: 155, end: 230, text: "Second caption line." },
  // ...
];

export const Transcription: React.FC = () => {
  const frame = useCurrentFrame();
  const activeLine = LINES.find((l) => frame >= l.start && frame <= l.end);
  if (!activeLine) return null;

  // CRITICAL: Adaptive fade prevents interpolation errors on short captions
  const dur = activeLine.end - activeLine.start;
  const fade = Math.min(10, Math.floor(dur / 3));

  const opacity = interpolate(
    frame,
    [
      activeLine.start,
      activeLine.start + fade,
      activeLine.end - fade,
      activeLine.end,
    ],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <div
      style={{
        position: "absolute",
        bottom: 56,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        opacity,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          padding: "14px 36px",
          borderRadius: 14,
          background: "rgba(0,0,0,0.6)",
          backdropFilter: "blur(16px)",
        }}
      >
        <span style={{ fontSize: 26, fontWeight: 500, color: "#fff" }}>
          {activeLine.text}
        </span>
      </div>
    </div>
  );
};
```

**Interpolation safety:** For short captions (< 20 frames), `start + 10 > end - 10` breaks Remotion's strictly-monotonic requirement. The adaptive `Math.min(10, Math.floor(dur / 3))` formula prevents this.

## Unified Type Scale

**ALWAYS define a shared type scale in `styles.ts`** — never set font sizes inline per scene. This prevents the #1 visual issue: inconsistent text sizing across scenes.

```tsx
// styles.ts
export const colors = {
  bg: "#0a0a0f",
  textPrimary: "rgba(255,255,255,0.95)",
  textSecondary: "rgba(255,255,255,0.55)",
  textDim: "rgba(255,255,255,0.3)",
  // Brand accent colors from Firecrawl scrape
};

export const fonts = {
  sans: "Inter, system-ui, sans-serif",
  mono: "'JetBrains Mono', monospace",
};

export const type = {
  hero: {
    fontSize: 96,
    fontWeight: 700,
    letterSpacing: "-0.04em",
    lineHeight: 1.05,
  },
  h1: {
    fontSize: 68,
    fontWeight: 700,
    letterSpacing: "-0.035em",
    lineHeight: 1.1,
  },
  h2: {
    fontSize: 48,
    fontWeight: 600,
    letterSpacing: "-0.025em",
    lineHeight: 1.2,
  },
  body: {
    fontSize: 28,
    fontWeight: 400,
    letterSpacing: "-0.01em",
    lineHeight: 1.5,
  },
  bodyLg: {
    fontSize: 34,
    fontWeight: 400,
    letterSpacing: "-0.015em",
    lineHeight: 1.4,
  },
  stat: {
    fontSize: 86,
    fontWeight: 800,
    letterSpacing: "-0.04em",
    lineHeight: 1,
  },
  label: {
    fontSize: 18,
    fontWeight: 600,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
  },
  mono: {
    fontSize: 22,
    fontWeight: 500,
    fontFamily: "'JetBrains Mono', monospace",
  },
};
```

Every scene imports `{ colors, fonts, type }` from `../styles` and uses the shared tokens.

## Tunnel Management

```bash
# Start tunnel (exposes port 3000 publicly)
bash skills/cloudflare-tunnel/scripts/tunnel.sh start 3000

# Check status
bash skills/cloudflare-tunnel/scripts/tunnel.sh status 3000

# List all tunnels
bash skills/cloudflare-tunnel/scripts/tunnel.sh list

# Stop tunnel
bash skills/cloudflare-tunnel/scripts/tunnel.sh stop 3000
```

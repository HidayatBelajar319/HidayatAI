# Ultron Jarvis Orb UI

An interactive holographic orb interface built with **Next.js**, **Three.js**, and **MediaPipe** hand tracking.

## Getting started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Controls

### Mouse / touch

| Input | Action |
| --- | --- |
| Drag | Spin the orb |
| Scroll / pinch | Zoom in & out |

### Hand gestures (webcam)

Click **GESTURES OFF** (or press `G`) and allow camera access, then:

| Gesture | Action |
| --- | --- |
| Pinch (thumb + index) one hand and move it | Spin the orb |
| Pinch with **both** hands, spread apart / bring together | Zoom in / out |

### Keyboard

| Key | Action |
| --- | --- |
| `G` | Toggle hand gestures |
| `R` | Reset the view |
| `+` / `-` | Zoom in / out |

## How it works

- **`lib/orbScene.ts`** builds the Three.js scene, visual effects, and camera controls.
- **`lib/handTracker.ts`** runs MediaPipe HandLandmarker on the webcam feed.
- **`components/BrahmaOrb.tsx`** connects the scene, the tracker, and user input.

## License

MIT

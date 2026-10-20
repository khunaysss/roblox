---
name: Cage Champions Native UI v02
description: Native Roblox broadcast UI for selection, training and combat.
colors:
  background: "#15171C"
  card: "#1E2026"
  border: "#3A3D46"
  text: "#F5F5F7"
  secondary-text: "#A6A9B4"
  red: "#E0243A"
  blue: "#2F6FE0"
  stamina: "#F2C94C"
  gold: "#E8B65A"
  green: "#2EB86B"
  locked: "#6B6E7A"
typography:
  title:
    fontFamily: GothamBlack
  emphasis:
    fontFamily: GothamBold
  body:
    fontFamily: Gotham
    fontSize: "17px"
rounded:
  surface: "4px"
spacing:
  grid: "8px"
  inset: "16px"
  panel: "24px"
components:
  button-primary:
    backgroundColor: "{colors.red}"
    textColor: "{colors.text}"
    rounded: "{rounded.surface}"
    height: "58px"
  button-secondary:
    backgroundColor: "{colors.card}"
    textColor: "{colors.text}"
    rounded: "{rounded.surface}"
    height: "58px"
  button-navigation:
    backgroundColor: "{colors.card}"
    textColor: "{colors.text}"
    rounded: "{rounded.surface}"
    height: "82px"
  panel:
    backgroundColor: "{colors.card}"
    textColor: "{colors.text}"
    rounded: "{rounded.surface}"
---

# Design System: Cage Champions Native UI v02

## Overview

**Creative North Star: "Clear Fight Broadcast"**

This name describes the established code thesis, not a new identity proposal: clear televised fight status, with direct navigation, live numbers and a visible fighter. Anthracite surfaces, strong Gotham headings and functional color establish a compact sports interface. Player-facing game copy is English.

The UI uses Roblox text and native geometry. Frames, UIStroke, UICorner and empty-image compatibility containers build surfaces and icons; neither external image assets nor rasterized interface panels are part of this system. Live character staging and ViewportFrame previews are separate from the UI icon vocabulary.

**Key Characteristics:**

- Flat dark panels with thin borders and small corners.
- Red selection and action emphasis; red/blue combat sides.
- Gold progression and mastery, yellow stamina, green completion.
- Native line and rectangle icons paired with readable text.

This is a source-derived visual reference dated 2026-10-20. Authority: `roblox/CC_UI_v02.module.luau`, `CC_HUD_v02.client.luau`, `CC_MainMenu_v02.client.luau`, `CC_TrainerPanel_v02.client.luau`, `CC_VisualTheme_v02.client.luau`, `CC_LoadingScreen_v03.client.luau` and screenshots in `renders/launch_v02_20261020`. The final native implementation block in CC_UI overrides historical helper names such as sprite and chamfer. No PRODUCT.md was present at the project root; no additional product commitments are inferred.

Render evidence includes training-final.jpg, hud-intro.jpg and loading-final.jpg at (1914 × 753). Other captures in the folder document additional states, including fixtures named belt-award-fixture and knockdown-attribute-fixture. A screenshot or fixture is evidence of that displayed state only. This document is not an overall launch certification, gameplay validation or accessibility certification. No Studio access or tests were performed for this documentation pass.

## Colors

The normative palette is the YAML above. Luau assigns the same card value to bg1 and bg2, the same border value to line and bg3, and the same yellow value to stamina and warn.

### Primary

- **Fight Red:** primary actions, selected navigation, player health, active progress and focus outlines.

### Secondary

- **Opponent Blue:** the opposing fighter's health and side identity. Preserve the red/blue pairing where both fighters appear.

### Tertiary

- **Stamina Yellow:** stamina bars and warning semantics; retain a label or numerical value.
- **Championship Gold:** wordmark, XP, levels, mastery, signature focus and reward availability.
- **Completion Green:** completed trainer requirements and ready/completed status.

### Neutral

- **Arena Background:** page shading, loading surface and dark HUD cards.
- **Panel Anthracite:** standard cards and secondary controls.
- **Structural Gray:** borders, empty tracks and hover surfaces.
- **Near White:** primary text and icons.
- **Secondary Gray:** supporting text and measurements.
- **Locked Gray:** locked names, disabled support text and lock icon treatment.

**The Semantic Color Rule.** Use accent colors for actions, combat identity or meaningful status; keep long explanatory copy on neutral text colors. Existing selected option cards also use a darker red tint. That state treatment is not an additional primary accent.

## Typography

Roblox font enums supply the type system: GothamBlack for UI.F.title and UI.F.head, GothamBold for UI.F.bold, and Gotham for UI.F.body. Do not add web fonts or a speculative fallback stack.

Large, heavy headings communicate destination and fight state; regular Gotham carries explanations. Uppercase is common in navigation, actions and short state labels. Names and supporting sentences retain their appropriate case.

### Hierarchy

- **Display:** fight banner (48px); loading wordmark responds to viewport dimensions within (32–84px).
- **Page title:** main menu headers (34px), trainer name (28px), clock time (30px).
- **Navigation:** primary navigation title up to (26px), with supporting line (16px).
- **Action:** normal button title up to (21px); ghost button up to (16px). The shared helper scales titles within a (12px) minimum constraint.
- **Body:** shared label default (17px); explanations commonly (15–17px).
- **Compact status:** HUD values and labels (13–16px); tags (13px). Existing dense menu rows contain smaller text, so the code does not establish a universal minimum for all labels.

**The Live Text Rule.** Keep labels as live text. Preserve the shared helper's wrapping, truncation and size constraints according to context. Do not use TextScaled alone as evidence that a label fits every viewport. Loading uses explicit responsive TextSize calculation to avoid tiny initial measurements.

## Layout

The pinned rhythm is an (8px) grid with common (16px) insets and (24px) panel padding. This is a compositional rhythm, not a claim that every existing coordinate is a multiple of eight: observed controls include (10px), (12px) and (14px) gaps or insets.

Main menu and trainer canvas call UI.autoscale with a virtual height of (840px). The shared helper scales by the smaller of available height/design height and viewport width/(design height × 1.5), clamped to (0.5–1.6). When IgnoreGuiInset is false, available height accounts for Roblox GUI insets. This is continuous canvas scaling, not a breakpoint-driven responsive layout.

The menu places navigation and page content on the left, the staged fighter to the right and the profile independently at the upper right. The source content area is (660 × 470px); the home list is (650 × 460px), before canvas scaling. Left and bottom shading separate text from the live world. The fighter editor combines a category column, options panel and separate lower-right save/rotation controls.

The HUD uses two top-side fighter cards, each with proportional width (.34 of the screen minus 24px), a centered clock (184 × 96px), and (24px) edge offsets. The center remains open for combat. Control hints form up to two rows near the bottom; contextual position/submission information sits above them. These are source dimensions, not final screenshot pixel dimensions.

The trainer modal is centered (640 × 492px), with (24px) horizontal content insets, three requirement rows spaced by (64px), then condition text and an action footer.

**Viewport evidence:** (1914 × 753) was visually checked in the supplied capture set. (1280 × 720) and (1920 × 1080) have not been visually verified. The loading code's fallback size is not proof of a checked viewport. No mobile or controller layout certification follows from autoscaling or input support in source.

## Elevation & Depth

Standard UI depth comes from tonal layering, thin outlines, transparent world shading and modal dimming. There is no shared drop-shadow primitive. Panels use a border (1px); focus is expressed through an outline and/or changed fill. Avoid adding blur, frosted glass or gradients to standard controls.

The loading wordmark retains a text shadow and black outline as an existing title treatment. Its gold, arena and fill color gradients are disabled by the final code, leaving flat surfaces and fills. Transparency gradients on loading lines/sweep and menu shading remain functional native effects; they are not a general gradient style for cards.

## Shapes

Use small surface corners (4px) and native outlines. Historical chamfer/cut parameters do not produce clipped polygon corners in the current final helper: UI.chamfer now builds a rounded native surface. Circular icon pieces and the slider knob retain their purposeful round geometry.

Icons are monochrome native lines, rectangles and circles. The helper defaults to a (32 × 32px) icon; individual controls set sizes appropriate to their role. Preserve recognizable silhouettes and consistent stroke character. Use neither emoji nor uploaded icon sheets. Some unimplemented icon names use a neutral fallback marker; do not describe every named icon as a distinct finished illustration.

## Components

### Buttons and navigation

The shared button is flat, bordered and direct. Primary uses red, secondary uses the card surface; default height is (58px). Navigation defaults to (82px) with an icon, title, optional subtitle and next chevron. Ghost defaults to (44px) but still receives a native bordered surface; the name does not imply a borderless web-style link.

Hover and gamepad selection share state refresh. Active/selected uses red; neutral hover uses the structural gray surface. Disabled buttons reduce prominence and set Active and Selectable false. RewardReady switches to gold with dark title text. Preserve text and icon state cues as well as color. Do not invent a separate keyboard focus animation or pressed treatment that is absent from the helper.

### Panels, tags and dialogs

UI.panel uses a native card fill, thin border and shared corner radius. Screen-specific insets vary; use the established layout rhythm when adding content. Tags are compact text badges with horizontal padding (8px) and height (22px). Dialogs use a dim modal shield, centered panel and explicit actions. The trainer panel follows this pattern with condition text that explains why a quest action is unavailable.

### Progress, health and stamina

UI.bar is a clipped track with an independent native fill; default height is (8px), with screen-specific heights. The v02 HUD uses UI.bar directly: health (12px) and stamina (6px). Keep numerical HP/stamina labels alongside color. Do not assume the separate combatBar helper's damage-lag behavior is active in the v02 HUD.

Gold represents XP/signature progression; trainer requirements turn green when their target is reached. A full signature focus outline can pulse unless UI.reduceMotion is active. UI.reduceMotion checks CC_ReduceMotion or CC_ReduceFX.

### Option cards and swatches

Option cards keep native text plus live ViewportFrame previews. Selection adds a red outline and check; locked state adds a lock and dims the preview/name. Hover/focus exposes an outline. Shared swatches are (46 × 46px) after the native override and show a contrasting check when selected. Maintain the state semantics rather than substituting an uploaded selected-card image.

### Settings and input hints

Volume controls use a labeled percentage, native track/fill and a round knob. Display settings use text buttons with ON/OFF states. Shared hints switch between PC and gamepad keys based on last input; shared menu hints omit the key row on touch. HUD hint content is contextual and should be documented independently from that menu helper. No general text-field component is established by the scoped sources.

### Loading

The full-screen native loading surface centers the gold wordmark and English subtitle, with restrained vertical cage lines, red horizontal accents and a bottom progress track. Progress advances on actual milestones: surface built, character present, and HumanoidRootPart present. Preserve these milestones when restyling. Reduce-motion/effects settings remove positional entrance motion and the visible sweep; fade transitions remain. This is an observed implementation behavior, not a claim that every animation in the game follows the same reduced-motion policy.

### Existing UI theme adapter

CC_VisualTheme applies UI.theme to CC_ ScreenGuis and new descendants, excluding CC_LoadingScreen. Objects tagged CC_NativeUI bypass this adapter. It maps legacy type, dark fills, corners and some gradients into the shared world without replacing their actions. This compatibility pass does not prove every legacy screen is fully redesigned.

## Do's and Don'ts

### Do:

- **Do** reuse UI.C, UI.F and the native helper API for additional UI.
- **Do** keep player-facing strings English and state explanations specific.
- **Do** retain live values, selected checks, lock cues and disabled-action reasons.
- **Do** preserve the open combat center and distinguish player/opponent status.
- **Do** inspect new layouts at their actual target viewport before claiming fit.

### Don't:

- **Don't** replace native surfaces or icons with images, emoji or rasterized text.
- **Don't** turn historical sprite/chamfer names into an instruction to restore image skins or cut corners.
- **Don't** add decorative gradients, heavy shadows or extra font families to ordinary panels.
- **Don't** infer responsive coverage, complete input accessibility or release readiness from one capture size or a fixture.
- **Don't** treat this versioned document as authorization to overwrite DESIGN.md, PROJECT.md or existing design decisions.

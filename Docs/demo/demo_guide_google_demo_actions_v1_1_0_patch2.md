# Google Demo Actions v1.1.0 Patch 2 Demo Guide

Version: v1.1.0-patch2
Audience: Demo Presenter
Language: EN

## Best way to show the fix

1. Start in `simulation` mode.
2. Click `Prepare Demo Calendar`.
3. Explain that the system now shows a preview only.
4. Click `Generate Demo Appointments`.
5. Point at the success message and generated item count.
6. Click `Delete Demo Appointments`.
7. Point at the deleted item count.

## Good presenter line

`Now the buttons are not just labels. Each button calls a real backend action and the UI shows clearly what happened.`

## Good technical line

`The root cause was that Prepare was wired to Generate. In this patch the actions are split, mode-aware, and visible in the UI.`

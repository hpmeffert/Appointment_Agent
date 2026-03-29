# Demo Cockpit v1.0.5 Admin Guide

Version: v1.0.5
Audience: Admin
Language: EN

## What this release adds

This release turns the older single demo page into a more product-like cockpit.

Main additions:

- top navigation
- shared header on all pages
- dedicated `Dashboard` page
- dedicated `Monitoring` page
- dedicated `Settings` page
- language switch
- day/night theme switch

## Incident ZIP reference

The Incident Demo ZIP is now available and was reviewed as a real reference source.

The most important reused patterns are:

- router-based admin structure
- sticky admin header
- visible navigation state
- DE and EN language switching in the header
- icon-based theme toggle
- small visible version badge in the header
- separate dashboard and settings thinking instead of one long prototype page

## Main route

- `http://localhost:8080/ui/demo-monitoring/v1.0.5`

## Key parameters

- `language`
  Controls whether the cockpit labels use English or German.

- `theme`
  Controls whether the cockpit uses day mode or night mode.

- `dashboard_mode`
  Controls whether the dashboard is presentation-heavy, monitoring-heavy, or balanced.

- `scenario_id`
  Controls which demo story is shown in the dashboard.

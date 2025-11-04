<img src="./.github/assets/app-icon.png" alt="Voice Assistant App Icon" width="100" height="100">

# Web Voice Assistant

This is a starter template for [LiveKit Agents](https://docs.livekit.io/agents) that provides a simple voice interface using the [LiveKit JavaScript SDK](https://github.com/livekit/client-sdk-js). It supports [voice](https://docs.livekit.io/agents/start/voice-ai), [transcriptions](https://docs.livekit.io/agents/build/text/), and [virtual avatars](https://docs.livekit.io/agents/integrations/avatar).

This template is built with Next.js and is free for you to use or modify as you see fit.


## UI Library

Los componentes han sido migrados a [Mantine](https://mantine.dev). Dependencias añadidas:

- `@mantine/core`
- `@mantine/hooks`
- `@mantine/notifications`
- `@mantine/form`
- `@tabler/icons-react`

El tema original definido en `styles/theme` se mapea parcialmente a un `MantineProvider` en `providers/ThemeProvider.tsx` con una paleta `brand` derivada de `theme.colors.primary`.

### Componentes refactorizados

- `NavBar` -> usa `Group`, `Anchor`, `Box`.
- `MainInput` -> usa `Paper`, `TextInput`, `ActionIcon` (se eliminó `MainInput.styles.tsx`).
- `NoAgentNotification` -> usa `Notification`, `ActionIcon`, `Anchor`.
- `TranscriptionView` -> usa `ScrollArea.Autosize`, `Stack`, `Paper`.
- `VoiceTooltipContent` -> `Box` para layout.
- `CloseIcon` -> reemplazado por `IconX` de `@tabler/icons-react`.

### Notas de limpieza futura

- Revisar si todavía se necesitan clases utilitarias de Tailwind (actualmente conviven algunos estilos). Puede eliminarse Tailwind si no se usa en otras partes.
- Unificar paleta extendiendo `createTheme` con colores del objeto `gray` del theme original.
- Añadir Dark mode si se requiere usando `defaultColorScheme` y `colorSchemeManager` de Mantine.


![App screenshot](/.github/assets/frontend-screenshot.jpeg)

## Getting started

> [!TIP]
> If you'd like to try this application without modification, you can deploy an instance in just a few clicks with [LiveKit Cloud Sandbox](https://cloud.livekit.io/projects/p_/sandbox/templates/voice-assistant-frontend).

Run the following command to automatically clone this template.

```bash
lk app create --template voice-assistant-frontend
```

Then run the app with:

```bash
pnpm install
pnpm dev
```

And open http://localhost:3000 in your browser.

You'll also need an agent to speak with. Try our [Voice AI Quickstart](https://docs.livekit.io/start/voice-ai) for the easiest way to get started.

> [!NOTE]
> If you need to modify the LiveKit project credentials used, you can edit `.env.local` (copy from `.env.example` if you don't have one) to suit your needs.

## Contributing

This template is open source and we welcome contributions! Please open a PR or issue through GitHub, and don't forget to join us in the [LiveKit Community Slack](https://livekit.io/join-slack)!

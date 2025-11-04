"use client";

import React from "react";
import Image from "next/image";
import { useTranslation } from "react-i18next";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Group, Anchor, rem, Box, useMantineTheme } from "@mantine/core";

/**
 * Barra de navegación usando Mantine.
 * - Muestra enlaces definidos en array `links`.
 * - Resalta el enlace activo comparando con `pathname`.
 */

export const NavBar: React.FC = () => {
	const pathname = usePathname();
	const theme = useMantineTheme();
	const { t, i18n } = useTranslation();

	const links: { href: string; label: string }[] = [
		{ href: "/", label: t("nav.home") },
		{ href: "/ingest", label: t("page.upload.navLabel") },
		{ href: "/processed-documents", label: t("page.processedDocuments.navLabel") },
	];

	const handleChangeLanguage = (lng: string) => {
		i18n.changeLanguage(lng);
		if (typeof document !== "undefined") {
			document.documentElement.dataset.appLocale = lng;
		}
	};

	return (
			<Box component="nav" style={{
				width: "100%",
				borderBottom: `${rem(1)} solid ${theme.colors.gray[3]}`,
				backdropFilter: "blur(6px)",
				background: "rgba(255,255,255,0.65)",
				WebkitBackdropFilter: "blur(6px)",
			}}>
			<Group
				justify="flex-start"
				gap="md"
				style={{
					maxWidth: 1200,
					margin: "0 auto",
					padding: `${rem(12)} ${rem(16)}`,
				}}
			>
						<Box style={{
							fontSize: rem(18),
							fontWeight: 600,
							letterSpacing: "-0.25px",
							color: theme.black,
						}}>
					Open Overheid
				</Box>
				<Group gap={4} component="ul" style={{ listStyle: "none", margin: 0 }}>
					{links.map((l) => {
						const active = pathname === l.href;
						return (
							<Box key={l.href} component="li">
								<Anchor
									component={Link}
									href={l.href}
									aria-current={active ? "page" : undefined}
									underline="never"
									fw={500}
									px="sm"
									py={6}
									style={{
										display: "block",
										borderRadius: rem(6),
										background: active ? theme.colors.gray[2] : "transparent",
										color: active ? theme.black : theme.colors.gray[7],
										transition: "background 120ms, color 120ms",
									}}
									onMouseEnter={(e) => {
										if (!active) (e.currentTarget.style.background = "rgba(0,0,0,0.05)");
									}}
									onMouseLeave={(e) => {
										if (!active) (e.currentTarget.style.background = "transparent");
									}}
								>
									{l.label}
								</Anchor>
							</Box>
						);
					})}
				</Group>
				<Group gap={8} ml="auto">
					<button
						onClick={() => handleChangeLanguage("en")}
						style={{
							background: "none",
							border: "none",
							padding: 0,
							cursor: "pointer",
							outline: i18n.language === "en" ? `2px solid ${theme.colors.blue[6]}` : "none",
							borderRadius: rem(4),
						}}
						aria-label="Switch to English"
					>
						<img src="/assets/uk-flag.svg" alt="English" width={28} height={18} style={{ display: "block" }} />
					</button>
					<button
						onClick={() => handleChangeLanguage("nl")}
						style={{
							background: "none",
							border: "none",
							padding: 0,
							cursor: "pointer",
							outline: i18n.language === "nl" ? `2px solid ${theme.colors.blue[6]}` : "none",
							borderRadius: rem(4),
						}}
						aria-label="Switch to Dutch"
					>
						<img src="/assets/nl-flag.svg" alt="Nederlands" width={28} height={18} style={{ display: "block" }} />
					</button>
				</Group>
			</Group>
		</Box>
	);
};

export default NavBar;


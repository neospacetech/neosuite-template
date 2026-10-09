/**
 * NeoExample client module for the neosuite-app shell.
 *
 * - `routes`: screens mounted under `/neoexample`.
 * - `widgets`: embeddable views, keyed by widget id.
 * - `context`: what NeoMind may know and do while a NeoExample screen is open.
 */
export * from "./api";
export { context } from "./context";
export type { ContextDescriptor, ContextSnapshot, ProductRoute, WidgetDescriptor } from "./module";
export { ItemsScreen, LifecycleScreen, routes } from "./routes";
export type * from "./types";
export { ItemStatusBadge, widgets, type ItemStatusBadgeProps } from "./widgets";

/** Product id and mount point used by the shell. */
export const product = { id: "neoexample", title: "NeoExample", basePath: "/neoexample" } as const;

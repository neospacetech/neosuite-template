import type { WidgetDescriptor } from "../module";
import { ItemStatusBadge, type ItemStatusBadgeProps } from "./ItemStatusBadge";

export { ItemStatusBadge, type ItemStatusBadgeProps };

/** Embeddable views other products and NeoMind can render, keyed by stable widget id. */
export const widgets = {
  "neoexample.item.status": {
    id: "neoexample.item.status",
    title: "Item status",
    objectType: "neoexample.Item",
    component: ItemStatusBadge,
  } satisfies WidgetDescriptor<ItemStatusBadgeProps>,
};

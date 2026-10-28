import type { CardPayload, MatchResponse } from "@/lib/api";
import { bucketLabel } from "@/lib/utils";

export interface ChatContext {
  offers: MatchResponse | null;
  /** Set when the drawer is opened on /offers/[sourceId]. */
  card: CardPayload | null;
}

export function suggestions(ctx: ChatContext): string[] {
  if (ctx.card) {
    return [
      `Why is this offer ${bucketLabel(ctx.card.bucket).toLowerCase()}?`,
      "Which course helps most?",
      "What am I missing?",
    ];
  }
  return ["Which offer fits me best?", "How many offers per bucket?", "Which course helps most?"];
}

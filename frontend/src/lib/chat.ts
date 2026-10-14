import type { CardPayload, MatchResponse } from "@/lib/api";
import { bucketLabel } from "@/lib/utils";

/**
 * Placeholder for the conversational agent (no /api/chat yet).
 *
 * Every answer is read from the session cards returned by the API: no score,
 * gap or course is invented here. When the backend ships a chat endpoint,
 * replace `answer()` with a fetch and keep the drawer as is.
 */
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

type Intent = "why" | "course" | "gaps" | "best" | "buckets" | "summary";

function detectIntent(question: string): Intent {
  const q = question.toLowerCase();
  if (/(why|pourquoi)/.test(q)) return "why";
  if (/(course|cours|formation|training|improve|améliorer|ameliorer)/.test(q)) return "course";
  if (/(miss|gap|manque|écart|ecart)/.test(q)) return "gaps";
  if (/(best|meilleur|top|fit)/.test(q)) return "best";
  if (/(bucket|panier|how many|combien)/.test(q)) return "buckets";
  return "summary";
}

function mandatoryGaps(card: CardPayload): string[] {
  return card.gaps
    .filter((gap) => gap.requirement === "mandatory")
    .map((gap) => gap.skill_id ?? gap.kind);
}

function bestSimulation(cards: CardPayload[]) {
  let best: { card: CardPayload; sim: CardPayload["simulations"][number] } | null = null;
  for (const card of cards) {
    for (const sim of card.simulations) {
      if (!best || sim.delta > best.sim.delta) best = { card, sim };
    }
  }
  return best;
}

function describeCourse(card: CardPayload, sim: CardPayload["simulations"][number]): string {
  const bucketChange =
    sim.bucket_before !== sim.bucket_after
      ? ` and moves it from ${bucketLabel(sim.bucket_before)} to ${bucketLabel(sim.bucket_after)}`
      : "";
  return `"${sim.title}" (${sim.skill_id}) takes ${card.title} from ${sim.score_before.toFixed(
    1
  )} to ${sim.score_after.toFixed(1)} (+${sim.delta.toFixed(1)})${bucketChange}.`;
}

function answerForCard(card: CardPayload, intent: Intent): string {
  const missing = mandatoryGaps(card);
  switch (intent) {
    case "why":
    case "summary": {
      const head = `${card.title} scores ${card.score.toFixed(1)}/100 and is ${bucketLabel(
        card.bucket
      )}.`;
      if (missing.length === 0) {
        return `${head} You cover every mandatory skill.`;
      }
      return `${head} ${missing.length} mandatory skill${
        missing.length > 1 ? "s are" : " is"
      } missing: ${missing.join(", ")}.`;
    }
    case "gaps":
      if (card.gaps.length === 0) return "No gap on this offer.";
      return card.gaps.map((gap) => `• ${gap.detail}`).join("\n");
    case "course": {
      const best = bestSimulation([card]);
      if (!best) return "The catalogue has no course for the remaining gaps of this offer.";
      return describeCourse(best.card, best.sim);
    }
    default:
      return answerForCard(card, "summary");
  }
}

function answerForList(offers: MatchResponse, intent: Intent): string {
  const cards = offers.cards;
  if (cards.length === 0) return "No offer in this session.";
  const count = (bucket: string) => cards.filter((card) => card.bucket === bucket).length;

  switch (intent) {
    case "best": {
      const top = cards[0];
      return `Your best match is ${top.title}${top.company ? ` at ${top.company}` : ""}: ${top.score.toFixed(
        1
      )}/100, ${bucketLabel(top.bucket)}.`;
    }
    case "course": {
      const best = bestSimulation(cards);
      if (!best) return "No course simulation is available on these offers.";
      return describeCourse(best.card, best.sim);
    }
    case "buckets":
    case "summary":
    default:
      return `${cards.length} offers: ${count("eligible")} Eligible, ${count(
        "reachable"
      )} Reachable, ${count("out_of_reach")} Out of Reach. Open an offer and ask "why" for details.`;
  }
}

export function answer(question: string, ctx: ChatContext): string {
  const intent = detectIntent(question);
  if (ctx.card) return answerForCard(ctx.card, intent);
  if (ctx.offers) return answerForList(ctx.offers, intent);
  return "Run a match first: I answer from your scored offers.";
}

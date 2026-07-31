/**
 * Phase 3 — Event Sequencer
 * Event ordering and causality tracking.
 */
import { TimelineEvent } from "../timeline/types";

export type CausalityChain = {
  id: string;
  rootEvent: TimelineEvent;
  caused: TimelineEvent[];
  depth: number;
};

export class EventSequencer {
  private events: TimelineEvent[] = [];
  private chains: CausalityChain[] = [];

  addEvents(events: TimelineEvent[]) {
    this.events.push(...events);
    this.events.sort((a, b) => a.timestamp - b.timestamp);
    this.buildChains();
  }

  private buildChains() {
    this.chains = [];
    const eventMap = new Map(this.events.map((e) => [e.id, e]));

    for (const event of this.events) {
      if (event.type === "PERTURBATION" || event.type === "REPAIR_TRIGGER") {
        // Find events caused by this one (within 5s, same zone)
        const caused = this.events.filter(
          (e) =>
            e.id !== event.id &&
            e.timestamp > event.timestamp &&
            e.timestamp < event.timestamp + 5000 &&
            e.fieldZone === event.fieldZone
        );

        if (caused.length > 0) {
          this.chains.push({
            id: `chain_${event.id}`,
            rootEvent: event,
            caused,
            depth: this.computeDepth(event, eventMap, 0),
          });
        }
      }
    }
  }

  private computeDepth(
    event: TimelineEvent,
    eventMap: Map<string, TimelineEvent>,
    depth: number
  ): number {
    if (depth > 10) return depth; // Prevent infinite recursion
    const caused = this.events.filter(
      (e) =>
        e.id !== event.id &&
        e.timestamp > event.timestamp &&
        e.timestamp < event.timestamp + 5000 &&
        e.fieldZone === event.fieldZone
    );
    if (caused.length === 0) return depth;
    return Math.max(
      ...caused.map((e) => this.computeDepth(e, eventMap, depth + 1))
    );
  }

  getChains(): CausalityChain[] {
    return this.chains;
  }

  getEventsByType(type: string): TimelineEvent[] {
    return this.events.filter((e) => e.type === type);
  }

  getEventsInWindow(start: number, end: number): TimelineEvent[] {
    return this.events.filter((e) => e.timestamp >= start && e.timestamp <= end);
  }
}

// Every number and quote on screen comes from videos/suki-data.json, built by
// videos/make_data.py from the real Jev run and read-only store.db queries.
// fix_run.placeholder stays true until the live "Fix top root cause" run lands.
import raw from "../../suki-data.json";

export const D = raw;

export const causeLabel = (key: string): string =>
  (D.cause_labels as Record<string, string>)[key] ?? key;

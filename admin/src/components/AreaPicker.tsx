import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { Boundary, BoundaryLevel } from "../types/api";

export const LEVELS: BoundaryLevel[] = ["COUNTRY", "STATE", "LGA", "WARD", "FACILITY"];
export const LEVEL_LABEL: Record<BoundaryLevel, string> = {
  COUNTRY: "Country",
  STATE: "State",
  LGA: "LGA",
  WARD: "Ward",
  FACILITY: "Facility",
};
export type AreaValue = Partial<Record<BoundaryLevel, string>>;

/** The deepest area chosen, or null when nothing is chosen. */
export function deepest(v: AreaValue): string | null {
  for (let i = LEVELS.length - 1; i >= 0; i--) {
    const id = v[LEVELS[i]];
    if (id) return id;
  }
  return null;
}

/** Query-string params for report filters, e.g. {state_id: ".."}. */
export function areaParams(v: AreaValue): Record<string, string> {
  const out: Record<string, string> = {};
  for (const l of LEVELS) if (v[l]) out[`${l.toLowerCase()}_id`] = v[l]!;
  return out;
}

/** Fills the picker from a user's saved area. */
export function areaFromUser(u: Record<string, unknown>): AreaValue {
  const v: AreaValue = {};
  for (const l of LEVELS) {
    const id = u[`${l.toLowerCase()}_id`];
    if (typeof id === "string") v[l] = id;
  }
  return v;
}

function Level({
  level,
  parentId,
  value,
  onPick,
  disabled,
}: {
  level: BoundaryLevel;
  parentId: string | undefined;
  value: string | undefined;
  onPick: (id: string) => void;
  disabled: boolean;
}) {
  const { data } = useQuery<Boundary[]>({
    queryKey: ["boundaries", level, parentId ?? "root"],
    queryFn: async () =>
      (await api.get("/boundaries", { params: { level, ...(parentId ? { parent_id: parentId } : {}), limit: 2000 } })).data,
    enabled: !disabled,
  });
  return (
    <select
      className="border rounded px-2 py-1.5 text-sm min-w-[8rem] disabled:bg-gray-100"
      disabled={disabled}
      value={value ?? ""}
      onChange={(e) => onPick(e.target.value)}
    >
      <option value="">{LEVEL_LABEL[level]}…</option>
      {data?.map((b) => (
        <option key={b.id} value={b.id}>
          {b.name}
        </option>
      ))}
    </select>
  );
}

/** Country > State > LGA > Ward > Facility. Picking a level clears the ones below it. */
export default function AreaPicker({
  value,
  onChange,
  upTo = "FACILITY",
}: {
  value: AreaValue;
  onChange: (next: AreaValue) => void;
  upTo?: BoundaryLevel;
}) {
  const shown = LEVELS.slice(0, LEVELS.indexOf(upTo) + 1);
  return (
    <div className="flex flex-wrap gap-2">
      {shown.map((level, i) => {
        const parent = i === 0 ? undefined : value[LEVELS[i - 1]];
        return (
          <Level
            key={level}
            level={level}
            parentId={parent}
            value={value[level]}
            disabled={i > 0 && !parent}
            onPick={(id) => {
              const next: AreaValue = {};
              for (let j = 0; j < i; j++) next[LEVELS[j]] = value[LEVELS[j]];
              if (id) next[level] = id;
              onChange(next);
            }}
          />
        );
      })}
    </div>
  );
}

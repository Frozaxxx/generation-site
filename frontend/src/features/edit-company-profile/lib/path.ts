/** Путь в формате проверок бэкенда: `team[0].bio`, `contacts.address.city`. */
export function parsePath(path: string): (string | number)[] {
  return path
    .replace(/\[(\d+)\]/g, ".$1")
    .split(".")
    .filter(Boolean)
    .map((part) => (/^\d+$/.test(part) ? Number(part) : part));
}

/** Неизменяемая запись значения по пути. */
export function setIn<T>(source: T, path: string, value: unknown): T {
  const keys = parsePath(path);
  const write = (node: unknown, index: number): unknown => {
    const key = keys[index];
    if (key === undefined) return value;
    const current = (node as Record<string | number, unknown> | undefined)?.[key];
    if (Array.isArray(node)) {
      const copy = [...node];
      copy[key as number] = write(current, index + 1);
      return copy;
    }
    return { ...(node as Record<string, unknown>), [key]: write(current, index + 1) };
  };
  return write(source, 0) as T;
}

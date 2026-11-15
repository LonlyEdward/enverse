type ClassValue = string | false | null | undefined

/** Join class names, dropping falsy values. Keeps conditional classes tidy
 *  without pulling in a dependency. */
export function cn(...values: ClassValue[]): string {
  return values.filter(Boolean).join(' ')
}

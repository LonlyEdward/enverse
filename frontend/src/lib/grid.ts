/**
 * The shared poster grid. `auto-fill` with a growing minimum column width lets
 * posters fill the full-width layout and scale up on larger screens: two across
 * a phone, more as the viewport grows, each poster noticeably larger than a
 * fixed column count would allow.
 */
export const POSTER_GRID =
  'grid gap-x-4 gap-y-7 ' +
  'grid-cols-[repeat(auto-fill,minmax(145px,1fr))] ' +
  'sm:grid-cols-[repeat(auto-fill,minmax(165px,1fr))] ' +
  'lg:grid-cols-[repeat(auto-fill,minmax(200px,1fr))]'
